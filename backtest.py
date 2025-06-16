import argparse
import yaml
import pandas as pd
from backtester.db import get_connection, load_candles_with_buffer
from backtester.engine import backtest, trades_to_equity
from backtester.indicators import macd


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--symbol', required=True)
    p.add_argument('--from', dest='start', required=True)
    p.add_argument('--to', dest='end', required=True)
    p.add_argument('--macd_fast', type=int, default=12)
    p.add_argument('--macd_slow', type=int, default=26)
    p.add_argument('--macd_signal', type=int, default=9)
    p.add_argument('--tick_mul', type=float, default=2)
    p.add_argument('--ema_fast', type=int, default=50)
    p.add_argument('--ema_slow', type=int, default=200)
    p.add_argument('--hv_len', type=int, default=200)
    p.add_argument('--hv_tp_div', type=float, default=3)
    p.add_argument('--hv_sl_div', type=float, default=4.5)
    p.add_argument('--hyperparam_config')
    return p.parse_args()


def main():
    args = parse_args()
    params = vars(args).copy()
    cfg = params.pop('hyperparam_config')
    if cfg:
        with open(cfg) as f:
            extra = yaml.safe_load(f)
            params.update(extra)
    conn = get_connection()
    df5 = load_candles_with_buffer(conn, 'candles5', args.symbol, args.start, args.end, params['ema_slow'], params['hv_len'])
    df1 = load_candles_with_buffer(conn, 'candles1', args.symbol, args.start, args.end)
    trades = backtest(df5, df1, params)
    if trades:
        trades_df = pd.DataFrame([t.__dict__ for t in trades])
    else:
        trades_df = pd.DataFrame(columns=[f.name for f in trades[0].__dataclass_fields__]) if trades else pd.DataFrame()
    trades_df.to_csv('trades.csv', index=False)
    equity = trades_to_equity(trades, df5)
    equity.to_csv('equity.csv', index=False)
    summary = {
        'total_trades': len(trades_df),
        'win_rate': (trades_df['outcome'] > 0).mean() if len(trades_df) else 0,
        'total_return_pct': (equity['equity'].iloc[-1] / df5['closePrice'].iloc[0] * 100) if len(equity) else 0,
    }
    with open('summary.txt', 'w') as f:
        for k, v in summary.items():
            f.write(f"{k}: {v}\n")


if __name__ == '__main__':
    main()
