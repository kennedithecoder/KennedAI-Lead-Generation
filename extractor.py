import re
from urllib.parse import urlparse
from scraper import _new_check_page
from config import CHATBOT_SIGNATURES

CONTACT_KEYWORDS = ["contact", "about", "team", "staff", "reach", "connect"]

# Titles used to find person names — order matters (most specific first)
_TITLE_GROUP = r"(?:Owner|Founder|Director|President|CEO|Principal|Manager|DDS|DMD|MD|DO|RN|PA)"
_NAME = r"[A-Z][a-z]+(?:-[A-Z][a-z]+)?\s+[A-Z][a-z]+"


def _extract_email(text, page):
    for a in page.query_selector_all("a[href^='mailto:']"):
        href = a.get_attribute("href") or ""
        email = href.replace("mailto:", "").split("?")[0].strip()
        if email:
            return email
    emails = re.findall(r"[\w.\-]+@[\w.\-]+\.\w{2,}", text)
    return emails[0] if emails else ""


def _extract_director(text):
    # 1. "Dr. First Last" — strongest signal for dental/medical
    m = re.search(rf"Dr\.?\s+({_NAME})", text)
    if m:
        return "Dr. " + m.group(1)

    # 2. "First Last, Title" — name immediately followed by a comma and title
    m = re.search(rf"({_NAME}),?\s+{_TITLE_GROUP}\b", text)
    if m:
        return m.group(1)

    # 3. "Title: First Last" or "Title First Last" — title leads
    m = re.search(rf"{_TITLE_GROUP}[:\s]+({_NAME})", text)
    if m:
        return m.group(1)

    return ""


def _contact_links(base_url, page):
    parsed = urlparse(base_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    links = []
    for a in page.query_selector_all("a[href]"):
        href = (a.get_attribute("href") or "").strip()
        text = (a.inner_text() or "").lower()
        if not any(kw in href.lower() or kw in text for kw in CONTACT_KEYWORDS):
            continue
        if href.startswith("/"):
            full = base + href
        elif href.startswith("http"):
            full = href
        else:
            continue
        if full not in links:
            links.append(full)
    return links[:3]


def check_website(website):
    """
    Single Playwright visit that returns chatbot status, email, and director.
    Replaces has_chatbot + find_email + find_director (3 separate visits → 1).
    """
    if not website or not website.startswith("http"):
        return False, "", ""

    page = _new_check_page()
    try:
        page.goto(website, timeout=15000)
        page.wait_for_timeout(2000)

        html = page.content().lower()
        text = page.inner_text("body")

        if any(sig in html for sig in CHATBOT_SIGNATURES):
            return True, "", ""

        email = _extract_email(text, page)
        director = _extract_director(text)

        if not email or not director:
            for link in _contact_links(website, page):
                try:
                    page.goto(link, timeout=8000)
                    page.wait_for_timeout(800)
                    sub_text = page.inner_text("body")
                    if not email:
                        email = _extract_email(sub_text, page)
                    if not director:
                        director = _extract_director(sub_text)
                    if email and director:
                        break
                except Exception:
                    continue

        return False, email, director

    except Exception as e:
        print(f"  Could not load {website}: {e}")
        return False, "", ""
    finally:
        page.close()
