"""Puntaje de confluencia (0-100) para compras y ventas en cada vela.

El puntaje no es la probabilidad: sirve para encontrar en el historial las
situaciones parecidas a la actual. La probabilidad sale de qué pasó en ellas.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import indicators as ind

WARMUP_BARS = 250  # velas necesarias para que EMA200 y el percentil de ATR sean fiables

# Puntos máximos de cada factor (suman 100).
WEIGHTS = {"trend": 20, "htf": 15, "adx": 15, "rsi": 15, "macd": 10, "vol": 10, "session": 15}


def compute_features(bars: pd.DataFrame, utc_offset_hours: int) -> pd.DataFrame:
    """`bars` con índice en hora del servidor y columnas open/high/low/close/spread (spread en precio)."""
    f = bars.copy()
    close = f["close"]
    f["ema20"] = ind.ema(close, 20)
    f["ema50"] = ind.ema(close, 50)
    f["ema200"] = ind.ema(close, 200)
    f["ema200_slope"] = f["ema200"] - f["ema200"].shift(20)
    f["atr"] = ind.atr(f, 14)
    f["rsi"] = ind.rsi(close, 14)
    f["adx"], f["plus_di"], f["minus_di"] = ind.adx(f, 14)
    f["macd_hist"] = ind.macd_hist(close)
    f["atr_pct"] = f["atr"].rolling(500, min_periods=100).rank(pct=True)

    utc_hour = (f.index - pd.Timedelta(hours=utc_offset_hours)).hour
    london = (utc_hour >= 7) & (utc_hour < 16)
    new_york = (utc_hour >= 12) & (utc_hour < 21)
    f["session"] = np.select(
        [london & new_york, london, new_york], ["Londres+NY", "Londres", "Nueva York"], "Asia/baja liquidez"
    )
    f["session_pts"] = np.select([london & new_york, london | new_york], [15, 10], 0)

    for direction, name in ((1, "score_long"), (-1, "score_short")):
        f[name] = sum(_components(f, direction).values())

    f["warm"] = (np.arange(len(f)) >= WARMUP_BARS) & f["atr_pct"].notna().to_numpy() & (f["atr"] > 0).to_numpy()
    return f


def _components(f: pd.DataFrame, direction: int) -> dict[str, pd.Series]:
    up = direction == 1
    trend = f["ema50"] > f["ema200"] if up else f["ema50"] < f["ema200"]
    htf = f["ema200_slope"] > 0 if up else f["ema200_slope"] < 0
    di_ok = f["plus_di"] > f["minus_di"] if up else f["minus_di"] > f["plus_di"]
    if up:
        rsi_full = f["rsi"].between(50, 68)
        rsi_half = (f["rsi"] >= 45) & (f["rsi"] < 50)
    else:
        rsi_full = f["rsi"].between(32, 50)
        rsi_half = (f["rsi"] > 50) & (f["rsi"] <= 55)
    macd_ok = f["macd_hist"] > 0 if up else f["macd_hist"] < 0
    return {
        "trend": trend * WEIGHTS["trend"],
        "htf": htf * WEIGHTS["htf"],
        "adx": ((f["adx"] >= 20) & di_ok) * WEIGHTS["adx"],
        "rsi": rsi_full * WEIGHTS["rsi"] + rsi_half * (WEIGHTS["rsi"] // 2),
        "macd": macd_ok * WEIGHTS["macd"],
        "vol": f["atr_pct"].between(0.25, 0.90) * WEIGHTS["vol"],
        "session": f["session_pts"],
    }


def explain(row: pd.Series, direction: int) -> list[tuple[bool, str]]:
    """Lista de (a favor?, texto) para mostrar en el mensaje."""
    up = direction == 1
    word = "alcista" if up else "bajista"
    checks: list[tuple[bool, str]] = []

    trend_ok = row["ema50"] > row["ema200"] if up else row["ema50"] < row["ema200"]
    checks.append((trend_ok, f"Tendencia {word} (EMA50 vs EMA200)" if trend_ok else "Contra la tendencia principal"))

    htf_ok = row["ema200_slope"] > 0 if up else row["ema200_slope"] < 0
    checks.append((htf_ok, "Tendencia de fondo a favor" if htf_ok else "Tendencia de fondo en contra"))

    di_ok = row["plus_di"] > row["minus_di"] if up else row["minus_di"] > row["plus_di"]
    if row["adx"] < 20:
        checks.append((False, f"ADX {row['adx']:.0f}: mercado sin fuerza / lateral"))
    elif di_ok:
        checks.append((True, f"ADX {row['adx']:.0f}: tendencia con fuerza a favor"))
    else:
        checks.append((False, f"ADX {row['adx']:.0f}: la fuerza va en contra"))

    r = row["rsi"]
    if (up and r > 68) or (not up and r < 32):
        checks.append((False, f"RSI {r:.0f}: {'sobrecomprado' if up else 'sobrevendido'}, entrada tardía"))
    elif (up and r >= 50) or (not up and r <= 50):
        checks.append((True, f"RSI {r:.0f}: impulso sano"))
    else:
        checks.append((False, f"RSI {r:.0f}: sin impulso a favor"))

    macd_ok = row["macd_hist"] > 0 if up else row["macd_hist"] < 0
    checks.append((macd_ok, "MACD a favor" if macd_ok else "MACD en contra"))

    pct = row["atr_pct"]
    if pct < 0.25:
        checks.append((False, "Volatilidad muy baja: el precio puede no llegar al TP"))
    elif pct > 0.90:
        checks.append((False, "Volatilidad extrema: riesgo de latigazos"))
    else:
        checks.append((True, "Volatilidad normal"))

    checks.append((row["session_pts"] > 0, f"Sesión: {row['session']}"))
    return checks
