import numpy as np
import pandas as pd
import pytest

from semaforo.probability import decluster, forward_outcomes, wilson


def frame(rows):
    """rows: lista de (high, low, close); ATR fijo en 1.0."""
    df = pd.DataFrame(rows, columns=["high", "low", "close"])
    df["atr"] = 1.0
    return df


def test_long_hits_tp_first():
    f = frame([(100, 100, 100), (100.5, 99.5, 100), (102.1, 100, 102), (102, 101, 101), (101, 100, 100)])
    out = forward_outcomes(f, np.array([0]), 1, sl_atr=1.0, tp_atr=2.0, max_bars=3, spread=0.0)
    assert out.win.tolist() == [True]
    assert out.r.tolist() == [2.0]
    assert out.held.tolist() == [2]


def test_long_hits_sl_first():
    f = frame([(100, 100, 100), (100.2, 98.9, 99), (103, 99, 102), (102, 101, 101), (101, 100, 100)])
    out = forward_outcomes(f, np.array([0]), 1, 1.0, 2.0, 3, 0.0)
    assert out.win.tolist() == [False]
    assert out.r.tolist() == [-1.0]


def test_same_bar_touching_both_counts_as_loss():
    f = frame([(100, 100, 100), (103, 98, 100), (100, 100, 100), (100, 100, 100)])
    out = forward_outcomes(f, np.array([0]), 1, 1.0, 2.0, 2, 0.0)
    assert out.r.tolist() == [-1.0]


def test_short_mirrors_long():
    f = frame([(100, 100, 100), (100.5, 97.9, 98), (99, 98, 98), (99, 98, 98)])
    out = forward_outcomes(f, np.array([0]), -1, 1.0, 2.0, 2, 0.0)
    assert out.win.tolist() == [True]


def test_spread_pushes_tp_away_and_sl_closer():
    # Sin spread toca el TP justo; con spread 0.2 el TP queda en 102.2 y no llega.
    f = frame([(100, 100, 100), (102.0, 100, 101), (101, 100.5, 101), (101, 100.5, 101)])
    assert forward_outcomes(f, np.array([0]), 1, 1.0, 2.0, 2, 0.0).win.tolist() == [True]
    out = forward_outcomes(f, np.array([0]), 1, 1.0, 2.0, 2, 0.2)
    assert out.win.tolist() == [False]
    # Termina sin tocar nada: cierra a mercado 101 - (100 + 0.2) = +0.8 R
    assert out.r[0] == pytest.approx(0.8)


def test_starts_without_full_future_are_dropped():
    f = frame([(100, 100, 100)] * 5)
    out = forward_outcomes(f, np.array([0, 1, 2, 3]), 1, 1.0, 1.0, 3, 0.0)
    assert out.starts.tolist() == [0, 1]


def test_decluster_keeps_spacing():
    assert decluster(np.array([0, 1, 2, 5, 6, 10]), 4).tolist() == [0, 5, 10]


def test_wilson_interval():
    low, high = wilson(50, 100, 1.96)
    assert low == pytest.approx(0.404, abs=0.001)
    assert high == pytest.approx(0.596, abs=0.001)
    assert wilson(0, 0, 1.96) == (0.0, 1.0)
