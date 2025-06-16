import pandas as pd
import numpy as np


def ema(series, period):
    return series.ewm(span=period, adjust=False).mean()


def macd(series, fast=12, slow=26, signal=9):
    ema_fast = ema(series, fast)
    ema_slow = ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = ema(macd_line, signal)
    hist = macd_line - signal_line
    return pd.DataFrame({"macd": macd_line, "signal": signal_line, "hist": hist})


def historical_volatility(series, length=200):
    log_returns = np.log(series / series.shift(1))
    vol = log_returns.rolling(length).std() * np.sqrt(365*24*12)  # yearly volatility
    return vol
