#!/usr/bin/env python3
"""
Alabama State Parks Scraper
============================
Scrapes the Alabama State Parks website (alapark.com) for state parks
with a focus on those offering RV camping. Outputs a CSV file with
amenity data and a schema ready for downstream rating integration.

Usage:
    python3 scrape_alabama_parks.py

Output:
    alabama_state_parks.csv  -- one row per park

Requirements:
    pip install requests beautifulsoup4

Notes:
    - Respects the site with a 2-second delay between requests.
    - Uses an identifying User-Agent string.
    - Saves raw page text alongside extracted fields so you can
      hand-fill structured fields and ratings later.
"""

import csv
import re
import sys
import time
from dataclasses import dataclass, field, asdict
from typing import Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://www.alapark.com"
PARKS_INDEX = f"{BASE_URL}/parks"
OUTPUT_CSV = "alabama_state_parks.csv"

# Polite request settings
USER_AGENT = (
    "AL-State-Parks-Research-Bot/0.1 "
    "(personal RV campground discovery project; "
    "contact: your-email@example.com)"
)
REQUEST_DELAY_SECONDS = 2.0
REQUEST_TIMEOUT = 30

# Keywords that signal RV-relevant content on a park page.

RV_KEYWORDS = [
    "rv", "full hookup", "full-hookup", "full hook-up",
    "improved campsite", "improved sites", "improved campground",
    "pull-thru", "pull through", "pull-through",
    "back-in", "campground", "hookups",
]


# ---------------------------------------------------------------------------
# Data schema
# ---------------------------------------------------------------------------
@dataclass
class ParkRecord:
    # Identity
    park_name: str = ""
    park_slug: str = ""
    state: str = "AL"
    park_url: str = ""

    # Location
    address: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # Contact
    phone_general: str = ""
    phone_camping: str = ""
    phone_other: str = ""

    # RV / Camping
    has_rv_camping: Optional[bool] = None
    rv_sites_count: Optional[int] = None
    has_tent_camping: Optional[bool] = None
    tent_sites_count: Optional[int] = None
    primitive_camping: Optional[bool] = None
    max_rig_length_ft: Optional[int] = None
    pull_through_available: Optional[bool] = None
    electric_30amp: Optional[bool] = None
    electric_50amp: Optional[bool] = None
    water_hookup: Optional[bool] = None
    sewer_hookup: Optional[bool] = None
    dump_station: Optional[bool] = None
    full_hookups: Optional[bool] = None

    # Amenities
    showers: Optional[bool] = None
    laundry: Optional[bool] = None
    wifi: Optional[bool] = None
    cell_signal_notes: str = ""
    pet_friendly: Optional[bool] = None
    ada_sites: Optional[bool] = None
    waterfront_sites: Optional[bool] = None

    # Features
    lake_river_access: Optional[bool] = None
    hiking: Optional[bool] = None
    fishing: Optional[bool] = None
    swimming: Optional[bool] = None
    boat_ramp: Optional[bool] = None
    golf: Optional[bool] = None

    # Operations
    open_year_round: Optional[bool] = None
    seasonal_notes: str = ""
    reservation_url: str = ""

    # Ratings (filled in later from Google Places API or manually)
    overall_rating: Optional[float] = None
    google_place_id: str = ""
    google_maps_url: str = ""
    google_rating: Optional[float] = None
    google_review_count: Optional[int] = None
    rating_site_quality: Optional[int] = None
    rating_hookup_reliability: Optional[int] = None
    rating_cleanliness: Optional[int] = None
    rating_scenery: Optional[int] = None
    rating_connectivity: Optional[int] = None
    rating_noise: Optional[int] = None
    rating_value: Optional[int] = None

    # Raw text fallback so nothing is lost
    description_text: str = ""
    campground_text: str = ""
    sub_page_urls: str = ""  # semicolon-separated
    scraped_at: str = ""


