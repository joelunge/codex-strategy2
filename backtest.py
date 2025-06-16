import argparse
import yaml
import pandas as pd
from backtester.db import get_connection, load_candles_with_buffer
from backtester.engine import backtest, trades_to_equity, debug_candle


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
    p.add_argument('--debug_ts')
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
    df5 = load_candles_with_buffer(
        conn,
        'candles5',
        args.symbol,
        args.start,
        args.end,
        ema_slow=params['ema_slow'],
        hv_len=params['hv_len'],
    )
    df1 = load_candles_with_buffer(
        conn,
        'candles1',
        args.symbol,
        args.start,
        args.end,
        ema_slow=26,  # enough for MACD
        hv_len=params['hv_len'],
    )
    if args.debug_ts:
        info = debug_candle(df5, df1, params, args.start, args.debug_ts)
        if not info:
            print(f"No data for {args.debug_ts}")
        else:
            print("=== DEBUG INFO ===")
            for key in [
                'symbol',
                'startTime',
                'ema_fast',
                'ema_slow',
                'golden_cross',
                'death_cross',
                'hv',
                'tp_pct',
                'sl_pct',
                'ticks_in_cross',
                'macd_val',
                'avg_macd',
                'pos_hist',
                'neg_hist',
                'trade_trigger',
                'reason',
            ]:
                print(f"{key}: {info[key]}")
            print("1m MACD bars:")
            for _, r in info['minute_block'].iterrows():
                print(f"{r['startTime']}, {r['hist']}")
        return

    trades = backtest(df5, df1, params, start_time=args.start)
    if trades:
        trades_df = pd.DataFrame([t.__dict__ for t in trades])
    else:
        trades_df = pd.DataFrame(columns=[f.name for f in trades[0].__dataclass_fields__]) if trades else pd.DataFrame()
    trades_df.to_csv('trades.csv', index=False)
    df5_visible = df5[df5['startTime'] >= pd.to_datetime(args.start)].reset_index(drop=True)
    equity = trades_to_equity(trades, df5_visible)
    equity.to_csv('equity.csv', index=False)
    summary = {
        'total_trades': len(trades_df),
        'win_rate': (trades_df['outcome'] > 0).mean() if len(trades_df) else 0,
        'total_return_pct': (equity['equity'].iloc[-1] / df5_visible['closePrice'].iloc[0] * 100) if len(equity) else 0,
    }
    with open('summary.txt', 'w') as f:
        for k, v in summary.items():
            f.write(f"{k}: {v}\n")


if __name__ == '__main__':
    main()
