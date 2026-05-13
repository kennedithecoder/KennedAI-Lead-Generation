import gspread
from google.oauth2.service_account import Credentials
import time
from config import SHEET_ID, INDUSTRIES, CITIES
from scraper import search_yelp, get_business_details, close_browser
from extractor import check_website
from logger import load_searched, log_searched

creds = Credentials.from_service_account_file("creds.json", scopes=[
    "https://www.googleapis.com/auth/spreadsheets"
])
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).sheet1

existing_rows = sheet.get_all_values()[1:]
existing_websites = set(row[5] for row in existing_rows if len(row) > 5 and row[5])
existing_names = set(row[2].lower() for row in existing_rows if len(row) > 2 and row[2])
existing_addresses = set(row[4].lower() for row in existing_rows if len(row) > 4 and row[4])

searched = load_searched()

MAX_LEADS_PER_RUN = 30

print("Starting lead generation agent...\n")

leads_added = 0
skipped_duplicate = 0
skipped_chatbot = 0
skipped_searched = 0

try:
    for industry_label, keywords in INDUSTRIES.items():
        for keyword in keywords:
            for city in CITIES:
                if leads_added >= MAX_LEADS_PER_RUN:
                    break
                print(f"Searching: {keyword} in {city}")
                listings = search_yelp(keyword, city)

                for yelp_url in listings:
                    details = get_business_details(yelp_url)
                    if not details:
                        continue

                    website = details["website"]
                    name = details["name"]
                    address = details["address"]

                    if website and website in existing_websites:
                        skipped_duplicate += 1
                        continue

                    if name and name.lower() in existing_names:
                        skipped_duplicate += 1
                        continue

                    if address and address.lower() in existing_addresses:
                        skipped_duplicate += 1
                        continue

                    if website and website in searched:
                        skipped_searched += 1
                        continue

                    if website:
                        log_searched(website)
                        searched.add(website)
                        existing_websites.add(website)

                    existing_names.add(name.lower())
                    existing_addresses.add(address.lower())

                    print(f"  Checking {name}...", end="", flush=True)
                    chatbot_found, email, director = check_website(website)
                    if chatbot_found:
                        print(" chatbot — skipping")
                        skipped_chatbot += 1
                        continue

                    row = [
                        director,               # A - POC
                        "New Lead",             # B - Stage
                        name,                   # C - Company
                        industry_label.title(), # D - Industry
                        address,                # E - City, State
                        website,                # F - Website
                        "",                     # G - LinkedIn (blank for now)
                        details["phone"],       # H - Phone Number
                        email,                  # I - Email
                        "",                     # J - Service Offered (fill manually)
                        "",                     # K - Fees Quoted (fill manually)
                        "",                     # L - Notes (fill manually)
                    ]

                    sheet.append_row(row)
                    leads_added += 1
                    print(f" added! ({leads_added}/{MAX_LEADS_PER_RUN}): {name} ({address})")
                    if leads_added >= MAX_LEADS_PER_RUN:
                        print(f"\nReached {MAX_LEADS_PER_RUN}-lead limit for this run.")
                        break

                    time.sleep(2)
finally:
    close_browser()

print(f"\nDone! Added: {leads_added} | Duplicates skipped: {skipped_duplicate} | Already searched: {skipped_searched} | Chatbot filtered: {skipped_chatbot}")
print("Check your Google Sheet.")
