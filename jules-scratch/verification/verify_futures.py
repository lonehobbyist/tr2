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
    setup_dummy_data()

    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()

    page.goto("http://127.0.0.1:5000/futures")

    # Wait for futures symbols to load
    page.wait_for_timeout(1000) # 1 second delay

    # Download futures data
    page.select_option("#futures-symbol", "NIFTY")
    page.fill("#start-date-futures", "2023-01-01")
    page.fill("#end-date-futures", "2023-01-01")
    page.click("#futures-form button")

    # Download options data
    page.wait_for_selector("#expiry-dropdown option")
    page.select_option("#expiry-dropdown", "2025-11-27")
    page.wait_for_selector("#strike-dropdown option")
    page.select_option("#strike-dropdown", "18000")
    page.click("#options-form button")

    # Go to analysis page and run analysis
    page.goto("http://127.0.0.1:5000/analysis")
    page.fill("#start-date", "2023-01-01")
    page.fill("#end-date", "2023-01-01")
    page.select_option("#strategy", "ema_crossover")
    page.select_option("#output-format", "chart")
    page.click("button[type=submit]")

    page.wait_for_selector("#chart")
    page.screenshot(path="jules-scratch/verification/futures_analysis.png")

    browser.close()

with sync_playwright() as playwright:
    run(playwright)
