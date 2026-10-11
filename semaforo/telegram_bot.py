"""Bot de Telegram: avisa las señales nuevas y responde comandos desde el celular."""
from __future__ import annotations

import logging
import time

import requests

from . import backtest, journal, messages
from .engine import Semaforo, parse_direction

log = logging.getLogger("semaforo")
MAX_LEN = 4000  # Telegram corta en 4096 caracteres


class TelegramClient:
    def __init__(self, token: str):
        if not token:
            raise RuntimeError("Falta el token del bot: ponlo en config.toml o en la variable TELEGRAM_TOKEN.")
        self.base = f"https://api.telegram.org/bot{token}"

    def send(self, chat_id: str, text: str) -> None:
        for chunk in _chunks(text):
            resp = requests.post(
                f"{self.base}/sendMessage",
                json={"chat_id": chat_id, "text": chunk, "parse_mode": "HTML", "disable_web_page_preview": True},
                timeout=20,
            )
            if not resp.ok:
                log.error("Telegram rechazó el mensaje: %s", resp.text)

    def updates(self, offset: int | None, timeout: int) -> list[dict]:
        resp = requests.get(
            f"{self.base}/getUpdates",
            params={"offset": offset, "timeout": timeout, "allowed_updates": '["message"]'},
            timeout=timeout + 10,
        )
        resp.raise_for_status()
        return resp.json().get("result", [])


def _chunks(text: str) -> list[str]:
    chunks, current = [], ""
    for line in text.split("\n"):
        if len(current) + len(line) + 1 > MAX_LEN:
            chunks.append(current)
            current = ""
        current += line + "\n"
    return chunks + [current] if current.strip() else chunks


def _number(text: str) -> float:
    return float(text.replace(",", "."))


def handle_command(sem: Semaforo, text: str) -> str:
    """Convierte un comando de Telegram en la respuesta (texto HTML)."""
    parts = text.strip().split()
    if not parts:
        return messages.HELP
    command = parts[0].split("@")[0].lower()
    args = parts[1:]
    try:
        if command in ("/senales", "/señales"):
            return messages.signal_list(*sem.scan(), sem.is_demo)
        if command == "/panorama":
            return messages.panorama(*sem.panorama(), sem.is_demo)
        if command == "/ranking":
            return messages.ranking(*backtest.ranking(sem), sem.is_demo)
        if command == "/evaluar":
            if len(args) not in (2, 5):
                return "Uso: /evaluar XAUUSD compra 2650 2640 2670  (o solo /evaluar XAUUSD compra)"
            symbol, direction = args[0].upper(), parse_direction(args[1])
            levels = [_number(a) for a in args[2:]] or [None, None, None]
            ev = sem.evaluate(symbol, direction, *levels, origin="manual")
            if args[2:]:
                journal.append(sem.cfg.general.journal_file, ev)
            return messages.evaluation(ev)
        if command == "/resultados":
            g = sem.cfg.general
            df = journal.resolve(g.journal_file, sem.source, g.timeframe, g.history_bars)
            return messages.journal_summary(journal.summary(df))
    except (ValueError, RuntimeError) as exc:
        return f"⚠️ {exc}"
    return messages.HELP


def run_bot(sem: Semaforo) -> None:
    cfg = sem.cfg
    client = TelegramClient(cfg.telegram.token)
    owner = str(cfg.telegram.chat_id).strip()
    if owner:
        client.send(owner, "🚦 Semáforo encendido. Escribe /ayuda para ver los comandos.")
    else:
        log.warning("Sin chat_id: escribe cualquier cosa al bot y te responderá con tu chat_id.")

    notified: set[tuple] = set()
    offset: int | None = None
    next_scan = 0.0
    while True:
        try:
            if owner and time.time() >= next_scan:
                _auto_scan(sem, client, owner, notified)
                next_scan = time.time() + cfg.general.scan_interval_sec

            wait = int(max(1, min(25, next_scan - time.time())))
            for update in client.updates(offset, wait):
                offset = update["update_id"] + 1
                msg = update.get("message") or {}
                chat_id = str(msg.get("chat", {}).get("id", ""))
                text = msg.get("text", "")
                if not owner:
                    client.send(chat_id, f"Tu chat_id es <code>{chat_id}</code>. Ponlo en config.toml y reinicia.")
                elif chat_id == owner and text:
                    log.info("Comando: %s", text)
                    try:
                        reply = handle_command(sem, text)
                    except Exception as exc:
                        log.exception("Falló el comando %s", text)
                        reply = f"⚠️ Error procesando el comando: {exc}"
                    client.send(chat_id, reply)
                # Mensajes de otros chats se ignoran: el bot solo te responde a ti.
        except requests.RequestException as exc:
            log.warning("Sin conexión con Telegram (%s); reintento en 10 s", exc)
            time.sleep(10)
        except Exception:
            log.exception("Error inesperado; el bot sigue funcionando")
            time.sleep(10)


def _auto_scan(sem: Semaforo, client: TelegramClient, owner: str, notified: set[tuple]) -> None:
    evals, _, errors = sem.scan()
    for symbol, error in errors.items():
        log.warning("%s: %s", symbol, error)
    for ev in evals:
        if ev.key in notified:
            continue
        notified.add(ev.key)
        journal.append(sem.cfg.general.journal_file, ev)  # se registran todas, también las rojas
        if ev.color in sem.cfg.general.notify_colors:
            client.send(owner, messages.evaluation(ev))
