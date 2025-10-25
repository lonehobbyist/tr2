import pandas as pd
import os
from datetime import datetime

def load_data_from_csv(symbol, start_date, end_date):
    all_files = os.listdir('data')
    symbol_files = [f for f in all_files if f.startswith(symbol.replace(':', '_'))]

    df_list = []

    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

    for file in symbol_files:
        try:
            date_str = file.split('_')[-1].replace('.csv', '')
            file_date = datetime.strptime(date_str, '%Y-%m-%d').date()

            if start_date <= file_date <= end_date:
                df = pd.read_csv(f'data/{file}', index_col='datetime', parse_dates=True)
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
        return {'nifty_dates': [], 'options_dates': {}}
    all_files = os.listdir('data')
    nifty_dates = sorted(list(set([f.split('_')[-1].replace('.csv', '') for f in all_files if f.startswith('NIFTY50')])))

    options_files = [f for f in all_files if not f.startswith('NIFTY50')]
    options_dates = {}
    for file in options_files:
        symbol = file.split('_20')[0]
        date = file.split('_')[-1].replace('.csv', '')
        if symbol not in options_dates:
            options_dates[symbol] = []
        options_dates[symbol].append(date)

    for symbol in options_dates:
        options_dates[symbol] = sorted(list(set(options_dates[symbol])))

    return {'nifty_dates': nifty_dates, 'options_dates': options_dates}

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
                      yaxis_title='Price')

    return fig.to_html(full_html=False)
