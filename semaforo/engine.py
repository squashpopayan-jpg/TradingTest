"""El semáforo: evalúa señales y escanea todos los símbolos."""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import pandas as pd

from . import strategy
from .config import Config, load_config
from .data import Quote, SymbolMeta, guess_digits, make_source
from .features import compute_features, explain
from .probability import Estimate, estimate

VERDE, AMARILLO, ROJO = "VERDE", "AMARILLO", "ROJO"
COLOR_ORDER = {VERDE: 0, AMARILLO: 1, ROJO: 2}

BUY_WORDS = {"compra", "comprar", "buy", "long", "c", "1"}
SELL_WORDS = {"venta", "vender", "sell", "short", "v", "-1"}


def parse_direction(text: str | int) -> int:
    word = str(text).strip().lower()
    if word in BUY_WORDS:
        return 1
    if word in SELL_WORDS:
        return -1
    raise ValueError(f"Dirección '{text}' no reconocida: usa compra o venta.")


@dataclass
class Evaluation:
    symbol: str
    direction: int
    entry: float
    sl: float
    tp: float
    color: str
    estimate: Estimate
    score: float
    bar_time: pd.Timestamp
    origin: str                      # estrategia | manual | panorama
    digits: int
    checks: list[tuple[bool, str]] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    lots: float | None = None
    demo: bool = False

    @property
    def side(self) -> str:
        return "COMPRA" if self.direction == 1 else "VENTA"

    @property
    def rr(self) -> float:
        return abs(self.tp - self.entry) / abs(self.entry - self.sl)

    @property
    def key(self) -> tuple:
        return (self.symbol, self.direction, self.bar_time)


