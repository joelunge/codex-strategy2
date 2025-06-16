import mysql.connector
import pandas as pd
from datetime import datetime, timedelta


def get_connection(host="localhost", user="root", password="root", database="sct_2024"):
    return mysql.connector.connect(host=host, user=user, password=password, database=database)


def load_candles(conn, table, symbol, start, end):
    query = (
        f"SELECT symbol, startTime, openPrice, highPrice, lowPrice, closePrice, volume, turnover "
        f"FROM {table} WHERE symbol = %s AND startTime BETWEEN %s AND %s ORDER BY startTime"
    )
    df = pd.read_sql(query, conn, params=(symbol, start, end))
    df['startTime'] = pd.to_datetime(df['startTime'])
    return df


def load_candles_with_buffer(conn, table, symbol, start, end, ema_slow=200, hv_len=200):
    start_dt = datetime.strptime(start, "%Y-%m-%d %H:%M") - timedelta(minutes=max(ema_slow, hv_len)*5)
    return load_candles(conn, table, symbol, start_dt.strftime("%Y-%m-%d %H:%M"), end)
