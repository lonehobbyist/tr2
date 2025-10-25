import unittest
import pandas as pd
from app.helpers import load_data_from_csv, calculate_vwap, get_data_summary
import os

class TestHelpers(unittest.TestCase):

    def setUp(self):
        # Create a dummy data directory and files for testing
        os.makedirs('data', exist_ok=True)
        nifty_data_1 = {'datetime': ['2023-01-01 09:15:00'],
                        'open': [18000], 'high': [18050], 'low': [17950],
                        'close': [18020], 'volume': [1000]}
        nifty_df_1 = pd.DataFrame(nifty_data_1)
        nifty_df_1.to_csv('data/NIFTY50_2023-01-01.csv', index=False)

        nifty_data_2 = {'datetime': ['2023-01-02 09:15:00'],
                        'open': [18100], 'high': [18150], 'low': [18050],
                        'close': [18120], 'volume': [1200]}
        nifty_df_2 = pd.DataFrame(nifty_data_2)
        nifty_df_2.to_csv('data/NIFTY50_2023-01-02.csv', index=False)

        option_data = {'datetime': ['2023-01-01 09:15:00'],
                       'open': [100], 'high': [120], 'low': [90],
                       'close': [115], 'volume': [500]}
        option_df = pd.DataFrame(option_data)
        option_df.to_csv('data/NSE_NIFTY_CE_18000_2023-01-01.csv', index=False)

    def tearDown(self):
        # Clean up dummy data files
        for f in os.listdir('data'):
            os.remove(os.path.join('data', f))
        os.rmdir('data')

    def test_load_data_from_csv(self):
        df = load_data_from_csv('NIFTY50', '2023-01-01', '2023-01-01')
        self.assertEqual(len(df), 1)

        df = load_data_from_csv('NIFTY50', '2023-01-01', '2023-01-02')
        self.assertEqual(len(df), 2)

    def test_calculate_vwap(self):
        data = {'datetime': ['2023-01-01 09:15:00', '2023-01-01 09:20:00'],
                'open': [100, 101], 'high': [102, 102], 'low': [99, 100],
                'close': [101, 101], 'volume': [100, 150]}
        df = pd.DataFrame(data).set_index(pd.to_datetime(data['datetime']))
        df = calculate_vwap(df)
        self.assertIn('vwap', df.columns)
        self.assertAlmostEqual(df['vwap'].iloc[-1], 100.9, places=1)

    def test_get_data_summary(self):
        summary = get_data_summary()
        self.assertIn('2023-01-01', summary['nifty_dates'])
        self.assertIn('NSE_NIFTY_CE_18000', summary['options_dates'])
        self.assertIn('2023-01-01', summary['options_dates']['NSE_NIFTY_CE_18000'])

if __name__ == '__main__':
    unittest.main()
