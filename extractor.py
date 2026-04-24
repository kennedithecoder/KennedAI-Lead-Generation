import requests
from bs4 import BeautifulSoup
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

DIRECTOR_TITLES = ["owner", "founder", "director", "president", "ceo", "principal", "manager", "dr."]


def find_contact_links(base_url, soup):
    """Find links on the page that are likely contact or about pages."""
    contact_keywords = ["contact", "about", "team", "staff", "reach", "connect", "get in touch"]
    contact_links = []

    for a in soup.find_all("a", href=True):
        href = a["href"].lower()
        text = a.get_text(strip=True).lower()

        if any(keyword in href or keyword in text for keyword in contact_keywords):
            if href.startswith("/"):
                full_url = base_url.rstrip("/") + href
            elif href.startswith("http"):
                full_url = href
            else:
                continue

            if full_url not in contact_links:
                contact_links.append(full_url)

    return contact_links[:5]


def find_email(base_url):
    try:
        # Load homepage first
        res = requests.get(base_url, headers=HEADERS, timeout=8)
        soup = BeautifulSoup(res.text, "html.parser")

        # Check homepage for email
        for a in soup.find_all("a", href=re.compile(r"mailto:")):
            email = a["href"].replace("mailto:", "").split("?")[0].strip()
            if email:
                return email
        emails = re.findall(r"[\w\.\-]+@[\w\.\-]+\.\w{2,}", soup.get_text())
        if emails:
            return emails[0]

        # Follow relevant links found on homepage
        contact_links = find_contact_links(base_url, soup)
        for url in contact_links:
            try:
                res = requests.get(url, headers=HEADERS, timeout=8)
                soup = BeautifulSoup(res.text, "html.parser")
                for a in soup.find_all("a", href=re.compile(r"mailto:")):
                    email = a["href"].replace("mailto:", "").split("?")[0].strip()
                    if email:
                        return email
                emails = re.findall(r"[\w\.\-]+@[\w\.\-]+\.\w{2,}", soup.get_text())
                if emails:
                    return ", ".join(emails)
            except:
                continue
    except:
        pass
    return ""


def find_director(base_url):
    try:
        # Load homepage and find relevant links
        res = requests.get(base_url, headers=HEADERS, timeout=8)
        soup = BeautifulSoup(res.text, "html.parser")

        contact_links = find_contact_links(base_url, soup)
        for url in contact_links:
            try:
                res = requests.get(url, headers=HEADERS, timeout=8)
                soup = BeautifulSoup(res.text, "html.parser")
                for title in DIRECTOR_TITLES:
                    pattern = rf"([A-Z][a-z]+ [A-Z][a-z]+)[^{{}}]{{0,40}}{title}"
                    match = re.search(pattern, soup.get_text(" ", strip=True), re.IGNORECASE)
                    if match:
                        return match.group(1)
            except:
                continue
    except:
        pass
    return ""