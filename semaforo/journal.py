"""Registro de TODAS las señales (no solo las ganadoras) y su resultado real.

Si solo se guardan las señales que salieron bien, el % de acierto se infla y
deja de servir. Aquí se guarda cada señal con su color, y `resolve()` revisa
después en el gráfico si tocó primero el TP o el SL.
"""
from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from .engine import COLOR_ORDER, Evaluation

COLUMNS = [
    "logged_utc", "bar_time", "symbol", "side", "entry", "sl", "tp", "color",
    "p_win", "ev_r", "samples", "score", "origin", "outcome", "outcome_r", "closed_time",
]
WIN, LOSS, OPEN = "GANADA", "PERDIDA", "ABIERTA"


def append(path: str | Path, ev: Evaluation) -> None:
    path = Path(path)
    new_file = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        if new_file:
            writer.writerow(COLUMNS)
        writer.writerow([
            datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            ev.bar_time.strftime("%Y-%m-%d %H:%M:%S"),
            ev.symbol, ev.side, ev.entry, ev.sl, ev.tp, ev.color,
            round(ev.estimate.p_win, 4), round(ev.estimate.ev_r, 4), ev.estimate.n, ev.score,
            ev.origin, "", "", "",
        ])


def load(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        return pd.DataFrame(columns=COLUMNS)
    # object: estas columnas mezclan vacío (señal abierta) con texto o números.
    pending_cols = {"outcome": object, "outcome_r": object, "closed_time": object}
    return pd.read_csv(path, dtype=pending_cols, keep_default_na=False)


def resolve_trade(bars: pd.DataFrame, bar_time: pd.Timestamp, side: str, sl: float, tp: float):
    """Recorre las velas posteriores a la señal. Devuelve (resultado, hora de cierre)."""
    after = bars[bars.index > bar_time]
    if after.empty:
        return OPEN, ""
    high, low = after["high"].to_numpy(float), after["low"].to_numpy(float)
    spread = after["spread"].to_numpy(float)
    if side == "COMPRA":
        hit_tp, hit_sl = high >= tp, low <= sl
    else:  # la venta se cierra al ask = bid + spread
        hit_tp, hit_sl = low + spread <= tp, high + spread >= sl
    first_tp = int(hit_tp.argmax()) if hit_tp.any() else len(after)
    first_sl = int(hit_sl.argmax()) if hit_sl.any() else len(after)
    if first_tp == first_sl == len(after):
        return OPEN, ""
    if first_tp < first_sl:
        return WIN, str(after.index[first_tp])
    return LOSS, str(after.index[first_sl])


def resolve(path: str | Path, source, timeframe: str, history_bars: int) -> pd.DataFrame:
    df = load(path)
    pending = df["outcome"].isin(["", OPEN])
    for symbol in df.loc[pending, "symbol"].unique():
        bars = source.bars(symbol, timeframe, history_bars)
        for i in df.index[pending & (df["symbol"] == symbol)]:
            row = df.loc[i]
            bar_time = pd.Timestamp(row["bar_time"])
            if bar_time < bars.index[0]:
                continue  # más vieja que el historial disponible: no se puede comprobar
            outcome, closed = resolve_trade(bars, bar_time, row["side"], row["sl"], row["tp"])
            risk = abs(row["entry"] - row["sl"])
            r = {WIN: abs(row["tp"] - row["entry"]) / risk, LOSS: -1.0}.get(outcome, "")
            df.loc[i, ["outcome", "outcome_r", "closed_time"]] = [outcome, r, closed]
    df.to_csv(path, index=False)
    return df


def summary(df: pd.DataFrame) -> list[dict]:
    """Acierto real por color: así se comprueba si el semáforo funciona."""
    closed = df[df["outcome"].isin([WIN, LOSS])]
    rows = []
    for color in sorted(df["color"].unique(), key=lambda c: COLOR_ORDER.get(c, 9)):
        part = closed[closed["color"] == color]
        r = pd.to_numeric(part["outcome_r"], errors="coerce")
        rows.append(dict(
            color=color,
            total=int((df["color"] == color).sum()),
            closed=len(part),
            win_rate=float((part["outcome"] == WIN).mean()) if len(part) else np.nan,
            avg_r=float(r.mean()) if len(part) else np.nan,
            predicted=float(pd.to_numeric(part["p_win"]).mean()) if len(part) else np.nan,
        ))
    return rows
