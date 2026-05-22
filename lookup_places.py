#!/usr/bin/env python3
"""
Google Places Lookup Script for Alabama State Parks
===================================================
Queries the Google Places Text Search API to retrieve Google Place ID, overall
Google rating, review count, and link to Google Maps for each state park.

Requirements:
    - GOOGLE_MAPS_API_KEY environment variable must be set.
    - pip install requests

Usage:
    python lookup_places.py [--force]
"""

import argparse
import csv
import os
import shutil
import sys
import time
import urllib.parse
from typing import Any, Dict, Optional, Tuple

import requests

CSV_PATH = "alabama_state_parks.csv"
BACKUP_PATH = "alabama_state_parks.csv.bak"

API_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
DELAY_SECONDS = 0.1


def lookup_place(
    query: str, api_key: str
) -> Tuple[Optional[str], Optional[float], Optional[int]]:
    """Query Google Places Text Search API.

    Returns (place_id, rating, review_count).
    """
    params = {"query": query, "key": api_key}
    try:
        time.sleep(DELAY_SECONDS)
        resp = requests.get(API_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        status = data.get("status")
        if status == "OK" and data.get("results"):
            result = data["results"][0]
            place_id = result.get("place_id")
            rating = result.get("rating")
            review_count = result.get("user_ratings_total")
            return place_id, rating, review_count
        elif status == "ZERO_RESULTS":
            print(f"    [info] No places found for query: '{query}'")
        else:
            print(f"    [warn] API returned status '{status}' for query: '{query}'", file=sys.stderr)
            if "error_message" in data:
                print(f"    [warn] Message: {data['error_message']}", file=sys.stderr)
    except Exception as e:
        print(f"    [warn] Request error for query '{query}': {e}", file=sys.stderr)

    return None, None, None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Lookup Google Place details for state parks."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force lookup even if Google Place ID is already populated.",
    )
    args = parser.parse_args()

    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    
    # 1. Fallback to .env file if key not in environment
    if not api_key and os.path.exists(".env"):
        try:
            with open(".env", "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip() and not line.strip().startswith("#"):
                        parts = line.strip().split("=", 1)
                        if len(parts) == 2 and parts[0].strip() == "GOOGLE_MAPS_API_KEY":
                            api_key = parts[1].strip().strip('"').strip("'")
                            break
            if api_key:
                print("Loaded GOOGLE_MAPS_API_KEY from .env file.")
        except Exception as e:
            print(f"Warning: Could not read .env file: {e}", file=sys.stderr)

    # 2. Prompt user interactively if key still missing
    if not api_key:
        try:
            print("GOOGLE_MAPS_API_KEY environment variable or .env file not found.")
            user_input = input("Please paste your Google Maps API Key: ").strip()
            if user_input:
                api_key = user_input
            else:
                print("Error: No API key provided.", file=sys.stderr)
                return 1
        except (KeyboardInterrupt, EOFError):
            print("\nCancelled by user.", file=sys.stderr)
            return 1

    if not os.path.exists(CSV_PATH):
        print(f"Error: {CSV_PATH} not found. Please run the scraper first.", file=sys.stderr)
        return 1


    # Read CSV
    records = []
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            records.append(row)

    if not fieldnames:
        print("Error: CSV has no headers.", file=sys.stderr)
        return 1

    required_fields = [
        "google_place_id",
        "google_rating",
        "google_review_count",
        "google_maps_url",
    ]
    for field in required_fields:
        if field not in fieldnames:
            print(f"Error: CSV header is missing the '{field}' column. Please check your scraper schema.", file=sys.stderr)
            return 1

    updated_count = 0
    skipped_count = 0
    failed_count = 0

    print("Starting Google Places lookup...")

    for row in records:
        name = row.get("park_name", "")
        place_id = row.get("google_place_id", "")

        # Skip if already looked up and not forcing
        if not args.force and place_id:
            skipped_count += 1
            continue

        query = f"{name}, Alabama"
        print(f"Searching Places API for '{name}' (query: '{query}')...")

        res_id, rating, count = lookup_place(query, api_key)

        if res_id:
            row["google_place_id"] = res_id
            row["google_rating"] = str(rating) if rating is not None else ""
            row["google_review_count"] = (
                str(count) if count is not None else ""
            )

            # Construct official deep link
            # https://www.google.com/maps/search/?api=1&query=Park+Name&query_place_id=place_id
            encoded_name = urllib.parse.quote_plus(name)
            row["google_maps_url"] = (
                f"https://www.google.com/maps/search/?api=1"
                f"&query={encoded_name}&query_place_id={res_id}"
            )

            print(f"  -> Found! Place ID: {res_id}, Rating: {rating}, Reviews: {count}")
            updated_count += 1
        else:
            print(f"  -> [FAILED] Could not resolve place details for '{name}'")
            failed_count += 1

    if updated_count > 0:
        print(f"Backing up {CSV_PATH} to {BACKUP_PATH}...")
        shutil.copyfile(CSV_PATH, BACKUP_PATH)

        # Write updated CSV
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)

        print(f"Successfully updated {updated_count} records in {CSV_PATH}.")
    else:
        print("No records were updated.")

    print(f"Summary: {updated_count} updated, {skipped_count} skipped, {failed_count} failed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
