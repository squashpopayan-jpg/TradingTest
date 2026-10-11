"""Probabilidad de ganar basada en lo que pasó en situaciones parecidas del historial.

Para una señal (dirección, SL y TP medidos en ATR, spread actual) se buscan en el
historial del mismo símbolo todas las velas con una confluencia parecida, se
simula la misma operación desde cada una y se cuenta cuántas tocaron el TP antes
que el SL. Si ambos se tocan en la misma vela se cuenta como pérdida.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view

from .config import SemaforoConfig


@dataclass
class Outcomes:
    starts: np.ndarray   # posición de la vela de entrada
    r: np.ndarray        # resultado en múltiplos de R (riesgo)
    win: np.ndarray      # True si tocó el TP primero
    held: np.ndarray     # velas que duró la operación


@dataclass
class Estimate:
    n: int               # situaciones parecidas que no se solapan en el tiempo
    wins: int
    p_win: float         # probabilidad suavizada
    p_low: float         # rango probable (intervalo de Wilson)
    p_high: float
    ev_r: float          # valor esperado por operación, en R
    breakeven: float     # % de acierto necesario para no perder con este R:R
    avg_bars: float      # duración media en velas


def forward_outcomes(
    f: pd.DataFrame,
    starts: np.ndarray,
    direction: int,
    sl_atr: float,
    tp_atr: float,
    max_bars: int,
    spread: np.ndarray | float,
) -> Outcomes:
    """Simula entrar al cierre de cada vela de `starts` (spread en unidades de precio)."""
    high = f["high"].to_numpy(float)
    low = f["low"].to_numpy(float)
    close = f["close"].to_numpy(float)
    atr = f["atr"].to_numpy(float)
    n = len(close)

    starts = np.asarray(starts, dtype=int)
    spread = np.broadcast_to(np.asarray(spread, dtype=float), starts.shape)
    keep = starts + max_bars < n
    starts, spread = starts[keep], spread[keep]
    if len(starts) == 0:
        empty = np.array([])
        return Outcomes(starts, empty, empty.astype(bool), empty)

    fut_high = sliding_window_view(high, max_bars)[starts + 1]
    fut_low = sliding_window_view(low, max_bars)[starts + 1]
    entry = close[starts]
    sl_d = sl_atr * atr[starts]
    tp_d = tp_atr * atr[starts]

    # Las velas son precio bid: la compra entra al ask y la venta sale al ask,
    # así que en ambos casos el TP queda `spread` más lejos y el SL `spread` más cerca.
    if direction == 1:
        hit_tp = fut_high >= (entry + spread + tp_d)[:, None]
        hit_sl = fut_low <= (entry + spread - sl_d)[:, None]
    else:
        hit_tp = fut_low <= (entry - spread - tp_d)[:, None]
        hit_sl = fut_high >= (entry - spread + sl_d)[:, None]

    first_tp = np.where(hit_tp.any(axis=1), hit_tp.argmax(axis=1), max_bars)
    first_sl = np.where(hit_sl.any(axis=1), hit_sl.argmax(axis=1), max_bars)
    win = first_tp < first_sl
    loss = (first_sl <= first_tp) & (first_sl < max_bars)

    # Si no tocó ni SL ni TP se cierra a mercado al final de la ventana.
    timeout_pnl = direction * (close[starts + max_bars] - entry) - spread
    r = np.where(win, tp_d / sl_d, np.where(loss, -1.0, timeout_pnl / sl_d))
    held = np.minimum(np.minimum(first_tp, first_sl) + 1, max_bars)
    return Outcomes(starts, r, win, held)


def decluster(idx: np.ndarray, min_gap: int) -> np.ndarray:
    """Evita contar muchas veces la misma situación (velas consecutivas casi idénticas)."""
    kept: list[int] = []
    last = -min_gap
    for i in idx:
        if i - last >= min_gap:
            kept.append(i)
            last = i
    return np.array(kept, dtype=int)


def wilson(wins: float, n: int, z: float) -> tuple[float, float]:
    if n == 0:
        return 0.0, 1.0
    p = wins / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def estimate(
    f: pd.DataFrame,
    direction: int,
    score: float,
    sl_atr: float,
    tp_atr: float,
    spread_atr: float,
    cfg: SemaforoConfig,
) -> Estimate:
    """`spread_atr` es el spread actual dividido por el ATR actual."""
    score_col = f["score_long" if direction == 1 else "score_short"].to_numpy(float)
    valid = f["warm"].to_numpy(bool)
    atr = f["atr"].to_numpy(float)

    all_idx = decluster(np.flatnonzero(valid), cfg.min_gap_bars)
    similar_idx = decluster(np.flatnonzero(valid & (np.abs(score_col - score) <= cfg.score_tolerance)), cfg.min_gap_bars)

    def run(idx: np.ndarray) -> Outcomes:
        return forward_outcomes(f, idx, direction, sl_atr, tp_atr, cfg.max_trade_bars, spread_atr * atr[idx])

    base = run(all_idx)
    sim = run(similar_idx)
    if len(base.r) == 0:
        raise ValueError("No hay suficiente historial para estimar la probabilidad (aumenta history_bars).")

    # Operaciones simuladas que se pisan en el tiempo cuentan casi como una sola:
    # la evidencia real es el número de muestras que no se solapan.
    if len(sim.r):
        hold = max(1, round(float(sim.held.mean())))
        n = len(decluster(sim.starts, hold))
        hit_rate, mean_r = float(sim.win.mean()), float(sim.r.mean())
    else:
        n, hit_rate, mean_r = 0, 0.0, 0.0
    wins = hit_rate * n

    # Suavizado bayesiano: con poca evidencia el resultado se acerca al promedio del símbolo.
    k = cfg.prior_strength
    p_win = (wins + k * base.win.mean()) / (n + k)
    ev_r = (mean_r * n + k * base.r.mean()) / (n + k)
    p_low, p_high = wilson(wins, n, cfg.confidence_z)
    rr = tp_atr / sl_atr
    return Estimate(
        n=n,
        wins=round(wins),
        p_win=float(p_win),
        p_low=p_low,
        p_high=p_high,
        ev_r=float(ev_r),
        breakeven=1 / (1 + rr),
        avg_bars=float(sim.held.mean()) if len(sim.r) else float(base.held.mean()),
    )
