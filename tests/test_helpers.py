import unittest
from unittest.mock import patch
import pandas as pd
from app.helpers import load_data_from_csv, calculate_vwap, get_data_summary, get_futures_symbols
import os
import shutil

class TestHelpers(unittest.TestCase):

    def setUp(self):
        os.makedirs('data/NIFTY/Options/2025-11-27', exist_ok=True)

        nifty_data = {'datetime': ['2023-01-01 09:15:00'], 'close': [18000], 'volume': [1000], 'high': [18050], 'low': [17950], 'open': [18000]}
        pd.DataFrame(nifty_data).to_csv('data/NIFTY/NIFTY_2023-01-01.csv', index=False)

        option_data = {'datetime': ['2023-01-01 09:15:00'], 'close': [100], 'volume': [500], 'high': [120], 'low': [90], 'open': [100]}
        pd.DataFrame(option_data).to_csv('data/NIFTY/Options/2025-11-27/NIFTY_CE_18000_2023-01-01.csv', index=False)

    def tearDown(self):
        shutil.rmtree('data')

    def test_load_data_from_csv_futures(self):
        df = load_data_from_csv('NIFTY', '2023-01-01', '2023-01-01')
        self.assertEqual(len(df), 1)

    def test_load_data_from_csv_options(self):
        df = load_data_from_csv('NIFTY', '2023-01-01', '2023-01-01', expiry='2025-11-27')
        self.assertEqual(len(df), 1)

    def test_get_data_summary(self):
        summary = get_data_summary()
        self.assertIn('NIFTY', summary['futures_dates'])
        self.assertIn('2023-01-01', summary['futures_dates']['NIFTY'][0])
        self.assertIn('NIFTY', summary['options_dates'])
        self.assertIn('2025-11-27', summary['options_dates']['NIFTY'])
        self.assertIn('2023-01-01', summary['options_dates']['NIFTY']['2025-11-27'][0])

    def test_calculate_vwap(self):
        data = {'datetime': pd.to_datetime(['2023-01-01 09:15:00', '2023-01-01 09:20:00']),
                'open': [100, 101], 'high': [102, 102], 'low': [99, 100],
                'close': [101, 101], 'volume': [100, 150]}
        df = pd.DataFrame(data).set_index('datetime')
        df = calculate_vwap(df)
        self.assertIn('vwap', df.columns)
        self.assertAlmostEqual(df['vwap'].iloc[-1], 100.9, places=1)

    @patch('app.helpers.pd.read_csv')
    def test_get_futures_symbols(self, mock_read_csv):
        mock_df = pd.DataFrame({12: ['NIFTY', 'BANKNIFTY', 'NIFTY']})
        mock_read_csv.return_value = mock_df
        symbols = get_futures_symbols()
        self.assertEqual(symbols, ['BANKNIFTY', 'NIFTY'])

if __name__ == '__main__':
    unittest.main()
