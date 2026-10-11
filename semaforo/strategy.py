"""Estrategia de ejemplo para el escáner: retroceso a la EMA20 a favor de la tendencia.

Si tu bot ya genera sus propias señales, no necesitas esta estrategia: pásale
esas señales a `Semaforo.evaluate(...)` y obtendrás el mismo semáforo.
Para cambiar la lógica del escáner, modifica `signals()` manteniendo la firma.
"""
from __future__ import annotations

import pandas as pd


def signals(f: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Devuelve (compras, ventas) como series booleanas sobre las velas cerradas."""
    long = (
        (f["ema50"] > f["ema200"])
        & (f["low"].rolling(3).min() <= f["ema20"])   # tocó la EMA20 en las últimas 3 velas
        & (f["close"] > f["ema20"])
        & (f["close"] > f["open"])                     # vela de confirmación alcista
        & f["rsi"].between(45, 70)
        & f["warm"]
    )
    short = (
        (f["ema50"] < f["ema200"])
        & (f["high"].rolling(3).max() >= f["ema20"])
        & (f["close"] < f["ema20"])
        & (f["close"] < f["open"])
        & f["rsi"].between(30, 55)
        & f["warm"]
    )
    return long, short
