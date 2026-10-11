"""Ranking de pares: prueba la estrategia del escáner en el historial de cada símbolo
con los spreads reales de tu bróker y ordena por la expectativa que se puede creer."""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from . import strategy
from .engine import AMARILLO, ROJO, VERDE, Semaforo
from .probability import forward_outcomes

MIN_TRADES = 30
Z_ONE_SIDED_95 = 1.645


@dataclass
class SymbolStats:
    symbol: str
    trades: int
    win_rate: float
    expectancy_r: float      # ganancia media por operación, en R
    expectancy_low: float    # expectativa con 95 % de confianza (lo mínimo que se puede creer)
    profit_factor: float
    max_drawdown_r: float
    cost_r: float            # cuánto del stop se come el spread
    trades_per_week: float
    days: float
    color: str


def backtest_symbol(sem: Semaforo, symbol: str) -> SymbolStats:
    cfg = sem.cfg
    f = sem.features(symbol)
    long, short = strategy.signals(f)
    spread = f["spread"].to_numpy(float)
    sl_atr, rr = cfg.strategy.sl_atr, cfg.strategy.rr
    max_bars = cfg.semaforo.max_trade_bars

    candidates = []
    for direction, mask in ((1, long), (-1, short)):
        idx = np.flatnonzero(mask.to_numpy(bool))
        out = forward_outcomes(f, idx, direction, sl_atr, sl_atr * rr, max_bars, spread[idx])
        candidates += list(zip(out.starts, out.r, out.held))
    candidates.sort()

    # Una operación a la vez: se ignoran las señales mientras hay una abierta.
    results, busy_until = [], -1
    for start, r, held in candidates:
        if start > busy_until:
            results.append(r)
            busy_until = start + held

    atr = f["atr"].to_numpy(float)
    warm = f["warm"].to_numpy(bool)
    sl_dist = sl_atr * atr[warm]
    days = (f.index[-1] - f.index[0]).total_seconds() / 86400
    stats = _summarise(np.array(results))
    stats.update(
        cost_r=float(np.median(spread[warm] / sl_dist)) if warm.any() else math.nan,
        trades_per_week=stats["trades"] / max(days / 7, 1e-9),
        days=days,
    )
    return SymbolStats(symbol=symbol, **stats)


def _summarise(r: np.ndarray) -> dict:
    n = len(r)
    if n == 0:
        return dict(trades=0, win_rate=0.0, expectancy_r=0.0, expectancy_low=-math.inf,
                    profit_factor=0.0, max_drawdown_r=0.0, color=ROJO)
    mean = float(r.mean())
    low = mean - (Z_ONE_SIDED_95 * float(r.std(ddof=1)) / math.sqrt(n) if n > 1 else math.inf)
    gains, losses = r[r > 0].sum(), -r[r < 0].sum()
    equity = np.cumsum(r)
    drawdown = float((np.maximum.accumulate(np.concatenate([[0.0], equity]))[1:] - equity).max())
    if n >= MIN_TRADES and low > 0:
        color = VERDE
    elif mean > 0:
        color = AMARILLO
    else:
        color = ROJO
    return dict(
        trades=n,
        win_rate=float((r > 0).mean()),
        expectancy_r=mean,
        expectancy_low=low,
        profit_factor=float(gains / losses) if losses > 0 else math.inf,
        max_drawdown_r=drawdown,
        color=color,
    )


def ranking(sem: Semaforo) -> tuple[list[SymbolStats], dict[str, str]]:
    stats, errors = [], {}
    for symbol in sem.cfg.general.symbols:
        try:
            stats.append(backtest_symbol(sem, symbol))
        except Exception as exc:
            errors[symbol] = str(exc)
    stats.sort(key=lambda s: s.expectancy_low, reverse=True)
    return stats, errors
