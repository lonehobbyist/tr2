from playwright.sync_api import sync_playwright
import pandas as pd
import os

def setup_dummy_data():
    os.makedirs('data', exist_ok=True)
    nifty_data = {'datetime': ['2023-01-01 09:15:00', '2023-01-02 09:15:00'],
                  'open': [18000, 18100], 'high': [18050, 18150], 'low': [17950, 18050],
                  'close': [18020, 18120], 'volume': [1000, 1200]}
    nifty_df = pd.DataFrame(nifty_data)
    nifty_df.to_csv('data/NIFTY50_2023-01-01.csv', index=False)
    nifty_df.to_csv('data/NIFTY50_2023-01-02.csv', index=False)

    option_data = {'datetime': ['2023-01-01 09:15:00'],
                   'open': [100], 'high': [120], 'low': [90],
                   'close': [115], 'volume': [500]}
    option_df = pd.DataFrame(option_data)
    option_df.to_csv('data/NSE_NIFTY_CE_18000_2023-01-01.csv', index=False)

def run(playwright):
    setup_dummy_data()
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()

    page.goto("http://127.0.0.1:5000/analysis")

    # Fill in the form and submit
    page.fill("#start-date", "2023-01-01")
    page.fill("#end-date", "2023-01-02")
    page.select_option("#strategy", "ema_crossover")
    page.click("button[type=submit]")

    # Wait for the chart to appear
    page.wait_for_selector("#chart")

    # Take a screenshot
    page.screenshot(path="jules-scratch/verification/analysis_verification.png")

    browser.close()

with sync_playwright() as playwright:
    run(playwright)
