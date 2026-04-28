# Lead Generation Agent — Project Overview

## What This Is

An automated Python agent that finds small businesses in high-value metro areas across the **East Coast and Midwest** that are missing AI chatbots on their websites. Target industries: **dentists, salons, and medical clinics**. Qualified leads are written directly to a Google Sheet.

---

## Target Markets

### East Coast
Naples FL, Boca Raton FL, Coral Gables FL, Bethesda MD, McLean VA, Greenwich CT, Charlotte NC, Raleigh NC, Atlanta GA, Princeton NJ, Westchester NY

### Midwest / South
Highland Park TX, Southlake TX, The Woodlands TX, Austin TX, Nashville TN, Franklin TN, Naperville IL, Winnetka IL, Lake Forest IL, Edina MN, Leawood KS

---

## Target Industries & Search Keywords

| Industry | Keywords |
|----------|----------|
| Dental | dentist, dental clinic, orthodontist |
| Salons | hair salon, nail salon, day spa, beauty salon |
| Medical | medical clinic, family doctor, urgent care |

---

## What Was Built

### `config.py`
Central configuration: Google Sheet ID, industry keyword groups, city list, and chatbot signature strings used for detection.

### `scraper.py`
Scrapes Yelp search results for a given keyword + city pair. Returns up to 10 business profile URLs, then pulls each business's name, phone, address, and website URL from their Yelp page.

### `detector.py`
Uses **Playwright** (headless Chromium) to fully render each business's website and scan the page source for known chatbot signatures: Intercom, Drift, Crisp, Tidio, Zendesk, Freshchat, LiveChat, Tawk.to, HubSpot, Olark, PureChat, and others. Businesses that already have a chatbot are skipped.

### `extractor.py`
Crawls the business website to find:
- **Email address** — checks homepage for `mailto:` links and regex email patterns, then follows contact/about/team sub-pages.
- **Decision maker name** — scans contact and about pages for names near titles like Owner, Founder, Director, CEO, Dr., Principal, Manager.

### `logger.py`
Maintains a local `searched.txt` file to persist which websites have already been processed across runs, preventing duplicate work.

### `main.py`
Orchestrates the full pipeline:
1. Connects to Google Sheets via a service account (`creds.json`)
2. Loads existing sheet data to avoid duplicates (checks website, name, and address)
3. Loads the local search log
4. Iterates every industry × keyword × city combination
5. For each business: scrapes details → deduplicates → checks for chatbot → extracts contact info → appends row to sheet

**Sheet columns:** Name, Phone, Email, Decision Maker, Address, Industry, Website, Status (`New Lead`)

---

## Tech Stack

| Tool | Purpose |
|------|---------|
| `requests` + `BeautifulSoup` | Yelp scraping and contact extraction |
| `Playwright` (headless Chromium) | JavaScript-rendered chatbot detection |
| `gspread` + Google Sheets API | Lead output and duplicate checking |
| `google-auth` | Service account authentication |

---

## How to Run

```bash
# Install dependencies
pip install requests beautifulsoup4 playwright gspread google-auth
playwright install chromium

# Run the agent
python main.py
```

Requires `creds.json` (Google service account key) in the project root and the target Sheet shared with the service account email.

---

## Deduplication Strategy

The agent avoids writing the same business twice using three checks (applied in order):
1. Website URL already in sheet
2. Business name already in sheet
3. Address already in sheet

It also skips any website already recorded in `searched.txt` from a prior run.

---

## Chatbot Signatures Detected

`intercom`, `drift`, `crisp`, `tidio`, `zendesk`, `freshchat`, `livechat`, `tawk.to`, `hubspot-messages`, `olark`, `purechat`, `chatbot`, `chat-widget`, `fb-messenger`
