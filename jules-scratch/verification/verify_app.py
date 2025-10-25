from playwright.sync_api import sync_playwright

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()

    # Capture console logs
    page.on("console", lambda msg: print(f"CONSOLE: {msg.text}"))

    page.goto("http://127.0.0.1:5000/")

    # Fill in the form and download data
    page.fill("#start-date", "2023-01-01")
    page.fill("#end-date", "2023-01-02")
    page.click("#nifty-form button")

    page.fill("#options-symbols", "NSE:NIFTY50-INDEX")
    page.click("#options-form button")

    # Wait for the signals to appear
    page.wait_for_selector("#signals-container", state="visible")

    # Take a screenshot
    page.screenshot(path="jules-scratch/verification/verification.png")

    browser.close()

with sync_playwright() as playwright:
    run(playwright)
