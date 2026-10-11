"""Textos para Telegram (HTML) y para la consola."""
from __future__ import annotations

import html
import math
import re

from .backtest import SymbolStats
from .engine import Evaluation

EMOJI = {"VERDE": "🟢", "AMARILLO": "🟡", "ROJO": "🔴"}
VERDICT = {
    "VERDE": "Vale la pena",
    "AMARILLO": "Dudosa: entra solo si tu análisis la confirma",
    "ROJO": "No entres",
}
DEMO_NOTE = "⚠️ <i>DATOS SIMULADOS (modo demo): no operes con esto.</i>"


def _price(value: float, digits: int) -> str:
    return f"{value:.{digits}f}"


def _pct(value: float) -> str:
    return "—" if value is None or math.isnan(value) else f"{value:.0%}"


def evaluation(ev: Evaluation) -> str:
    e = ev.estimate
    sym = html.escape(ev.symbol)
    lines = [
        f"{EMOJI[ev.color]} <b>{ev.color} · {sym} {ev.side}</b>",
        f"<b>{VERDICT[ev.color]}</b>",
        "",
        f"🎯 Probabilidad de ganar: <b>{_pct(e.p_win)}</b> (rango {_pct(e.p_low)}–{_pct(e.p_high)})",
        f"💰 Valor esperado: <b>{e.ev_r:+.2f}R</b> por operación",
        f"⚖️ Necesitas acertar {_pct(e.breakeven)} para no perder con R:R 1:{ev.rr:.1f}",
        "",
        f"Entrada {_price(ev.entry, ev.digits)} · SL {_price(ev.sl, ev.digits)} · TP {_price(ev.tp, ev.digits)}",
    ]
    if ev.lots is not None:
        lines.append(f"Lote sugerido: <b>{ev.lots:.2f}</b>")
    lines += ["", f"Confluencia {ev.score:.0f}/100 · basado en {e.n} situaciones parecidas"]
    lines += [f"{'✅' if ok else '❌'} {html.escape(text)}" for ok, text in ev.checks]
    lines += [f"⛔ {html.escape(text)}" for text in ev.blockers]
    lines += [f"⚠️ {html.escape(text)}" for text in ev.warnings]
    if ev.demo:
        lines += ["", DEMO_NOTE]
    return "\n".join(lines)


def evaluation_line(ev: Evaluation) -> str:
    e = ev.estimate
    return (
        f"{EMOJI[ev.color]} <b>{html.escape(ev.symbol)} {ev.side}</b> · {_pct(e.p_win)} · {e.ev_r:+.2f}R\n"
        f"    E {_price(ev.entry, ev.digits)} · SL {_price(ev.sl, ev.digits)} · TP {_price(ev.tp, ev.digits)}"
    )


def _errors(errors: dict[str, str]) -> list[str]:
    return [f"⚠️ {html.escape(sym)}: {html.escape(msg)}" for sym, msg in errors.items()]


def signal_list(evals: list[Evaluation], idle: list[str], errors: dict[str, str], demo: bool) -> str:
    good = [e for e in evals if e.color != "ROJO"]
    bad = [e for e in evals if e.color == "ROJO"]
    lines = ["<b>📡 Señales de la estrategia (última vela cerrada)</b>", ""]
    if good:
        lines += [evaluation_line(e) for e in good]
    else:
        lines.append("Ninguna señal que valga la pena ahora mismo.")
    if bad:
        lines += ["", "Descartadas: " + ", ".join(f"🔴 {html.escape(e.symbol)} {e.side}" for e in bad)]
    if idle:
        lines += ["", "Sin setup: " + ", ".join(html.escape(s) for s in idle)]
    lines += _errors(errors)
    if demo:
        lines += ["", DEMO_NOTE]
    return "\n".join(lines)


def panorama(evals: list[Evaluation], errors: dict[str, str], demo: bool) -> str:
    lines = ["<b>🗺️ Panorama: si entraras AHORA</b>", "<i>Mejor dirección de cada par con SL/TP por defecto</i>", ""]
    lines += [evaluation_line(e) for e in evals]
    lines += _errors(errors)
    lines += ["", "Detalle de uno: /evaluar SIMBOLO compra|venta"]
    if demo:
        lines += ["", DEMO_NOTE]
    return "\n".join(lines)


def ranking(stats: list[SymbolStats], errors: dict[str, str], demo: bool) -> str:
    lines = ["<b>🏆 Ranking de pares para tu estrategia</b>", "<i>Probada en tu historial con tus spreads reales</i>", ""]
    for pos, s in enumerate(stats, 1):
        pf = "∞" if math.isinf(s.profit_factor) else f"{s.profit_factor:.2f}"
        lines.append(
            f"{pos}. {EMOJI[s.color]} <b>{html.escape(s.symbol)}</b> · {s.expectancy_r:+.2f}R/op · acierto {_pct(s.win_rate)}\n"
            f"    {s.trades} ops ({s.trades_per_week:.1f}/semana) · PF {pf} · caída máx −{s.max_drawdown_r:.1f}R\n"
            f"    spread = {_pct(s.cost_r)} del stop"
        )
    lines += _errors(errors)
    lines += [
        "",
        "🟢 ganancia comprobada (≥30 ops)  🟡 positiva pero sin confirmar  🔴 pierde",
        "Opera los primeros y evita pares muy correlacionados a la vez (p. ej. EURUSD y GBPUSD).",
    ]
    if demo:
        lines += ["", DEMO_NOTE]
    return "\n".join(lines)


def journal_summary(rows: list[dict]) -> str:
    if not rows:
        return "Todavía no hay señales registradas."
    lines = ["<b>📒 Resultados reales de las señales registradas</b>", ""]
    for r in rows:
        lines.append(
            f"{EMOJI.get(r['color'], '⚪')} {r['color']}: {r['closed']} cerradas de {r['total']} · "
            f"acierto real {_pct(r['win_rate'])} (estimado {_pct(r['predicted'])}) · "
            + ("—" if math.isnan(r["avg_r"]) else f"{r['avg_r']:+.2f}R promedio")
        )
    lines += ["", "Si el acierto real de las verdes queda muy por debajo del estimado, sube ev_green en config.toml."]
    return "\n".join(lines)


HELP = """<b>🚦 Semáforo de señales</b>

/senales — señales de la estrategia en todos tus pares
/panorama — qué par vale la pena si entraras ahora
/evaluar XAUUSD compra 2650 2640 2670 — evalúa tu señal (entrada SL TP)
/evaluar XAUUSD venta — igual, con precio actual y SL/TP por defecto
/ranking — qué par le conviene más a la estrategia
/resultados — acierto real de las señales registradas
/ayuda — este mensaje

🟢 Vale la pena: valor esperado positivo y comprobado
🟡 Dudosa: positiva pero con poca evidencia
🔴 No entres: pierde en promedio o hay un riesgo que la bloquea

El % sale del historial: es una estimación, no una garantía.
Revisa siempre el calendario económico (NFP, IPC, FOMC) antes de entrar."""


def to_plain(text: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", text))
