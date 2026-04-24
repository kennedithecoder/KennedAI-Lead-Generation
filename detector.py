from playwright.sync_api import sync_playwright
from config import CHATBOT_SIGNATURES

def has_chatbot(url):
    if not url or not url.startswith("http"):
        return False
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=15000)
            page.wait_for_timeout(3000)
            content = page.content().lower()
            browser.close()
            return any(sig in content for sig in CHATBOT_SIGNATURES)
    except Exception as e:
        print(f"  Could not load {url}: {e}")
        return False