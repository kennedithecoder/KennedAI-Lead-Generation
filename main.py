import gspread
from google.oauth2.service_account import Credentials
import time
from config import SHEET_ID, INDUSTRIES, CITIES
from scraper import search_yelp, get_business_details
from detector import has_chatbot
from extractor import find_email, find_director
from logger import load_searched, log_searched

creds = Credentials.from_service_account_file("creds.json", scopes=[
    "https://www.googleapis.com/auth/spreadsheets"
])
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).sheet1

# Load existing data from sheet for duplicate checking
existing_rows = sheet.get_all_values()[1:]
existing_websites = set(row[5] for row in existing_rows if len(row) > 5 and row[5])   # column F - Website
existing_names = set(row[2].lower() for row in existing_rows if len(row) > 2 and row[2])  # column C - Company
existing_addresses = set(row[4].lower() for row in existing_rows if len(row) > 4 and row[4])  # column E - City, State

searched = load_searched()

print("Starting lead generation agent...\n")

for industry_label, keywords in INDUSTRIES.items():
    for keyword in keywords:
        for city in CITIES:
            print(f"Searching: {keyword} in {city}")
            listings = search_yelp(keyword, city)

            for yelp_url in listings:
                details = get_business_details(yelp_url)
                if not details:
                    continue

                website = details["website"]
                name = details["name"]
                address = details["address"]

                # Check if already in sheet by website
                if website and website in existing_websites:
                    print(f"  Already in sheet (website match): {name}")
                    continue

                # Check if already in sheet by name
                if name and name.lower() in existing_names:
                    print(f"  Already in sheet (name match): {name}")
                    continue

                # Check if already in sheet by address
                if address and address.lower() in existing_addresses:
                    print(f"  Already in sheet (address match): {name}")
                    continue

                # Check if already searched before
                if website and website in searched:
                    print(f"  Already searched before: {name}")
                    continue

                # Log it immediately
                if website:
                    log_searched(website)
                    searched.add(website)
                    existing_websites.add(website)

                existing_names.add(name.lower())
                existing_addresses.add(address.lower())

                # Check for chatbot
                chatbot_found = has_chatbot(website)
                if chatbot_found:
                    print(f"  Has chatbot — skipping")
                    continue

                # Extract contact info
                email = find_email(website) if website else ""
                director = find_director(website) if website else ""

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
                print(f"  Added: {name} ({address})")

                time.sleep(2)

print("\nDone! Check your Google Sheet.")