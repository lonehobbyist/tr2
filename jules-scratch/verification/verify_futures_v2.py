from playwright.sync_api import sync_playwright
import pandas as pd
import os
import shutil

def setup_dummy_data():
    os.makedirs('data/NIFTY/Options/2025-11-27', exist_ok=True)
    nifty_data = {'datetime': ['2023-01-01 09:15:00'], 'close': [18000], 'volume': [1000], 'high': [18050], 'low': [17950], 'open': [18000]}
    pd.DataFrame(nifty_data).to_csv('data/NIFTY/NIFTY_2023-01-01.csv', index=False)
    option_data = {'datetime': ['2023-01-01 09:15:00'], 'close': [100], 'volume': [500], 'high': [120], 'low': [90], 'open': [100]}
    pd.DataFrame(option_data).to_csv('data/NIFTY/Options/2025-11-27/NIFTY_CE_18000_2023-01-01.csv', index=False)

def run(playwright):
    if os.path.exists('data'):
        shutil.rmtree('data')

    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()

    page.goto("http://127.0.0.1:5000/futures")

    # Wait for futures symbols to load and select one
    page.wait_for_timeout(1000) # Wait for select2 to initialize
    page.select_option("#futures-symbol", "NIFTY")

    # Wait for option chain to load and select an option
    page.wait_for_selector("#option-chain-container table")
    page.check('input[data-symbol="NIFTY25NOV18000CE"]')

    # Download data
    page.fill("#start-date-futures", "2023-01-01")
    page.fill("#end-date-futures", "2023-01-01")
    page.click("#download-options-btn")

    # Go to analysis page and run analysis
    page.goto("http://127.0.0.1:5000/analysis")
    page.fill("#start-date", "2023-01-01")
    page.fill("#end-date", "2023-01-01")
    page.select_option("#strategy", "ema_crossover")
    page.select_option("#output-format", "chart")
    page.click("button[type=submit]")

    page.wait_for_selector("#chart")
    page.screenshot(path="jules-scratch/verification/futures_analysis_v2.png")

    browser.close()

with sync_playwright() as playwright:
    run(playwright)
