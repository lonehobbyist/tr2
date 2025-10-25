from flask import Blueprint, render_template, request, jsonify
from fyers_apiv3 import fyersModel
import pandas as pd
import talib
import os
import logging
from config import FYERS_CLIENT_ID, FYERS_SECRET_KEY, FYERS_REDIRECT_URI, TESTING
from .helpers import load_data_from_csv, calculate_vwap, get_data_summary, create_candlestick_chart

bp = Blueprint('main', __name__)

class MockFyers:
    def history(self, *args, **kwargs):
        return {
            's': 'ok',
            'candles': [
                [1672531200, 18000, 18050, 17950, 18020, 1000]
            ]
        }

# Initialize Fyers API client
if TESTING:
    fyers = MockFyers()
else:
    fyers = fyersModel.FyersModel(client_id=FYERS_CLIENT_ID, token=None, log_path=os.getcwd())

# In-memory storage for the access token (in a real application, use a more persistent storage)
access_token = None

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/login')
def login():
    try:
        session = fyersModel.SessionModel(client_id=FYERS_CLIENT_ID,
                                         secret_key=FYERS_SECRET_KEY,
                                         redirect_uri=FYERS_REDIRECT_URI,
                                         response_type="code")
        response = session.generate_authcode()
        logging.info("Generated auth code for Fyers login.")
        return f'<a href="{response}">Click here to login to Fyers and get the auth code.</a>'
    except Exception as e:
        logging.error(f"Error generating auth code: {e}")
        return "Error generating auth code. Please check the logs.", 500

@bp.route('/callback')
def callback():
    global access_token
    try:
        auth_code = request.args.get('auth_code')
        session = fyersModel.SessionModel(client_id=FYERS_CLIENT_ID,
                                         secret_key=FYERS_SECRET_KEY,
                                         redirect_uri=FYERS_REDIRECT_URI,
                                         response_type="code",
                                         grant_type="authorization_code")
        session.set_token(auth_code)
        response = session.generate_token()
        access_token = response['access_token']
        fyers.token = access_token
        logging.info("Successfully obtained access token.")
        return "Login successful! You can now use the application."
    except Exception as e:
        logging.error(f"Error obtaining access token: {e}")
        return "Error obtaining access token. Please check the logs.", 500

