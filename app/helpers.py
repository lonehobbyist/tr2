import pandas as pd
import os
from datetime import datetime

def load_data_from_csv(symbol, start_date, end_date, expiry=None, option_type=None, strike=None):
    path = f'data/{symbol}'
    if expiry:
        path += f'/Options/{expiry}'

    if not os.path.exists(path):
        return pd.DataFrame()

    all_files = []
    if expiry:
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith('.csv'):
                    all_files.append(os.path.join(root, file))
    else:
        for file in os.listdir(path):
            if file.endswith('.csv'):
                all_files.append(os.path.join(path, file))

    df_list = []
    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

    for file in all_files:
        try:
            date_str = file.split('_')[-1].replace('.csv', '')
            file_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            if start_date <= file_date <= end_date:
                df = pd.read_csv(file, index_col='datetime', parse_dates=True)
                df_list.append(df)
        except Exception as e:
            print(f"Error processing file {file}: {e}")

    if not df_list:
        return pd.DataFrame()

    return pd.concat(df_list).sort_index()

def calculate_vwap(df):
    df = df.copy()
    df['date'] = df.index.date
    df['cumulative_volume'] = df.groupby(df['date'])['volume'].cumsum()
    df['cumulative_volume_price'] = (df['volume'] * (df['high'] + df['low'] + df['close']) / 3).groupby(df['date']).cumsum()
    df['vwap'] = df['cumulative_volume_price'] / df['cumulative_volume']
    df.drop(columns=['date', 'cumulative_volume', 'cumulative_volume_price'], inplace=True)
    return df

def get_data_summary():
    if not os.path.exists('data'):
        return {'futures_dates': {}, 'options_dates': {}}

    futures_dates = {}
    options_dates = {}

    for symbol in os.listdir('data'):
        symbol_path = os.path.join('data', symbol)
        if os.path.isdir(symbol_path):
            futures_dates[symbol] = sorted([f.split('_')[-1].replace('.csv', '') for f in os.listdir(symbol_path) if f.endswith('.csv')])

            options_path = os.path.join(symbol_path, 'Options')
            if os.path.exists(options_path):
                options_dates[symbol] = {}
                for expiry in os.listdir(options_path):
                    expiry_path = os.path.join(options_path, expiry)
                    options_dates[symbol][expiry] = [f.split('_')[-1].replace('.csv', '') for f in os.listdir(expiry_path) if f.endswith('.csv')]

    return {'futures_dates': futures_dates, 'options_dates': options_dates}

import plotly.graph_objects as go

def create_candlestick_chart(df, signals, symbol):
    fig = go.Figure(data=[go.Candlestick(x=df.index,
                                           open=df['open'],
                                           high=df['high'],
                                           low=df['low'],
                                           close=df['close'])])

    for signal_time in signals:
        fig.add_annotation(x=signal_time, y=df.loc[signal_time]['low'] * 0.98,
                           text="^", showarrow=False, font=dict(size=20, color="green"))

    fig.update_layout(title=f'Candlestick Chart for {symbol}',
                      xaxis_title='Time',
                      yaxis_title='Price',
                      xaxis_rangebreaks=[
                          dict(bounds=["sat", "mon"]), # hide weekends
                          dict(bounds=[15.5, 9.25], pattern="hour"), # hide non-trading hours
                      ])

    return fig.to_html(full_html=False)

_symbols_cache = None
def get_futures_symbols():
    global _symbols_cache
    if _symbols_cache:
        return _symbols_cache

    try:
        url = "https://public.fyers.in/sym_details/NSE_FO.csv"
        df = pd.read_csv(url, header=None)
        _symbols_cache = sorted(list(df[12].unique()))
        return _symbols_cache
    except Exception as e:
        print(f"Error fetching futures symbols: {e}")
        return []
