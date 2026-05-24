#!/usr/bin/env python3
"""
Geocoding Script for Alabama State Parks
=========================================
Resolves park addresses in `alabama_state_parks.csv` to latitude and longitude
coordinates using either Nominatim (OpenStreetMap) or Google Geocoding API.

Usage:
    python geocode_parks.py [--force] [--service {osm,google}]

Options:
    --force             Re-geocode rows that already have coordinates.
    --service           Force a specific service (defaults to 'google' if
                        GOOGLE_MAPS_API_KEY env var is set, else 'osm').
"""

import argparse
import csv
import os
import shutil
import sys
import time
from typing import Optional, Tuple

import requests

CSV_PATH = "alabama_state_parks.csv"
BACKUP_PATH = "alabama_state_parks.csv.bak"

USER_AGENT = "AL-State-Parks-Geocoder/0.1 (campground discovery project)"

# Enforced rate limits
OSM_DELAY_SECONDS = 1.0
GOOGLE_DELAY_SECONDS = 0.1


def geocode_osm(address: str, park_name: str, state_name: str) -> Tuple[Optional[float], Optional[float]]:
    """Geocode using OpenStreetMap's Nominatim API."""
    url = "https://nominatim.openstreetmap.org/search"
    headers = {"User-Agent": USER_AGENT}

    # Attempt 1: Full Address
    params = {"q": address, "format": "json", "limit": 1}
    try:
        time.sleep(OSM_DELAY_SECONDS)
        response = requests.get(url, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as e:
        print(f"    [warn] OSM geocoding error for '{address}': {e}", file=sys.stderr)

    # Attempt 2: Park Name + State
    query_fallback = f"{park_name}, {state_name}"
    params = {"q": query_fallback, "format": "json", "limit": 1}
    try:
        time.sleep(OSM_DELAY_SECONDS)
        response = requests.get(url, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        if data:
            print(f"    [info] Resolved using fallback query: '{query_fallback}'")
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as e:
        print(f"    [warn] OSM fallback query error: {e}", file=sys.stderr)

    return None, None


def geocode_google(address: str, park_name: str, state_name: str, api_key: str) -> Tuple[Optional[float], Optional[float]]:
    """Geocode using Google Geocoding API."""
    url = "https://maps.googleapis.com/maps/api/geocode/json"

    # Attempt 1: Full Address
    params = {"address": address, "key": api_key}
    try:
        time.sleep(GOOGLE_DELAY_SECONDS)
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        if data.get("status") == "OK" and data.get("results"):
            loc = data["results"][0]["geometry"]["location"]
            return float(loc["lat"]), float(loc["lng"])
    except Exception as e:
        print(f"    [warn] Google geocoding error for '{address}': {e}", file=sys.stderr)

    # Attempt 2: Park Name + State
    query_fallback = f"{park_name}, {state_name}"
    params = {"address": query_fallback, "key": api_key}
    try:
        time.sleep(GOOGLE_DELAY_SECONDS)
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        if data.get("status") == "OK" and data.get("results"):
            loc = data["results"][0]["geometry"]["location"]
            print(f"    [info] Resolved using fallback query: '{query_fallback}'")
            return float(loc["lat"]), float(loc["lng"])
    except Exception as e:
        print(f"    [warn] Google fallback query error: {e}", file=sys.stderr)

    return None, None


def main() -> int:
    parser = argparse.ArgumentParser(description="Geocode park addresses in CSV.")
    parser.add_argument(
        "--csv",
        default="alabama_state_parks.csv",
        help="Path to the CSV file to geocode (defaults to alabama_state_parks.csv).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-geocode even if coordinates already exist.",
    )
    parser.add_argument(
        "--service",
        choices=["osm", "google"],
        help="Force geocoding service. If not specified, defaults to Google if key is present, else OSM.",
    )
    args = parser.parse_args()

    csv_path = args.csv
    backup_path = csv_path + ".bak"

    # Determine service and API key
    google_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not google_key and os.path.exists(".env"):
        try:
            with open(".env", "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip() and not line.strip().startswith("#"):
                        parts = line.strip().split("=", 1)
                        if len(parts) == 2 and parts[0].strip() == "GOOGLE_MAPS_API_KEY":
                            google_key = parts[1].strip().strip('"').strip("'")
                            break
            if google_key:
                print("Loaded GOOGLE_MAPS_API_KEY from .env file.")
        except Exception as e:
            print(f"Warning: Could not read .env file: {e}", file=sys.stderr)
            
    service = args.service

    if not service:
        if google_key:
            service = "google"
        else:
            service = "osm"

    if service == "google" and not google_key:
        print("Error: Google Geocoding selected but GOOGLE_MAPS_API_KEY environment variable is not set.", file=sys.stderr)
        return 1

    print(f"Using geocoding service: {service.upper()}")

    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.", file=sys.stderr)
        return 1

    # Read records
    records = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            records.append(row)

    if not fieldnames:
        print("Error: CSV has no headers.", file=sys.stderr)
        return 1

    # Ensure latitude and longitude columns exist in header
    for field in ["latitude", "longitude"]:
        if field not in fieldnames:
            print(f"Error: CSV header is missing the '{field}' column.", file=sys.stderr)
            return 1

    states = {
        "AL": "Alabama",
        "AK": "Alaska",
        "AZ": "Arizona",
        "AR": "Arkansas",
        "CA": "California",
        "CO": "Colorado",
        "CT": "Connecticut"
    }

    # Geocode each park
    updated_count = 0
    skipped_count = 0
    failed_count = 0

    for row in records:
        name = row.get("park_name", "")
        address = row.get("address", "")
        lat_str = row.get("latitude", "")
        lon_str = row.get("longitude", "")
        state_abbr = row.get("state", "AL")
        state_name = states.get(state_abbr, "Alabama")

        # Skip if already geocoded (and not forcing)
        if not args.force and lat_str and lon_str:
            skipped_count += 1
            continue

        if not address:
            print(f"Skipping '{name}': Address field is empty.")
            failed_count += 1
            continue

        print(f"Geocoding '{name}' -> Address: '{address}'")

        if service == "google" and google_key:
            lat, lon = geocode_google(address, name, state_name, google_key)
        else:
            lat, lon = geocode_osm(address, name, state_name)

        if lat is not None and lon is not None:
            row["latitude"] = str(lat)
            row["longitude"] = str(lon)
            print(f"  -> Success: {lat}, {lon}")
            updated_count += 1
        else:
            print(f"  -> [FAILED] Could not geocode '{name}'")
            failed_count += 1

    if updated_count > 0:
        # Create a backup of the original CSV file
        print(f"Backing up {csv_path} to {backup_path}...")
        shutil.copyfile(csv_path, backup_path)

        # Write updated CSV
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)

        print(f"Successfully updated {updated_count} records in {csv_path}.")
    else:
        print("No records were updated.")

    print(f"Summary: {updated_count} updated, {skipped_count} skipped, {failed_count} failed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
