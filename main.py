import gspread
from google.oauth2.service_account import Credentials
import time
from config import SHEET_ID, INDUSTRIES, CITIES
from scraper import search_yelp, get_business_details, close_browser
from extractor import check_website
from logger import load_searched, log_searched
from progress import load_progress, save_progress

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

# Flat ordered list of every (industry, keyword, city) combination
queries = []
for industry_label, keywords in INDUSTRIES.items():
    for keyword in keywords:
        for city in CITIES:
            queries.append((industry_label, keyword, city))

# Resume from saved position
progress = load_progress()
query_index = progress["query_index"]
current_page = progress["page"]

if query_index >= len(queries):
    print("All queries completed. Starting over from the beginning.\n")
    query_index = 0
    current_page = 1

industry_label, keyword, city = queries[query_index]

print(f"Starting lead generation agent...")
print(f"Resuming: '{keyword}' in {city} — page {current_page}\n")

leads_added = 0
skipped_duplicate = 0
skipped_chatbot = 0
skipped_searched = 0
cap_hit = False

try:
    # Keep paginating the current query until 30 leads are found or query is exhausted
    while leads_added < MAX_LEADS_PER_RUN:
        listings, has_next = search_yelp(keyword, city, page_num=current_page)
        print(f"  Page {current_page} — {len(listings)} businesses found")

        if not listings:
            has_next = False

        for yelp_url in listings:
            details = get_business_details(yelp_url)
            if not details:
                continue

            website = details["website"]
            name = details["name"]
            address = details["address"]

            if website and website in existing_websites:
                print(f"  Skip (duplicate): {name}")
                skipped_duplicate += 1
                continue

            if name and name.lower() in existing_names:
                print(f"  Skip (duplicate): {name}")
                skipped_duplicate += 1
                continue

            if address and address.lower() in existing_addresses:
                print(f"  Skip (duplicate): {name}")
                skipped_duplicate += 1
                continue

            if website and website in searched:
                print(f"  Skip (already searched): {name}")
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
                cap_hit = True
                break

            time.sleep(2)

        if cap_hit:
            # Hit 30 leads mid-page — re-process same page next run (duplicates filter already-done ones)
            save_progress(query_index, current_page)
            print(f"\nReached {MAX_LEADS_PER_RUN} leads. Next run resumes: '{keyword}' in {city} — page {current_page}")
            break

        if has_next:
            # More pages exist for this query — continue to next page
            current_page += 1
        else:
            # Query exhausted — move to next query next run
            next_index = query_index + 1
            if next_index >= len(queries):
                save_progress(0, 1)
                print(f"\nAll queries completed! Next run will start from the beginning.")
            else:
                next_industry, next_kw, next_city = queries[next_index]
                save_progress(next_index, 1)
                print(f"\n'{keyword}' in {city} fully processed. Next run: '{next_kw}' in {next_city}")
            break

finally:
    close_browser()

print(f"\nDone! Added: {leads_added} | Duplicates: {skipped_duplicate} | Already searched: {skipped_searched} | Chatbot filtered: {skipped_chatbot}")
print("Check your Google Sheet.")