@bp.route('/download_nifty_data', methods=['POST'])
def download_nifty_data():
    if not TESTING and not access_token:
        return jsonify({'error': 'Not logged in'}), 401

    data = request.get_json()
    start_date = data['start_date']
    end_date = data['end_date']
    logging.info(f"Downloading NIFTY50 data from {start_date} to {end_date}")

    try:
        data = {
            "symbol": "NSE:NIFTY50-INDEX",
            "resolution": "5",
            "date_format": "1",
            "range_from": start_date,
            "range_to": end_date,
            "cont_flag": "1"
        }
        response = fyers.history(data=data)

        if response['s'] == 'ok':
            df = pd.DataFrame(response['candles'], columns=['epoch', 'open', 'high', 'low', 'close', 'volume'])
            df['datetime'] = pd.to_datetime(df['epoch'], unit='s')
            df.set_index('datetime', inplace=True)

            for day in pd.to_datetime(df.index).date:
                day_str = day.strftime('%Y-%m-%d')
                day_df = df[df.index.date == day]
                if not day_df.empty:
                    day_df.to_csv(f'data/NIFTY50_{day_str}.csv')

            logging.info('NIFTY50 data downloaded and saved successfully.')
            return jsonify({'message': 'NIFTY50 data downloaded successfully.'})
        else:
            logging.error(f"Error from Fyers API: {response['message']}")
            return jsonify({'error': response['message']}), 500
    except Exception as e:
        logging.error(f"Error downloading NIFTY50 data: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/download_options_data', methods=['POST'])
def download_options_data():
    if not TESTING and not access_token:
        return jsonify({'error': 'Not logged in'}), 401

    data = request.get_json()
    symbol = data['symbol']
    start_date = data['start_date']
    end_date = data['end_date']
    logging.info(f"Downloading options data for {symbol} from {start_date} to {end_date}")

    try:
        data = {
            "symbol": symbol,
            "resolution": "5",
            "date_format": "1",
            "range_from": start_date,
            "range_to": end_date,
            "cont_flag": "1"
        }
        response = fyers.history(data=data)

        if response['s'] == 'ok':
            df = pd.DataFrame(response['candles'], columns=['epoch', 'open', 'high', 'low', 'close', 'volume'])
            df['datetime'] = pd.to_datetime(df['epoch'], unit='s')
            df.set_index('datetime', inplace=True)

            for day in pd.to_datetime(df.index).date:
                day_str = day.strftime('%Y-%m-%d')
                day_df = df[df.index.date == day]
                if not day_df.empty:
                    day_df.to_csv(f'data/{symbol.replace(":", "_")}_{day_str}.csv')

            logging.info(f'Options data for {symbol} downloaded and saved successfully.')
            return jsonify({'message': f'Options data for {symbol} downloaded successfully.'})
        else:
            logging.error(f"Error from Fyers API for {symbol}: {response['message']}")
            return jsonify({'error': response['message']}), 500
    except Exception as e:
        logging.error(f"Error downloading options data for {symbol}: {e}")
        return jsonify({'error': str(e)}), 500

def run_analysis(start_date, end_date, strategy):
    data_summary = get_data_summary()
    nifty_df = load_data_from_csv("NIFTY50", start_date, end_date)

    if nifty_df.empty:
        return data_summary, None

    if strategy == 'ema_crossover':
        nifty_df['ema10'] = talib.EMA(nifty_df['close'], timeperiod=10)
        nifty_df['ema20'] = talib.EMA(nifty_df['close'], timeperiod=20)
        nifty_df['signal'] = (nifty_df['close'] > nifty_df['ema10']) & (nifty_df['close'] > nifty_df['ema20']) & \
                           (nifty_df['close'].shift(1) < nifty_df[['ema10', 'ema20']].shift(1).max(axis=1))
    elif strategy == 'vwap_crossover':
        nifty_df = calculate_vwap(nifty_df)
        nifty_df['signal'] = (nifty_df['close'] > nifty_df['vwap']) & (nifty_df['close'].shift(1) < nifty_df['vwap'].shift(1))

    signal_times = nifty_df[nifty_df['signal']].index

    charts = ""
    for symbol in data_summary['options_dates']:
        option_df = load_data_from_csv(symbol, start_date, end_date)
        if not option_df.empty:
            option_signals = []
            for signal_time in signal_times:
                if signal_time in option_df.index:
                    option_row = option_df.loc[signal_time]
                    if strategy == 'ema_crossover':
                        option_df['ema10'] = talib.EMA(option_df['close'], timeperiod=10)
                        option_df['ema20'] = talib.EMA(option_df['close'], timeperiod=20)
                        if option_row['close'] > option_row['ema10'] and option_row['close'] > option_row['ema20']:
                            option_signals.append(signal_time)
                    elif strategy == 'vwap_crossover':
                        option_df = calculate_vwap(option_df)
                        if option_row['close'] > option_row['vwap']:
                            option_signals.append(signal_time)

            charts += create_candlestick_chart(option_df, option_signals, symbol)

    return data_summary, charts

@bp.route('/analysis', methods=['GET', 'POST'])
def analysis():
    if request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        strategy = request.form.get('strategy')
        data_summary, chart_div = run_analysis(start_date, end_date, strategy)
        return render_template('analysis.html', data_summary=data_summary, chart_div=chart_div)

    data_summary = get_data_summary()
    return render_template('analysis.html', data_summary=data_summary)

@bp.route('/get_signals', methods=['GET'])
def get_signals():
    if not TESTING and not access_token:
        return jsonify({'error': 'Not logged in'}), 401

    logging.info("Starting signal generation.")
    signals = []

    try:
        data_files = os.listdir('data')
        nifty_files = [f for f in data_files if f.startswith('NIFTY50')]

        for nifty_file in nifty_files:
            try:
                nifty_df = pd.read_csv(f'data/{nifty_file}', index_col='datetime', parse_dates=True)
                nifty_df['ema10'] = talib.EMA(nifty_df['close'], timeperiod=10)
                nifty_df['ema20'] = talib.EMA(nifty_df['close'], timeperiod=20)

                nifty_df['signal'] = (nifty_df['close'] > nifty_df['ema10']) & (nifty_df['close'] > nifty_df['ema20']) & \
                                   (nifty_df['close'].shift(1) < nifty_df[['ema10', 'ema20']].shift(1).max(axis=1))

                signal_times = nifty_df[nifty_df['signal']].index

                if not signal_times.empty:
                    day_str = nifty_file.split('_')[1].replace('.csv', '')
                    option_files = [f for f in data_files if f.endswith(f'_{day_str}.csv') and not f.startswith('NIFTY50')]

                    for option_file in option_files:
                        option_df = pd.read_csv(f'data/{option_file}', index_col='datetime', parse_dates=True)
                        option_df['ema10'] = talib.EMA(option_df['close'], timeperiod=10)
                        option_df['ema20'] = talib.EMA(option_df['close'], timeperiod=20)

                        for signal_time in signal_times:
                            if signal_time in option_df.index:
                                option_row = option_df.loc[signal_time]
                                if option_row['close'] > option_row['ema10'] and option_row['close'] > option_row['ema20']:
                                    signals.append(f"Signal found for {option_file.split('_')[0]} at {signal_time}")
            except Exception as e:
                logging.error(f"Error processing {nifty_file}: {e}")

        logging.info(f"Generated {len(signals)} signals.")
        return jsonify({'signals': signals})
    except Exception as e:
        logging.error(f"Error generating signals: {e}")
        return jsonify({'error': str(e)}), 500
