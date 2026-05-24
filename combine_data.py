#!/usr/bin/env python3
"""
Campground Discovery Project - Dataset Merger
=============================================
Combines individual state CSV files (e.g., `alabama_state_parks.csv`)
into a single consolidated `all_state_parks.csv` dataset.
"""

import csv
import glob
import os
import sys

OUTPUT_FILE = "all_state_parks.csv"
FILE_PATTERN = "*_state_parks.csv"

def main():
    # Find all matching CSV files in the current directory
    csv_files = glob.glob(FILE_PATTERN)
    
    # Filter out the output file itself if it exists
    csv_files = [f for f in csv_files if os.path.basename(f) != OUTPUT_FILE]
    
    if not csv_files:
        print(f"Error: No state CSV files found matching pattern '{FILE_PATTERN}' in current directory.", file=sys.stderr)
        return 1
        
    print(f"Found {len(csv_files)} state dataset files to merge:")
    for f in sorted(csv_files):
        print(f"  - {f}")
        
    # Read headers and verify consistency
    common_headers = None
    all_rows = []
    
    for file_path in sorted(csv_files):
        with open(file_path, mode="r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            try:
                headers = next(reader)
            except StopIteration:
                print(f"Warning: {file_path} is empty. Skipping.", file=sys.stderr)
                continue
                
            if common_headers is None:
                common_headers = headers
            elif headers != common_headers:
                print(f"Error: Schema mismatch in '{file_path}'.", file=sys.stderr)
                print(f"Expected: {common_headers[:5]}...", file=sys.stderr)
                print(f"Found:    {headers[:5]}...", file=sys.stderr)
                return 1
                
            # Read the rest of the rows
            file_rows = list(reader)
            all_rows.extend(file_rows)
            print(f"    Loaded {len(file_rows)} rows from {os.path.basename(file_path)}")

    if not all_rows or not common_headers:
        print("Error: No data rows found to combine.", file=sys.stderr)
        return 1

    # Write merged results
    with open(OUTPUT_FILE, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(common_headers)
        writer.writerows(all_rows)
        
    print(f"\nSuccessfully combined {len(all_rows)} total parks into '{OUTPUT_FILE}'.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
