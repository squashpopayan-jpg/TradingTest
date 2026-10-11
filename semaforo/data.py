"""Fuentes de precios: MetaTrader 5 (real), archivos CSV exportados de MT5, o datos de demostración."""
from __future__ import annotations

import time
import zlib
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from .config import MT5Config

TIMEFRAME_MINUTES = {"M1": 1, "M5": 5, "M15": 15, "M30": 30, "H1": 60, "H4": 240, "D1": 1440}


@dataclass
class Quote:
    bid: float
    ask: float


@dataclass
class SymbolMeta:
    digits: int
    tick_size: float | None = None
    tick_value: float | None = None
    volume_min: float | None = None
    volume_step: float | None = None
    volume_max: float | None = None


def guess_digits(price: float) -> int:
    if price >= 1000:
        return 2
    if price >= 50:
        return 3
    return 5


class MT5Source:
    """Lee velas y precios en vivo de la terminal MetaTrader 5 (solo Windows)."""

    label = "MT5"

    def __init__(self, cfg: MT5Config):
        try:
            import MetaTrader5 as mt5
        except ImportError as exc:
            raise RuntimeError(
                "Falta el paquete MetaTrader5. Instálalo con: pip install MetaTrader5 (solo funciona en Windows)."
            ) from exc
        self.mt5 = mt5
        kwargs: dict = {}
        if cfg.path:
            kwargs["path"] = cfg.path
        if cfg.login:
            kwargs.update(login=int(cfg.login), password=cfg.password, server=cfg.server)
        if not mt5.initialize(**kwargs):
            raise RuntimeError(f"No se pudo conectar con MetaTrader 5: {mt5.last_error()}")
        self._selected: set[str] = set()

    def _info(self, symbol: str):
        if symbol not in self._selected:
            if not self.mt5.symbol_select(symbol, True):
                raise RuntimeError(
                    f"El símbolo '{symbol}' no existe en tu bróker. Revisa el nombre exacto en "
                    "'Observación del mercado' (p. ej. XAUUSD, XAUUSDm, GOLD)."
                )
            self._selected.add(symbol)
        return self.mt5.symbol_info(symbol)

    def bars(self, symbol: str, timeframe: str, count: int) -> pd.DataFrame:
        info = self._info(symbol)
        tf = getattr(self.mt5, f"TIMEFRAME_{timeframe}")
        rates = self.mt5.copy_rates_from_pos(symbol, tf, 1, count)  # desde 1: solo velas cerradas
        if rates is None or len(rates) == 0:
            raise RuntimeError(f"MT5 no devolvió velas de {symbol}: {self.mt5.last_error()}")
        df = pd.DataFrame(rates)
        df.index = pd.to_datetime(df["time"], unit="s")
        df["spread"] = df["spread"] * info.point
        return df[["open", "high", "low", "close", "spread"]]

    def quote(self, symbol: str) -> Quote:
        self._info(symbol)
        tick = self.mt5.symbol_info_tick(symbol)
        return Quote(bid=tick.bid, ask=tick.ask)

    def utc_offset_hours(self, symbol: str, default: int) -> int:
        """La hora del servidor viene en los ticks; la comparamos con la hora UTC real."""
        self._info(symbol)
        tick = self.mt5.symbol_info_tick(symbol)
        diff = tick.time - time.time()
        hours = round(diff / 3600)
        # Si el último tick es viejo (mercado cerrado) la resta no es fiable.
        return hours if abs(diff - hours * 3600) < 300 else default

    def meta(self, symbol: str) -> SymbolMeta:
        info = self._info(symbol)
        return SymbolMeta(
            digits=info.digits,
            tick_size=info.trade_tick_size,
            tick_value=info.trade_tick_value,
            volume_min=info.volume_min,
            volume_step=info.volume_step,
            volume_max=info.volume_max,
        )

    def balance(self) -> float | None:
        account = self.mt5.account_info()
        return account.balance if account else None