# ---------------------------------------------------------------------------
# Networking
# ---------------------------------------------------------------------------
def fetch(url: str, session: requests.Session) -> Optional[str]:
    """Fetch a URL with polite delay and timeout. Returns HTML or None."""
    try:
        time.sleep(REQUEST_DELAY_SECONDS)
        resp = session.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as e:
        print(f"  [warn] failed to fetch {url}: {e}", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# Park list discovery
# ---------------------------------------------------------------------------
def get_park_list(session: requests.Session) -> list[tuple[str, str]]:
    """Return list of (park_name, park_url) tuples from the parks nav."""
    html = fetch(PARKS_INDEX, session)
    if not html:
        # Fall back to the hardcoded list we already know from the nav.
        print("  [info] using fallback hardcoded park list", file=sys.stderr)
        return HARDCODED_PARK_LIST

    soup = BeautifulSoup(html, "html.parser")
    parks: dict[str, str] = {}

    # Look for any /parks/{slug} link in the page body
    for a in soup.find_all("a", href=True):
        href = a["href"]
        m = re.fullmatch(r"(?:https?://www\.alapark\.com)?/parks/([a-z0-9\-]+)", href)
        if not m:
            continue
        slug = m.group(1)
        # Skip non-park pages
        if slug in {"map-of-parks", "sounds-alabama"}:
            continue
        name = a.get_text(strip=True)
        if not name:
            continue
        url = urljoin(BASE_URL, href)
        # Prefer the longer (more descriptive) name if we see the slug twice
        if slug not in parks or len(name) > len(parks[slug][0]):
            parks[slug] = (name, url)

    # Convert to list and sort by name
    result = sorted(parks.values(), key=lambda x: x[0].lower())
    if len(result) < 15:
        # Suspiciously short — fall back
        print(
            f"  [warn] only found {len(result)} parks from nav; "
            "using hardcoded list",
            file=sys.stderr,
        )
        return HARDCODED_PARK_LIST
    return result


# Hardcoded list from the site navigation as a fallback.
HARDCODED_PARK_LIST: list[tuple[str, str]] = [
    ("Bladon Springs State Park",        f"{BASE_URL}/parks/bladon-springs-state-park"),
    ("Blue Springs State Park",          f"{BASE_URL}/parks/blue-springs-state-park"),
    ("Bucks Pocket State Park",          f"{BASE_URL}/parks/bucks-pocket-state-park"),
    ("Cathedral Caverns State Park",     f"{BASE_URL}/parks/cathedral-caverns-state-park"),
    ("Cheaha State Park",                f"{BASE_URL}/parks/cheaha-state-park"),
    ("Chewacla State Park",              f"{BASE_URL}/parks/chewacla-state-park"),
    ("Chickasaw State Park",             f"{BASE_URL}/parks/chickasaw-state-park"),
    ("DeSoto State Park",                f"{BASE_URL}/parks/desoto-state-park"),
    ("Frank Jackson State Park",         f"{BASE_URL}/parks/frank-jackson-state-park"),
    ("Gulf State Park",                  f"{BASE_URL}/parks/gulf-state-park"),
    ("Joe Wheeler State Park",           f"{BASE_URL}/parks/joe-wheeler-state-park"),
    ("Lake Guntersville State Park",     f"{BASE_URL}/parks/lake-guntersville-state-park"),
    ("Lake Jackson RV Park at Florala",  f"{BASE_URL}/parks/lake-jackson-rv-park-at-florala"),
    ("Lake Lurleen State Park",          f"{BASE_URL}/parks/lake-lurleen-state-park"),
    ("Lakepoint State Park",             f"{BASE_URL}/parks/lakepoint-state-park"),
    ("Meaher State Park",                f"{BASE_URL}/parks/meaher-state-park"),
    ("Monte Sano State Park",            f"{BASE_URL}/parks/monte-sano-state-park"),
    ("Oak Mountain State Park",          f"{BASE_URL}/parks/oak-mountain-state-park"),
    ("Paul Grist State Park",            f"{BASE_URL}/parks/paul-grist-state-park"),
    ("Rickwood Caverns State Park",      f"{BASE_URL}/parks/rickwood-caverns-state-park"),
    ("Roland Cooper State Park",         f"{BASE_URL}/parks/roland-cooper-state-park"),
    ("Wind Creek State Park",            f"{BASE_URL}/parks/wind-creek-state-park"),
]


# ---------------------------------------------------------------------------
# Per-park extraction
# ---------------------------------------------------------------------------
def get_main_content(soup: BeautifulSoup) -> BeautifulSoup:
    """Try to isolate the main content region; fall back to the whole soup."""
    main = soup.find("main")
    if main:
        return main
    main = soup.find(id="main-content")
    if main:
        if main.name == "a" and not main.get_text(strip=True):
            parent = main.parent
            if parent:
                return parent
        return main
    return soup


def extract_address(soup: BeautifulSoup) -> str:
    """Find the address link (the maps.google.com link near 'Location')."""
    for a in soup.find_all("a", href=True):
        if "maps.google.com" in a["href"]:
            text = a.get_text(strip=True)
            if text:
                return text
    return ""


def extract_phones(soup: BeautifulSoup) -> dict[str, str]:
    """Extract phone numbers; classify them by surrounding label text."""
    phones = {"general": "", "camping": "", "other": []}
    for a in soup.find_all("a", href=True):
        if not a["href"].startswith("tel:"):
            continue
        label = a.get_text(strip=True)
        lower = label.lower()
        if "camping" in lower:
            phones["camping"] = label
        elif "general" in lower or "park info" in lower:
            phones["general"] = label
        else:
            phones["other"].append(label)
    phones["other_str"] = "; ".join(phones["other"])
    return phones


def find_sub_pages(soup: BeautifulSoup, slug: str) -> list[tuple[str, str]]:
    """Find /parks/{slug}/... sub-page links (RV campground, etc.)."""
    subs: dict[str, str] = {}
    pattern = re.compile(rf"/parks/{re.escape(slug)}/([a-z0-9\-]+)/?$")
    for a in soup.find_all("a", href=True):
        m = pattern.search(a["href"])
        if not m:
            continue
        text = a.get_text(strip=True)
        if not text:
            continue
        url = urljoin(BASE_URL, a["href"])
        subs[url] = text
    return list(subs.items())


def find_campground_subpage(sub_pages: list[tuple[str, str]]) -> Optional[str]:
    """Pick the most RV-relevant sub-page URL, if any."""
    priorities = [
        "rv-and-primitive-campground",
        "rv-resort",
        "campground",
        "camping",
    ]
    for keyword in priorities:
        for url, _label in sub_pages:
            if keyword in url:
                return url
    return None


def get_clean_text(soup: BeautifulSoup) -> str:
    """Return cleaned visible text from the main content region."""
    main = get_main_content(soup)
    # Strip nav and footer noise
    for tag in main.find_all(["nav", "header", "footer", "script", "style"]):
        tag.decompose()
    text = main.get_text(separator=" ", strip=True)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text)
    return text


