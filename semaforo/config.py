"""Carga de configuración desde config.toml (+ variables de entorno para secretos)."""
from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field, fields, is_dataclass
from pathlib import Path


@dataclass
class MT5Config:
    path: str = ""          # Ruta a terminal64.exe (vacío = la terminal que ya está abierta)
    login: int = 0          # 0 = usar la sesión ya iniciada en la terminal
    password: str = ""
    server: str = ""


@dataclass
class TelegramConfig:
    token: str = ""
    chat_id: str = ""


@dataclass
class GeneralConfig:
    source: str = "mt5"                 # mt5 | csv | demo
    csv_dir: str = "datos"
    symbols: list[str] = field(default_factory=lambda: ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY"])
    timeframe: str = "M15"
    history_bars: int = 20000
    utc_offset_hours: str | int = "auto"  # hora del servidor del bróker respecto a UTC
    default_utc_offset_hours: int = 2     # se usa si "auto" no se puede detectar
    scan_interval_sec: int = 30
    notify_colors: list[str] = field(default_factory=lambda: ["VERDE", "AMARILLO"])
    journal_file: str = "registro_senales.csv"


@dataclass
class StrategyConfig:
    sl_atr: float = 1.5            # stop loss = 1.5 x ATR
    rr: float = 1.5                # take profit = 1.5 x distancia del stop
    signal_lookback_bars: int = 1  # cuántas velas cerradas hacia atrás se considera "señal vigente"


@dataclass
class SemaforoConfig:
    ev_green: float = 0.20          # valor esperado mínimo (en R) para VERDE
    min_samples: int = 40           # situaciones históricas mínimas para confiar en el %
    score_tolerance: int = 10       # "situación similar" = confluencia +/- 10 puntos
    max_trade_bars: int = 96        # velas máximas que se deja correr la operación simulada
    min_gap_bars: int = 4           # separación mínima entre muestras históricas
    prior_strength: float = 30.0    # suavizado hacia el promedio del símbolo
    confidence_z: float = 1.645     # 1.645 = rango al 90 %
    max_spread_to_sl: float = 0.20  # ROJO si el spread se come más del 20 % del stop


@dataclass
class RiskConfig:
    risk_pct: float = 1.0           # % del balance arriesgado por operación (para el lote sugerido)


@dataclass
class Config:
    mt5: MT5Config = field(default_factory=MT5Config)
    telegram: TelegramConfig = field(default_factory=TelegramConfig)
    general: GeneralConfig = field(default_factory=GeneralConfig)
    strategy: StrategyConfig = field(default_factory=StrategyConfig)
    semaforo: SemaforoConfig = field(default_factory=SemaforoConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)


def _fill(obj, data: dict, section: str) -> None:
    known = {f.name: f for f in fields(obj)}
    for key, value in data.items():
        if key not in known:
            raise ValueError(f"Opción desconocida '{key}' en [{section}] de config.toml")
        current = getattr(obj, key)
        if is_dataclass(current):
            _fill(current, value, key)
        else:
            setattr(obj, key, value)


def load_config(path: str | Path = "config.toml") -> Config:
    cfg = Config()
    path = Path(path)
    if path.exists():
        with path.open("rb") as fh:
            _fill(cfg, tomllib.load(fh), "raíz")

    # Los secretos pueden venir del entorno para no dejarlos escritos en el archivo.
    cfg.telegram.token = os.environ.get("TELEGRAM_TOKEN", cfg.telegram.token)
    cfg.telegram.chat_id = str(os.environ.get("TELEGRAM_CHAT_ID", cfg.telegram.chat_id))
    cfg.mt5.password = os.environ.get("MT5_PASSWORD", cfg.mt5.password)
    cfg.general.notify_colors = [c.upper() for c in cfg.general.notify_colors]
    return cfg