class CSVSource:
    """Archivos `SIMBOLO_TIMEFRAME.csv` exportados desde MT5 (Ver > Símbolos > Barras > Exportar).

    También acepta CSV propios con columnas time,open,high,low,close[,spread] (spread en precio).
    """

    label = "CSV"

    def __init__(self, folder: str | Path, timeframe: str):
        self.folder = Path(folder)
        self.timeframe = timeframe
        self._cache: dict[str, tuple[pd.DataFrame, int]] = {}

    def _load(self, symbol: str, timeframe: str) -> tuple[pd.DataFrame, int]:
        key = f"{symbol}_{timeframe}"
        if key in self._cache:
            return self._cache[key]
        path = self.folder / f"{key}.csv"
        if not path.exists():
            raise RuntimeError(f"No encuentro {path}. Exporta las velas desde MT5 con ese nombre.")
        raw = pd.read_csv(path, sep=None, engine="python", dtype=str)
        if "<DATE>" in raw.columns:
            raw.columns = [c.strip("<>").lower() for c in raw.columns]
            time_text = raw["date"].str.replace(".", "-", regex=False)
            if "time" in raw.columns:
                time_text = time_text + " " + raw["time"]
            index = pd.to_datetime(time_text, format="mixed")
            spread_in_points = True
        else:
            raw.columns = [c.lower() for c in raw.columns]
            index = pd.to_datetime(raw["time"], format="mixed")
            spread_in_points = False

        digits = int(raw["close"].str.partition(".")[2].str.len().max())
        df = raw[["open", "high", "low", "close"]].astype(float)
        df.index = pd.DatetimeIndex(index)
        spread = raw["spread"].astype(float).to_numpy() if "spread" in raw.columns else np.zeros(len(df))
        df["spread"] = spread * 10.0 ** -digits if spread_in_points else spread
        df = df.sort_index()
        self._cache[key] = (df, digits)
        return df, digits

    def bars(self, symbol: str, timeframe: str, count: int) -> pd.DataFrame:
        return self._load(symbol, timeframe)[0].tail(count)

    def quote(self, symbol: str) -> Quote:
        last = self._load(symbol, self.timeframe)[0].iloc[-1]
        return Quote(bid=last["close"], ask=last["close"] + last["spread"])

    def utc_offset_hours(self, symbol: str, default: int) -> int:
        return default

    def meta(self, symbol: str) -> SymbolMeta:
        return SymbolMeta(digits=self._load(symbol, self.timeframe)[1])

    def balance(self) -> float | None:
        return None


# Parámetros aproximados para generar precios de demostración: (precio, volatilidad por vela, spread)
_DEMO_PARAMS = {
    "XAUUSD": (2400.0, 0.0012, 0.25),
    "EURUSD": (1.1000, 0.0005, 0.00008),
    "GBPUSD": (1.2800, 0.0006, 0.00012),
    "USDJPY": (150.00, 0.0006, 0.012),
}


class DemoSource:
    """Precios SIMULADOS (paseo aleatorio con rachas de tendencia) para probar sin MT5."""

    label = "DEMO"
    utc_offset = 2
    end = pd.Timestamp("2026-01-07 14:00")  # miércoles, sesión Londres+NY (hora servidor UTC+2)

    def __init__(self, timeframe: str = "M15", seed: int = 7, size: int = 30000):
        self.timeframe = timeframe
        self.seed = seed
        self.size = size
        self._cache: dict[str, pd.DataFrame] = {}

    def _series(self, symbol: str) -> pd.DataFrame:
        if symbol in self._cache:
            return self._cache[symbol]
        count = self.size
        price, vol, spread = _DEMO_PARAMS.get(symbol, (100.0, 0.001, 0.02))
        rng = np.random.default_rng(zlib.crc32(f"{symbol}:{self.seed}".encode()))
        drift = np.repeat(rng.choice([-0.08, 0.0, 0.08], size=count // 300 + 1), 300)[:count] * vol
        log_ret = drift + rng.standard_normal(count) * vol
        close = price * np.exp(np.cumsum(log_ret))
        open_ = np.concatenate([[price], close[:-1]])
        wick = np.abs(rng.standard_normal((2, count))) * vol * 0.6 * close
        minutes = TIMEFRAME_MINUTES[self.timeframe]
        index = pd.date_range(end=self.end, periods=count * 2, freq=f"{minutes}min")
        index = index[index.weekday < 5][-count:]  # sin fines de semana, como en MT5
        df = pd.DataFrame(
            {
                "open": open_,
                "high": np.maximum(open_, close) + wick[0],
                "low": np.minimum(open_, close) - wick[1],
                "close": close,
                "spread": spread,
            },
            index=index,
        )
        self._cache[symbol] = df
        return df

    def bars(self, symbol: str, timeframe: str, count: int) -> pd.DataFrame:
        return self._series(symbol).tail(count)

    def quote(self, symbol: str) -> Quote:
        last = self._series(symbol).iloc[-1]
        return Quote(bid=last["close"], ask=last["close"] + last["spread"])

    def utc_offset_hours(self, symbol: str, default: int) -> int:
        return self.utc_offset

    def meta(self, symbol: str) -> SymbolMeta:
        return SymbolMeta(digits=guess_digits(_DEMO_PARAMS.get(symbol, (100.0,))[0]))

    def balance(self) -> float | None:
        return None


def make_source(cfg) -> MT5Source | CSVSource | DemoSource:
    kind = cfg.general.source.lower()
    if kind == "mt5":
        return MT5Source(cfg.mt5)
    if kind == "csv":
        return CSVSource(cfg.general.csv_dir, cfg.general.timeframe)
    if kind == "demo":
        return DemoSource(cfg.general.timeframe)
    raise ValueError(f"Fuente desconocida '{cfg.general.source}'. Usa mt5, csv o demo.")
