import pandas as pd
import numpy as np
from backtester.strategy import detect_crosses, Trade
from backtester.engine import backtest


def test_detect_crosses():
    ema_fast = pd.Series([1,2,3,4])
    ema_slow = pd.Series([2,2,2,2])
    golden, death = detect_crosses(ema_fast, ema_slow)
    assert golden.tolist() == [False, False, True, False]
    assert death.tolist() == [False, False, False, False]


def make_price_df():
    times = pd.date_range('2024-01-01', periods=10, freq='5T')
    data = {
        'startTime': times,
        'openPrice': np.arange(10.0),
        'highPrice': np.arange(10.0)+0.5,
        'lowPrice': np.arange(10.0)-0.5,
        'closePrice': np.arange(10.0),
        'volume': 1,
        'turnover': 1,
        'symbol': 'TEST'
    }
    return pd.DataFrame(data)



def make_macd_df():
    times = pd.date_range('2024-01-01', periods=50, freq='1T')
    df = pd.DataFrame({'startTime': times, 'closePrice': np.linspace(0,49,50)})
    return df


def test_backtest_no_trades():
    df5 = make_price_df()
    df1 = make_macd_df()
    params = {
        'ema_fast': 2,
        'ema_slow': 4,
        'hv_len': 2,
        'hv_tp_div': 3,
        'hv_sl_div': 4.5,
        'macd_fast': 12,
        'macd_slow': 26,
        'macd_signal': 9,
    }
    trades = backtest(df5, df1, params)
    assert isinstance(trades, list)