# ---------------------------------------------------------------------------
# Light-touch keyword inference (best-effort; user verifies)
# ---------------------------------------------------------------------------
def infer_amenities(text: str, record: ParkRecord) -> None:
    """Best-effort keyword detection. Leaves None when uncertain."""
    t = text.lower()

    # RV camping presence
    if any(kw in t for kw in RV_KEYWORDS):
        record.has_rv_camping = True

    # Tent camping presence
    tent_keywords = ["primitive", "tent-only", "tent sites", "walk-in", "tent camping", "tents"]
    if any(kw in t for kw in tent_keywords):
        record.has_tent_camping = True

    if "primitive" in t:
        record.primitive_camping = True

    # RV site count - look for patterns like "192 improved sites" or "50 rv sites"
    # Avoid matching tent/primitive sites by excluding those terms nearby
    rv_site_match = re.search(
        r"\b(\d{1,3})[\s\-]+(?:improved|rv|full[\s\-]hook|campsite|site(?![\s\-]+(?:tent|primitive|walk\-in)))",
        t,
    )
    if rv_site_match:
        try:
            record.rv_sites_count = int(rv_site_match.group(1))
        except ValueError:
            pass

    # Tent site count - look for patterns like "10 tent sites" or "24 primitive sites"
    tent_site_match = re.search(
        r"\b(\d{1,3})[\s\-]+(?:tent|primitive|walk\-in)[\s\-]*(?:site|camp|campsite)?",
        t,
    )
    if tent_site_match:
        try:
            record.tent_sites_count = int(tent_site_match.group(1))
        except ValueError:
            pass

    # Hookups
    if "full hookup" in t or "full-hookup" in t or "full hook-up" in t:
        record.full_hookups = True
        record.electric_30amp = True  # assume; user can correct
        record.water_hookup = True
        record.sewer_hookup = True
    if "50 amp" in t or "50-amp" in t:
        record.electric_50amp = True
    if "30 amp" in t or "30-amp" in t:
        record.electric_30amp = True
    if "dump station" in t:
        record.dump_station = True

    # Pull-through
    if "pull-thru" in t or "pull-through" in t or "pull through" in t:
        record.pull_through_available = True

    # Bathhouse / showers / laundry
    if "bathhouse" in t or "shower" in t:
        record.showers = True
    if "laundry" in t:
        record.laundry = True
    if "wi-fi" in t or "wifi" in t or "wireless internet" in t:
        record.wifi = True

    # Accessibility
    if "ada-accessible" in t or "ada accessible" in t or "ada site" in t:
        record.ada_sites = True

    # Waterfront / lake / river
    if "waterfront" in t:
        record.waterfront_sites = True
    if any(w in t for w in ["lake ", "river ", "gulf ", "shoreline", "shores of"]):
        record.lake_river_access = True

    # Activities
    if "hiking" in t or "trails" in t:
        record.hiking = True
    if "fishing" in t:
        record.fishing = True
    if "swimming" in t or "swim " in t or "swim." in t:
        record.swimming = True
    if "boat ramp" in t or "marina" in t:
        record.boat_ramp = True
    if "golf" in t:
        record.golf = True
    if "pet" in t and ("welcome" in t or "allow" in t or "friendly" in t or "leash" in t):
        record.pet_friendly = True


