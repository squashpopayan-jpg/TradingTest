"""Semáforo de señales para MetaTrader 5 con avisos por Telegram.

Uso desde tu propio bot:

    from semaforo import Semaforo, messages
    sem = Semaforo.from_config("config.toml")
    ev = sem.evaluate("XAUUSD", "compra", entry, sl, tp)
    print(ev.color, ev.estimate.p_win)          # "VERDE", 0.58
    texto_telegram = messages.evaluation(ev)
"""
from . import messages
from .engine import AMARILLO, ROJO, VERDE, Evaluation, Semaforo

__all__ = ["Semaforo", "Evaluation", "messages", "VERDE", "AMARILLO", "ROJO"]
