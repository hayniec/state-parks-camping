#!/usr/bin/env python3
import csv
import os
import urllib.request
import urllib.error
import ssl
import shutil
from collections import defaultdict

def check_all_urls():
    csv_file = "all_state_parks.csv"
    reports_dir = "broken_link_reports"
    
    # Create or clean the reports directory
    if os.path.exists(reports_dir):
        shutil.rmtree(reports_dir)
    os.makedirs(reports_dir)
    
    # Map state -> list of broken links
    broken_by_state = defaultdict(list)
    ssl_context = ssl._create_unverified_context()
    
    print(f"Reading parks from '{csv_file}'...")
    try:
        with open(csv_file, mode="r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            parks = list(reader)
    except FileNotFoundError:
        print(f"Error: Master file '{csv_file}' not found.")
        return

    print(f"Starting verification of {len(parks)} park URLs across all states...\n")
    
    for idx, park in enumerate(parks, 1):
        name = park.get("park_name")
        state = park.get("state", "UNKNOWN")
        url = park.get("park_url")
        
        if not url:
            continue
            
        print(f"[{idx}/{len(parks)}] Checking ({state}): {name}...")
        try:
            req = urllib.request.Request(
                url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                }
            )
            with urllib.request.urlopen(req, context=ssl_context, timeout=8) as response:
                html = response.read().decode('utf-8', errors='ignore')
                
                # Check for known 404 page signatures
                is_bad = False
                reason = ""
                
                # Alaska 404
                if "SORRY - PAGE NOT FOUND" in html or "not a natural disaster!" in html:
                    is_bad = True
                    reason = "Renders 404 Error Screen"
                # General HTTP status
                elif response.getcode() == 404:
                    is_bad = True
                    reason = "HTTP 404 status"
                    
                if is_bad:
                    print(f"  [!] BROKEN: {reason}")
                    broken_by_state[state].append({
                        "name": name,
                        "url": url,
                        "reason": reason
                    })
                else:
                    print("  [OK]")
        except urllib.error.HTTPError as e:
            if e.code == 403:
                print(f"  [!] SKIP: HTTP 403 Forbidden (likely bot blocking)")
            else:
                print(f"  [!] HTTP ERROR {e.code}: {e}")
                broken_by_state[state].append({
                    "name": name,
                    "url": url,
                    "reason": f"HTTP Error {e.code}: {e}"
                })
        except urllib.error.URLError as e:
            print(f"  [!] URL ERROR: {e.reason}")
            broken_by_state[state].append({
                "name": name,
                "url": url,
                "reason": f"URL Error: {e.reason}"
            })
        except Exception as e:
            print(f"  [!] ERROR: {e}")
            broken_by_state[state].append({
                "name": name,
                "url": url,
                "reason": f"Connection Error: {e}"
            })

    # Generate Reports grouped and alphabetized by state
    sorted_states = sorted(broken_by_state.keys())
    
    if sorted_states:
        print("\n" + "="*50)
        print("!!! ALERT: FOUND BROKEN LINKS IN THE FOLLOWING STATES:")
        print("="*50)
        
        # Write individual state files
        for state in sorted_states:
            state_file = os.path.join(reports_dir, f"{state}_broken_links.log")
            print(f"- {state} ({len(broken_by_state[state])} broken links) -> written to {state_file}")
            
            with open(state_file, "w", encoding="utf-8") as sf:
                sf.write(f"Broken Links Report for State: {state}\n")
                sf.write("=" * 40 + "\n\n")
                for item in broken_by_state[state]:
                    sf.write(f"Park: {item['name']}\n")
                    sf.write(f"URL: {item['url']}\n")
                    sf.write(f"Reason: {item['reason']}\n\n")
                    
        # Write a master summary file
        summary_file = os.path.join(reports_dir, "summary.log")
        with open(summary_file, "w", encoding="utf-8") as sum_f:
            sum_f.write("Master Broken Links Summary (Alphabetized by State)\n")
            sum_f.write("=" * 55 + "\n\n")
            for state in sorted_states:
                sum_f.write(f"=== STATE: {state} ({len(broken_by_state[state])} Broken) ===\n")
                for item in broken_by_state[state]:
                    sum_f.write(f"- {item['name']}\n  URL: {item['url']}\n  Reason: {item['reason']}\n\n")
                    
        print(f"\nAll reports saved in directory: {reports_dir}/")
        print(f"Master summary file: {summary_file}")
    else:
        print("\nAll state park URLs across all states are active and working correctly!")

if __name__ == "__main__":
    check_all_urls()
