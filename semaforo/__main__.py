"""Uso: python -m semaforo <comando> [--config config.toml] [--fuente mt5|csv|demo]

Comandos:
  bot                                   bot de Telegram 24/7 (avisos + comandos desde el celular)
  senales                               señales de la estrategia en todos los pares
  panorama                              qué par vale la pena si entraras ahora
  evaluar XAUUSD compra [E SL TP]       semáforo de una señal concreta
  ranking                               qué par le conviene más a la estrategia
  resultados                            acierto real de las señales registradas
  demo                                  todo lo anterior con datos simulados (sin MT5 ni Telegram)
"""
from __future__ import annotations

import argparse
import logging
import sys

from .config import load_config
from .engine import Semaforo
from .messages import to_plain
from .telegram_bot import handle_command, run_bot


def main(argv: list[str] | None = None) -> int:
    # La consola de Windows no siempre muestra emojis; así no se cae al imprimirlos.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(prog="python -m semaforo", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("comando")
    parser.add_argument("args", nargs="*")
    parser.add_argument("--config", default="config.toml")
    parser.add_argument("--fuente", choices=["mt5", "csv", "demo"], help="ignora la fuente de config.toml")
    opts = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    cfg = load_config(opts.config)
    command = opts.comando.lower()
    if command == "demo":
        cfg.general.source = "demo"
        cfg.general.symbols = ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY"]
    elif opts.fuente:
        cfg.general.source = opts.fuente

    try:
        sem = Semaforo(cfg)
    except (RuntimeError, ValueError) as exc:
        print(f"Error: {exc}")
        return 1

    if command == "bot":
        run_bot(sem)
        return 0
    if command == "demo":
        for text in ("/panorama", "/evaluar XAUUSD compra", "/senales", "/ranking"):
            print(f"\n===== {text} =====\n")
            print(to_plain(handle_command(sem, text)))
        return 0
    print(to_plain(handle_command(sem, " ".join([f"/{command}", *opts.args]))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
