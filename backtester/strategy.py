from dataclasses import dataclass
import pandas as pd
from .indicators import ema


@dataclass
class Trade:
    symbol: str
    side: str
    entry_time: pd.Timestamp
    entry_price: float
    exit_time: pd.Timestamp
    exit_price: float
    outcome: float
    tp_pct: float
    sl_pct: float
    hist_value: float
    avg_macd: float
    ticks_required: int
    cross_start: pd.Timestamp


def detect_crosses(ema_fast: pd.Series, ema_slow: pd.Series):
    prev = ema_fast.shift(1) - ema_slow.shift(1)
    curr = ema_fast - ema_slow
    golden = (prev <= 0) & (curr > 0)
    death = (prev >= 0) & (curr < 0)
    return golden, death