# ---------------------------------------------------------------------------
# Main per-park flow
# ---------------------------------------------------------------------------
def scrape_park(
    name: str, url: str, session: requests.Session
) -> ParkRecord:
    print(f"Scraping: {name}")
    record = ParkRecord(park_name=name, park_url=url)
    slug = url.rstrip("/").rsplit("/", 1)[-1]
    record.park_slug = slug
    record.scraped_at = time.strftime("%Y-%m-%d %H:%M:%S")

    html = fetch(url, session)
    if not html:
        return record

    soup = BeautifulSoup(html, "html.parser")
    main = get_main_content(soup)

    record.address = extract_address(main)
    phones = extract_phones(main)
    record.phone_general = phones["general"]
    record.phone_camping = phones["camping"]
    record.phone_other = phones["other_str"]

    description_text = get_clean_text(soup)
    record.description_text = description_text

    sub_pages = find_sub_pages(main, slug)
    record.sub_page_urls = "; ".join(
        f"{label} -> {url}" for url, label in sub_pages
    )

    # Reservation URL (subdomain reserve.alapark.com)
    for a in main.find_all("a", href=True):
        if "reserve.alapark.com" in a["href"]:
            record.reservation_url = a["href"]
            break

    # Fetch the dedicated campground page if one exists
    cg_url = find_campground_subpage(sub_pages)
    if cg_url:
        cg_html = fetch(cg_url, session)
        if cg_html:
            cg_soup = BeautifulSoup(cg_html, "html.parser")
            record.campground_text = get_clean_text(cg_soup)

    # Combined text gives us the best chance to infer amenities
    combined = description_text + " " + record.campground_text
    infer_amenities(combined, record)

    return record


# ---------------------------------------------------------------------------
# CSV writing
# ---------------------------------------------------------------------------
def write_csv(records: list[ParkRecord], path: str) -> None:
    if not records:
        print("No records to write.", file=sys.stderr)
        return
    fieldnames = list(asdict(records[0]).keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in records:
            writer.writerow(asdict(r))
    print(f"\nWrote {len(records)} records to {path}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> int:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    print("Fetching park list...")
    parks = get_park_list(session)
    print(f"Found {len(parks)} parks.\n")

    records: list[ParkRecord] = []
    for name, url in parks:
        try:
            records.append(scrape_park(name, url, session))
        except Exception as e:
            print(f"  [error] {name}: {e}", file=sys.stderr)
            records.append(ParkRecord(park_name=name, park_url=url))

    write_csv(records, OUTPUT_CSV)
    rv_count = sum(1 for r in records if r.has_rv_camping)
    print(f"  -> {rv_count} parks flagged as having RV camping")
    return 0


if __name__ == "__main__":
    sys.exit(main())
