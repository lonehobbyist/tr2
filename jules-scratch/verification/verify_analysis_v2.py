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

    page.goto("http://127.0.0.1:5000/analysis")

    # Run analysis for chart
    page.fill("#start-date", "2023-01-01")
    page.fill("#end-date", "2023-01-01")
    page.select_option("#strategy", "ema_crossover")
    page.select_option("#output-format", "chart")
    page.click("button[type=submit]")

    page.wait_for_selector("#chart")
    page.screenshot(path="jules-scratch/verification/analysis_chart.png")

    # Run analysis for CSV
    page.select_option("#output-format", "csv")
    page.click("button[type=submit]")

    page.wait_for_selector("table")
    page.screenshot(path="jules-scratch/verification/analysis_csv.png")

    browser.close()

with sync_playwright() as playwright:
    run(playwright)
