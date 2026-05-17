import time
import random
from urllib.parse import quote_plus
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

_playwright = None
_browser = None
_search_context = None  # isolated context for Yellow Pages only
_check_context = None   # separate context for business website visits
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


def _ensure_browser():
    global _playwright, _browser
    if _browser is None:
        _playwright = sync_playwright().start()
        _browser = _playwright.chromium.launch(headless=True, args=BROWSER_ARGS)


def _make_context():
    ctx = _browser.new_context(
        user_agent=USER_AGENT,
        viewport={"width": 1280, "height": 800},
        locale="en-US",
    )
    ctx.add_init_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    return ctx


def _get_search_context():
    global _search_context
    _ensure_browser()
    if _search_context is None:
        _search_context = _make_context()
    return _search_context


def _get_check_context():
    global _check_context
    _ensure_browser()
    if _check_context is None:
        _check_context = _make_context()
    return _check_context


def close_browser():
    global _playwright, _browser, _search_context, _check_context
    for ctx in (_search_context, _check_context):
        if ctx:
            try:
                ctx.close()
            except Exception:
                pass
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
    _playwright = _browser = _search_context = _check_context = None


def _new_page():
    """Page for Yellow Pages searches — uses isolated search context."""
    page = _get_search_context().new_page()
    page.set_extra_http_headers({"Accept-Language": "en-US,en;q=0.9"})
    return page


def _new_check_page():
    """Page for business website visits — uses separate check context."""
    page = _get_check_context().new_page()
    page.set_extra_http_headers({"Accept-Language": "en-US,en;q=0.9"})
    return page


def search_yelp(keyword, city, page_num=1):
    """Search Yellow Pages for one page of results. Returns (keys, has_next_page)."""
    parts = city.rsplit(" ", 1)
    geo = f"{parts[0]}, {parts[1]}" if len(parts) == 2 else city

    url = (
        f"https://www.yellowpages.com/search"
        f"?search_terms={quote_plus(keyword)}"
        f"&geo_location_terms={quote_plus(geo)}"
        f"&page={page_num}"
    )

    keys = []
    has_next = False
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

            key = website or f"nositefound://{name}|{address}"
            _cached_details[key] = {
                "name": name,
                "phone": phone,
                "address": address,
                "website": website,
                "yelp_url": key,
            }
            keys.append(key)

        has_next = page.query_selector("a.next") is not None

    except PWTimeout:
        print(f"  Timeout searching: {keyword} in {city} (page {page_num})")
    except Exception as e:
        print(f"  Search error ({keyword} in {city}): {e}")
    finally:
        page.close()

    _get_search_context().clear_cookies()
    time.sleep(random.uniform(1.0, 2.0))
    return keys, has_next


def get_business_details(key):
    return _cached_details.get(key)
