import unittest
from unittest.mock import patch, MagicMock
from app import create_app
import json
import pandas as pd
import os
import shutil

class TestRoutes(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        # Create a dummy data directory for testing
        if not os.path.exists('data'):
            os.makedirs('data')

    def tearDown(self):
        # Clean up dummy data files
        if os.path.exists('data'):
            shutil.rmtree('data')

    @patch('app.routes.access_token', 'dummy_token')
    @patch('app.routes.fyers.history')
    def test_download_nifty_data_success(self, mock_history):
        mock_history.return_value = {
            's': 'ok',
            'candles': [
                [1672531200, 18000, 18050, 17950, 18020, 1000]
            ]
        }

        response = self.client.post('/download_nifty_data',
                                     data=json.dumps({'start_date': '2023-01-01', 'end_date': '2023-01-01'}),
                                     content_type='application/json')

        self.assertEqual(response.status_code, 200)
        self.assertIn('NIFTY50 data downloaded successfully.', response.get_data(as_text=True))
        self.assertTrue(os.path.exists('data/NIFTY50_2023-01-01.csv'))

    @patch('app.routes.access_token', 'dummy_token')
    @patch('app.routes.fyers.history')
    def test_get_signals_success(self, mock_history):
        # Create dummy data files for testing
        nifty_data = {'datetime': ['2023-01-01 09:15:00', '2023-01-01 09:20:00'],
                      'open': [18000, 18020], 'high': [18050, 18060], 'low': [17950, 18010],
                      'close': [18020, 18050], 'volume': [1000, 1200]}
        nifty_df = pd.DataFrame(nifty_data)
        nifty_df.to_csv('data/NIFTY50_2023-01-01.csv', index=False)

        option_data = {'datetime': ['2023-01-01 09:15:00', '2023-01-01 09:20:00'],
                       'open': [100, 110], 'high': [120, 130], 'low': [90, 105],
                       'close': [115, 125], 'volume': [500, 600]}
        option_df = pd.DataFrame(option_data)
        option_df.to_csv('data/NSE_NIFTY50_CE_18000_2023-01-01.csv', index=False)

        response = self.client.get('/get_signals')

        self.assertEqual(response.status_code, 200)
        # This is a simplified check; a more robust test would mock the talib functions
        self.assertIn('signals', response.get_data(as_text=True))

if __name__ == '__main__':
    unittest.main()
