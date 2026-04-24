import requests
from bs4 import BeautifulSoup
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def search_yelp(keyword, city):
    query = f"{keyword} {city}".replace(" ", "+")
    url = f"https://www.yelp.com/search?find_desc={query}"
    res = requests.get(url, headers=HEADERS, timeout=10)
    soup = BeautifulSoup(res.text, "html.parser")

    businesses = []
    links = soup.find_all("a", href=re.compile(r"/biz/"))
    seen = set()
    for link in links:
        href = link.get("href", "")
        if href not in seen and "/biz/" in href:
            seen.add(href)
            businesses.append("https://www.yelp.com" + href.split("?")[0])

    return businesses[:10]


def get_business_details(yelp_url):
    try:
        res = requests.get(yelp_url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        name = soup.find("h1")
        name = name.get_text(strip=True) if name else "Unknown"

        phone = ""
        phone_tag = soup.find("p", string=re.compile(r"\(\d{3}\)"))
        if phone_tag:
            phone = phone_tag.get_text(strip=True)

        
        address = ""
        location = soup.find("p", {"data-font-weight": "semibold"})
        if location:
           address = location.get_text(strip=True)

        website = ""
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "yelp.com" not in href and href.startswith("http"):
                website = href
                break

        return {
            "name": name,
            "phone": phone,
            "address": address,
            "website": website,
            "yelp_url": yelp_url
        }
    except Exception as e:
        print(f"  Error scraping {yelp_url}: {e}")
        return None