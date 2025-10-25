#region Imports
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from fyers_apiv3 import fyersModel
import pandas as pd
import talib
import os
import logging
from datetime import datetime

from app.config import FYERS_CLIENT_ID, FYERS_SECRET_KEY, FYERS_REDIRECT_URI, TESTING, DATA_FOLDER_PATH
#endregion Imports

bp = Blueprint('main', __name__)

class MockFyers:
    def history(self, *args, **kwargs):
        return {
            's': 'ok',
            'candles': [
                [1672531200, 18000, 18050, 17950, 18020, 1000]
            ]
        }

fyers = None
# Initialize Fyers API client
if TESTING:
    fyers = MockFyers()
else:
    fyers = fyersModel.FyersModel(client_id=FYERS_CLIENT_ID, token=None, log_path=os.getcwd())

# In-memory storage for the access token (in a real application, use a more persistent storage)
access_token = None

@bp.route('/')
def index():    
    login_link = ''
    if 'auth_code' in request.args and 'code' in request.args:
        # auth_code = request.args.get('auth_code')
        # code = request.args.get('code')
        callback()       
        redirect(url_for('main.index'))    

    if access_token == None:
        try:
            session = fyersModel.SessionModel(client_id=FYERS_CLIENT_ID,
                                            secret_key=FYERS_SECRET_KEY,
                                            redirect_uri=FYERS_REDIRECT_URI,
                                            response_type="code")
            response = session.generate_authcode()
            logging.info("Generated auth code for Fyers login.")
            # return f'<a href="{response}">Click here to login to Fyers and get the auth code.</a>'
            login_link = response
        except Exception as e:
            logging.error(f"Error generating auth code: {e}")
            return "Error generating auth code. Please check the logs.", 500
    return render_template('index.html', user_logged_in=access_token!=None, login_link=login_link, time=datetime.now().timestamp())    
    
@bp.route('/routes')
def list_routes():
    output = []
    for rule in bp.url_map.iter_rules():
        methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
        line = f"{rule.endpoint:30s} | {methods:10s} | {rule.rule}"
        output.append(line)
    return "<pre>" + "\n".join(sorted(output)) + "</pre>"

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

#@bp.route('/callback')
def callback():
    global access_token
    global fyers
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
        fyers = fyersModel.FyersModel(token=access_token,is_async=False,client_id=FYERS_CLIENT_ID,log_path="")
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
                    tmpFilePath = f'{DATA_FOLDER_PATH}NIFTY50_{day_str}.csv'
                    if os.path.exists(tmpFilePath):
                        os.remove(tmpFilePath)
                    day_df.to_csv(tmpFilePath)

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
                    tmpFilePath = f'{DATA_FOLDER_PATH}{symbol.replace(":", "_")}_{day_str}.csv'
                    if os.path.exists(tmpFilePath):
                        os.remove(tmpFilePath)
                    day_df.to_csv(tmpFilePath)
                    #day_df.to_csv(f'data/{symbol.replace(":", "_")}_{day_str}.csv')

            logging.info(f'Options data for {symbol} downloaded and saved successfully.')
            return jsonify({'message': f'Options data for {symbol} downloaded successfully.'})
        else:
            logging.error(f"Error from Fyers API for {symbol}: {response['message']}")
            return jsonify({'error': response['message']}), 500
    except Exception as e:
        logging.error(f"Error downloading options data for {symbol}: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/get_signals', methods=['POST'])
def get_signals():
    # if not TESTING and not access_token:
    #     return jsonify({'error': 'Not logged in'}), 401

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
                                    signals.append(f"Signal found for {option_file.split('.')[0]} at {signal_time}")
            except Exception as e:
                logging.error(f"Error processing {nifty_file}: {e}")

        logging.info(f"Generated {len(signals)} signals.")
        return jsonify({'signals': signals})
    except Exception as e:
        logging.error(f"Error generating signals: {e}")
        return jsonify({'error': str(e)}), 500
