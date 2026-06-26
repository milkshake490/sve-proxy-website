import requests
from bs4 import BeautifulSoup
import os
import time
import re
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

BASE_URL = "https://en.shadowverse-evolve.com"
SAVE_DIR = "all_cards_numbered"

os.makedirs(SAVE_DIR, exist_ok=True)

# -------------------------
# THREADING / RATE LIMITING
# -------------------------
lock = threading.Lock()
last_request_time = 0
RATE_LIMIT = 0.1  # ~10 requests/sec max

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9"
}


def rate_limited_get(url, headers):
    global last_request_time

    with lock:
        now = time.time()
        wait = RATE_LIMIT - (now - last_request_time)

        if wait > 0:
            time.sleep(wait)

        last_request_time = time.time()

    return requests.get(url, headers=headers, timeout=15)


# -------------------------
# SETS
# -------------------------
EXPANSIONS = [
    "BP01", "BP02", "BP03", "BP04", "BP05",
    "BP06", "BP07", "BP08", "BP09", "BP10",
    "BP11", "BP12", "BP13", "BP14", "BP15",
    "BP16", "BP17", "CP01", "CP02", "CP03", 
    "ECP01", "ECP02", "SP01"
]

STARTER_DECKS = [
    "SD01", "SD02", "SD03", "SD04",
    "SD05", "SD06", "CSD01", "CSD02", "CSD03",
    "GFB01", "GFD01", "GFD02"
]

PROMOS = [
    "PR"
]

ALL_SETS = EXPANSIONS + STARTER_DECKS + PROMOS


# -------------------------
# FILENAME CLEANING
# -------------------------
def clean_filename(name):
    name = name.strip().lower()
    name = re.sub(r'[^a-z0-9 ]', '', name)
    name = name.replace(" ", "_")
    return name


# -------------------------
# SCRAPE CARD LIST PAGE
# -------------------------
def get_cards(set_code, page):
    url = (
        f"{BASE_URL}/cards/searchresults_ex"
        f"?expansion_name={set_code}&view=image&page={page}"
    )

    print(f"[{set_code}] Fetching page {page}...")

    try:
        res = rate_limited_get(url, headers)

        if res.status_code != 200:
            print(f"[{set_code}] HTTP {res.status_code}")
            return []

        soup = BeautifulSoup(res.text, "html.parser")

        cards = []

        for li in soup.find_all("li"):
            a_tag = li.find("a")
            img = li.find("img")

            if not a_tag or not img:
                continue

            href = a_tag.get("href", "")
            src = img.get("src", "")
            name = img.get("title") or img.get("alt")

            if not src or not name:
                continue

            # Ignore junk images
            if "cardlist" not in src.lower():
                continue

            # Extract card number
            match = re.search(r'cardno=([A-Z0-9\-]+)', href)

            if not match:
                continue

            card_number = match.group(1)

            full_url = urljoin(BASE_URL, src)

            cards.append({
                "name": name,
                "number": card_number,
                "url": full_url
            })

        return cards

    except Exception as e:
        print(f"[{set_code}] Error fetching page {page}: {e}")
        return []


# -------------------------
# DOWNLOAD CARD
# -------------------------
def download_card(card, seen):
    number = card["number"]
    name = clean_filename(card["name"])

    filename = f"{number}_{name}.png"
    path = os.path.join(SAVE_DIR, filename)

    # Reserve filename before download
    with lock:
        if filename in seen or os.path.exists(path):
            print(f"Skipped: {filename}")
            return

        seen.add(filename)

    try:
        res = rate_limited_get(card["url"], headers)

        if res.status_code == 200:
            with open(path, "wb") as f:
                f.write(res.content)

            print(f"Downloaded: {filename}")

        else:
            print(f"Failed ({res.status_code}): {filename}")

    except Exception as e:
        print(f"Error downloading {filename}: {e}")


# -------------------------
# MAIN
# -------------------------
seen = set()
MAX_WORKERS = 10

with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:

    for set_code in ALL_SETS:

        print(f"\n========== {set_code} ==========")

        page = 1

        while True:

            cards = get_cards(set_code, page)

            # No cards found
            if not cards:
                print(f"{set_code}: Finished.")
                break

            print(f"{set_code} Page {page}: {len(cards)} cards")

            futures = [
                executor.submit(download_card, card, seen)
                for card in cards
            ]

            for future in as_completed(futures):
                pass

            page += 1

            # Small pause between page fetches
            time.sleep(0.3)

print("\nAll sets completed.")