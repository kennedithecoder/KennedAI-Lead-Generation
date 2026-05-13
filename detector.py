from scraper import _new_page
from config import CHATBOT_SIGNATURES

def has_chatbot(url):
    if not url or not url.startswith("http"):
        return False
    page = _new_page()
    try:
        page.goto(url, timeout=15000)
        page.wait_for_timeout(3000)
        content = page.content().lower()
        return any(sig in content for sig in CHATBOT_SIGNATURES)
    except Exception as e:
        print(f"  Could not load {url}: {e}")
        return False
    finally:
        page.close()
