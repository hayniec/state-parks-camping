#!/usr/bin/env python3
import csv
import urllib.request
import ssl

def check_alaska_urls():
    csv_file = "alaska_state_parks.csv"
    bad_urls = []
    
    # Create an unverified SSL context to bypass certificate issues if any
    ssl_context = ssl._create_unverified_context()
    
    print(f"Starting verification of Alaska State Park URLs from '{csv_file}'...\n")
    
    try:
        with open(csv_file, mode="r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row.get("park_name")
                url = row.get("park_url")
                if not url:
                    continue
                
                print(f"Checking: {name}...")
                try:
                    # Request with custom headers to prevent blocking
                    req = urllib.request.Request(
                        url,
                        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                    )
                    with urllib.request.urlopen(req, context=ssl_context, timeout=10) as response:
                        html = response.read().decode('utf-8', errors='ignore')
                        
                        # Detect specific 404 Page Not Found signature phrases
                        if "SORRY - PAGE NOT FOUND" in html or "not a natural disaster!" in html:
                            print(f"  [!] Renders 404 Page Not Found screen.")
                            bad_urls.append((name, url, "Renders 404 Error Screen"))
                        elif response.getcode() == 404:
                            print(f"  [!] Response status code: 404")
                            bad_urls.append((name, url, "HTTP 404 status"))
                        else:
                            print("  [OK]")
                except Exception as e:
                    print(f"  [!] Network / Request Error: {e}")
                    bad_urls.append((name, url, f"Error: {e}"))
    except FileNotFoundError:
        print(f"Error: Database file '{csv_file}' not found.")
        return

    # Report results
    if bad_urls:
        print("\n" + "="*50)
        print("!!! ALERT: THE FOLLOWING URLS RETURNED ERRORS/404s:")
        print("="*50)
        for name, url, reason in bad_urls:
            print(f"- {name}\n  URL: {url}\n  Reason: {reason}\n")
            
        # Write to log file
        log_file = "broken_alaska_links.log"
        with open(log_file, "w", encoding="utf-8") as log_f:
            log_f.write("Broken Alaska State Park URLs Log\n")
            log_f.write("=================================\n\n")
            for name, url, reason in bad_urls:
                log_f.write(f"Park: {name}\nURL: {url}\nReason: {reason}\n\n")
        print(f"Detailed list written to: {log_file}")
    else:
        print("\nAll Alaska State Park URLs are active and working correctly!")

if __name__ == "__main__":
    check_alaska_urls()
