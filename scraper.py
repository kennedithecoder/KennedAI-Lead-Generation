import time
import random
from urllib.parse import quote_plus
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

_playwright = None
_browser = None
_context = None
_cached_details = {}

BROWSER_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
    "--disable-dev-shm-usage",
]

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def _get_context():
    global _playwright, _browser, _context
    if _context is None:
        _playwright = sync_playwright().start()
        _browser = _playwright.chromium.launch(headless=True, args=BROWSER_ARGS)
        _context = _browser.new_context(
            user_agent=USER_AGENT,
            viewport={"width": 1280, "height": 800},
            locale="en-US",
        )
        _context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
    return _context


def close_browser():
    global _playwright, _browser, _context
    if _browser:
        try:
            _browser.close()
        except Exception:
            pass
    if _playwright:
        try:
            _playwright.stop()
        except Exception:
            pass
    _playwright = _browser = _context = None


def _new_page():
    page = _get_context().new_page()
    page.set_extra_http_headers({"Accept-Language": "en-US,en;q=0.9"})
    return page


def search_yelp(keyword, city):
    """Search Yellow Pages and return opaque keys for get_business_details."""
    # Convert "Naples FL" -> "Naples, FL"
    parts = city.rsplit(" ", 1)
    geo = f"{parts[0]}, {parts[1]}" if len(parts) == 2 else city

    url = (
        f"https://www.yellowpages.com/search"
        f"?search_terms={quote_plus(keyword)}"
        f"&geo_location_terms={quote_plus(geo)}"
    )

    keys = []
    page = _new_page()
    try:
        page.goto(url, timeout=20000, wait_until="domcontentloaded")
        page.wait_for_timeout(2500)

        cards = page.query_selector_all("div.result")
        for card in cards:
            name_el = card.query_selector("a.business-name")
            phone_el = card.query_selector("div.phone")
            addr_el = card.query_selector("p.adr")
            site_el = card.query_selector('a[href^="http"][rel="nofollow noopener"]')

            name = name_el.inner_text().strip() if name_el else "Unknown"
            phone = phone_el.inner_text().strip() if phone_el else ""
            address = addr_el.inner_text().strip() if addr_el else ""
            website = site_el.get_attribute("href") if site_el else ""

            # Use website as cache key; fall back to name+address
            key = website or f"nositefound://{name}|{address}"
            _cached_details[key] = {
                "name": name,
                "phone": phone,
                "address": address,
                "website": website,
                "yelp_url": key,
            }
            keys.append(key)

    except PWTimeout:
        print(f"  Timeout searching: {keyword} in {city}")
    except Exception as e:
        print(f"  Search error ({keyword} in {city}): {e}")
    finally:
        page.close()

    time.sleep(random.uniform(1.0, 2.0))
    return keys[:10]


def get_business_details(key):
    return _cached_details.get(key)