class Semaforo:
    def __init__(self, cfg: Config, source=None):
        self.cfg = cfg
        self.source = source if source is not None else make_source(cfg)
        self._features: dict[str, tuple[pd.Timestamp, pd.DataFrame]] = {}

    @classmethod
    def from_config(cls, path: str = "config.toml") -> "Semaforo":
        return cls(load_config(path))

    @property
    def is_demo(self) -> bool:
        return getattr(self.source, "label", "") == "DEMO"

    # ------------------------------------------------------------------ datos
    def utc_offset(self, symbol: str) -> int:
        g = self.cfg.general
        if str(g.utc_offset_hours).lower() == "auto":
            return self.source.utc_offset_hours(symbol, g.default_utc_offset_hours)
        return int(g.utc_offset_hours)

    def features(self, symbol: str) -> pd.DataFrame:
        g = self.cfg.general
        bars = self.source.bars(symbol, g.timeframe, g.history_bars)
        cached = self._features.get(symbol)
        if cached and cached[0] == bars.index[-1]:
            return cached[1]
        f = compute_features(bars, self.utc_offset(symbol))
        self._features[symbol] = (bars.index[-1], f)
        return f

    def _meta(self, symbol: str, price: float) -> SymbolMeta:
        try:
            return self.source.meta(symbol)
        except Exception:
            return SymbolMeta(digits=guess_digits(price))

    # -------------------------------------------------------------- evaluación
    def evaluate(
        self,
        symbol: str,
        direction: int | str,
        entry: float | None = None,
        sl: float | None = None,
        tp: float | None = None,
        origin: str = "manual",
    ) -> Evaluation:
        """Evalúa una señal. Sin entry/sl/tp usa el precio actual y el SL/TP por defecto (ATR)."""
        direction = parse_direction(direction)
        f = self.features(symbol)
        row = f.iloc[-1]
        if not row["warm"]:
            raise ValueError(f"{symbol}: historial insuficiente, sube history_bars en config.toml.")
        quote: Quote = self.source.quote(symbol)
        market = quote.ask if direction == 1 else quote.bid
        atr = float(row["atr"])

        if entry is None:
            entry = market
        if sl is None or tp is None:
            sl_dist = self.cfg.strategy.sl_atr * atr
            sl = entry - direction * sl_dist
            tp = entry + direction * sl_dist * self.cfg.strategy.rr

        if direction == 1 and not sl < entry < tp:
            raise ValueError("En una COMPRA el SL va debajo de la entrada y el TP encima.")
        if direction == -1 and not tp < entry < sl:
            raise ValueError("En una VENTA el SL va encima de la entrada y el TP debajo.")

        sl_dist, tp_dist = abs(entry - sl), abs(tp - entry)
        spread = max(quote.ask - quote.bid, 0.0)
        score = float(row["score_long" if direction == 1 else "score_short"])
        est = estimate(f, direction, score, sl_dist / atr, tp_dist / atr, spread / atr, self.cfg.semaforo)

        blockers, warnings = self._risks(row, f.index[-1], symbol, entry, market, sl_dist, spread, atr, est)
        meta = self._meta(symbol, entry)
        lots = self._lots(meta, sl_dist, warnings)
        return Evaluation(
            symbol=symbol,
            direction=direction,
            entry=float(entry),
            sl=float(sl),
            tp=float(tp),
            color=self._color(est, blockers),
            estimate=est,
            score=score,
            bar_time=f.index[-1],
            origin=origin,
            digits=meta.digits,
            checks=explain(row, direction),
            blockers=blockers,
            warnings=warnings,
            lots=lots,
            demo=self.is_demo,
        )

    def _color(self, est: Estimate, blockers: list[str]) -> str:
        c = self.cfg.semaforo
        if blockers or est.ev_r <= 0:
            return ROJO
        if est.n >= c.min_samples and est.ev_r >= c.ev_green and est.p_low >= est.breakeven:
            return VERDE
        return AMARILLO

    def _risks(self, row, bar_time, symbol, entry, market, sl_dist, spread, atr, est):
        c = self.cfg.semaforo
        blockers: list[str] = []
        warnings: list[str] = []
        if spread > c.max_spread_to_sl * sl_dist:
            blockers.append(f"El spread se come el {spread / sl_dist:.0%} del stop")
        utc = bar_time - pd.Timedelta(hours=self.utc_offset(symbol))
        if utc.weekday() >= 5 or (utc.weekday() == 4 and utc.hour >= 20):
            blockers.append("Cierre de semana: riesgo de gap el lunes")
        if est.n < c.min_samples:
            warnings.append(f"Solo {est.n} situaciones parecidas: el % es poco fiable")
        if sl_dist < 0.5 * atr:
            warnings.append("Stop muy ajustado: el ruido normal del mercado puede sacarte")
        if abs(entry - market) > 0.5 * atr:
            warnings.append("La entrada está lejos del precio actual; el % supone entrar ya")
        return blockers, warnings

    def _lots(self, meta: SymbolMeta, sl_dist: float, warnings: list[str]) -> float | None:
        balance = self.source.balance()
        if not (balance and meta.tick_size and meta.tick_value and meta.volume_step):
            return None
        risk_money = balance * self.cfg.risk.risk_pct / 100
        loss_per_lot = sl_dist / meta.tick_size * meta.tick_value
        lots = math.floor(risk_money / loss_per_lot / meta.volume_step) * meta.volume_step
        if meta.volume_min and lots < meta.volume_min:
            warnings.append(f"Con {self.cfg.risk.risk_pct}% de riesgo ni el lote mínimo cabe: no entres o reduce el stop")
            return None
        if meta.volume_max:
            lots = min(lots, meta.volume_max)
        return round(lots, 2)

    # ---------------------------------------------------------------- escaneo
    def strategy_signal(self, symbol: str) -> Evaluation | None:
        """Señal de la estrategia del escáner en las últimas velas cerradas (o None)."""
        f = self.features(symbol)
        long, short = strategy.signals(f)
        lookback = max(1, self.cfg.strategy.signal_lookback_bars)
        for direction, mask in ((1, long), (-1, short)):
            if mask.iloc[-lookback:].any():
                return self.evaluate(symbol, direction, origin="estrategia")
        return None

    def scan(self) -> tuple[list[Evaluation], list[str], dict[str, str]]:
        """Revisa todos los símbolos. Devuelve (señales, símbolos sin setup, errores)."""
        signals, idle, errors = [], [], {}
        for symbol in self.cfg.general.symbols:
            try:
                ev = self.strategy_signal(symbol)
            except Exception as exc:  # un símbolo con problemas no debe tumbar el escaneo
                errors[symbol] = str(exc)
                continue
            if ev is None:
                idle.append(symbol)
            else:
                signals.append(ev)
        return sort_evaluations(signals), idle, errors

    def panorama(self) -> tuple[list[Evaluation], dict[str, str]]:
        """Para cada símbolo: la mejor dirección si entraras ahora con el SL/TP por defecto."""
        out, errors = [], {}
        for symbol in self.cfg.general.symbols:
            try:
                both = [self.evaluate(symbol, d, origin="panorama") for d in (1, -1)]
            except Exception as exc:
                errors[symbol] = str(exc)
                continue
            out.append(max(both, key=lambda e: (-COLOR_ORDER[e.color], e.estimate.ev_r)))
        return sort_evaluations(out), errors


def sort_evaluations(evals: list[Evaluation]) -> list[Evaluation]:
    return sorted(evals, key=lambda e: (COLOR_ORDER[e.color], -e.estimate.ev_r))
