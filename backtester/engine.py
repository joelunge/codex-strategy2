import pandas as pd
from .indicators import ema, macd, historical_volatility
from .strategy import detect_crosses, Trade


def backtest(df5, df1, params):
    ema_fast = ema(df5['closePrice'], params['ema_fast'])
    ema_slow = ema(df5['closePrice'], params['ema_slow'])
    hv = historical_volatility(df5['closePrice'], params['hv_len']) * 100
    df5 = df5.copy()
    df5['hv'] = hv
    golden, death = detect_crosses(ema_fast, ema_slow)

    macd_full = macd(df1['closePrice'], params['macd_fast'], params['macd_slow'], params['macd_signal'])
    df1 = df1.copy()
    df1[['macd', 'signal', 'hist']] = macd_full
    macd_sel = (
        df1.groupby(df1['startTime'].dt.floor('5min'))
        .apply(lambda x: x.loc[x['hist'].abs().idxmax()])
        .reset_index(drop=True)
        .sort_values('startTime')
    )
    macd_sel['avg'] = macd_sel['hist'].rolling(72).mean()
    macd_map = macd_sel.set_index('startTime')

    trades = []
    in_pos = False
    cooldown = 0
    ticks_in_cross = 0
    side = None
    entry_price = None
    entry_time = None
    cross_start = None
    tp_pct = sl_pct = 0

    for i, row in df5.iterrows():
        time = row['startTime']
        if cooldown > 0:
            cooldown -= 1
            continue
        if time not in macd_map.index:
            continue
        macd_val = macd_map.loc[time, 'hist']
        avg_macd = macd_map.loc[time, 'avg']
        hv_val = row['hv']
        if not in_pos:
            if golden.iloc[i]:
                side = 'long'
                ticks_in_cross = 0
                cross_start = time
            elif death.iloc[i]:
                side = 'short'
                ticks_in_cross = 0
                cross_start = time
            if side:
                if side == 'long' and ema_fast.iloc[i] > ema_slow.iloc[i] and macd_val <= avg_macd * 2:
                    ticks_in_cross += 1
                    if ticks_in_cross <= 5:
                        entry_price = row['closePrice']
                        entry_time = time
                        tp_pct = hv_val / params['hv_tp_div']
                        sl_pct = hv_val / params['hv_sl_div']
                        in_pos = True
                        ticks_required = ticks_in_cross
                elif side == 'short' and ema_fast.iloc[i] < ema_slow.iloc[i] and macd_val >= avg_macd * 2:
                    ticks_in_cross += 1
                    if ticks_in_cross <= 5:
                        entry_price = row['closePrice']
                        entry_time = time
                        tp_pct = hv_val / params['hv_tp_div']
                        sl_pct = hv_val / params['hv_sl_div']
                        in_pos = True
                        ticks_required = ticks_in_cross
        else:
            if side == 'long':
                tp_price = entry_price * (1 + tp_pct/100)
                sl_price = entry_price * (1 - sl_pct/100)
                if row['highPrice'] >= tp_price:
                    exit_price = tp_price
                    outcome = tp_pct / sl_pct
                elif row['lowPrice'] <= sl_price:
                    exit_price = sl_price
                    outcome = -1
                else:
                    continue
            else:
                tp_price = entry_price * (1 - tp_pct/100)
                sl_price = entry_price * (1 + sl_pct/100)
                if row['lowPrice'] <= tp_price:
                    exit_price = tp_price
                    outcome = tp_pct / sl_pct
                elif row['highPrice'] >= sl_price:
                    exit_price = sl_price
                    outcome = -1
                else:
                    continue
            trades.append(Trade(df5['symbol'].iloc[0], side, entry_time, entry_price, time, exit_price, outcome, tp_pct, sl_pct, macd_val, avg_macd, ticks_required, cross_start))
            in_pos = False
            ticks_in_cross = 0
            side = None
            cooldown = 10
    return trades


def trades_to_equity(trades, df5):
    equity = []
    pnl = 0.0
    trade_iter = iter(trades)
    current = next(trade_iter, None)
    for _, row in df5.iterrows():
        time = row['startTime']
        if current and time >= current.exit_time:
            pnl += current.exit_price - current.entry_price if current.side == 'long' else current.entry_price - current.exit_price
            current = next(trade_iter, None)
        equity.append({'startTime': time, 'equity': pnl})
    return pd.DataFrame(equity)
