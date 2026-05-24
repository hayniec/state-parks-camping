#!/usr/bin/env python3
"""
Campground Discovery Project - State Dataset Generator
======================================================
Creates initial CSV and Markdown templates for CA, CO, and CT state parks.
"""

import csv
import os
import re

HEADERS = [
    "park_name", "park_slug", "state", "park_url", "address", "latitude", "longitude",
    "phone_general", "phone_camping", "phone_other", "has_rv_camping", "rv_sites_count",
    "has_tent_camping", "tent_sites_count", "primitive_camping", "max_rig_length_ft",
    "pull_through_available", "electric_30amp", "electric_50amp", "water_hookup",
    "sewer_hookup", "dump_station", "full_hookups", "showers", "laundry", "wifi",
    "cell_signal_notes", "pet_friendly", "ada_sites", "waterfront_sites", "lake_river_access",
    "hiking", "fishing", "swimming", "boat_ramp", "golf", "open_year_round", "seasonal_notes",
    "reservation_url", "ada_restrooms", "ada_trails", "ada_water_access", "overall_rating",
    "google_place_id", "google_maps_url", "google_rating", "google_review_count",
    "rating_site_quality", "rating_hookup_reliability", "rating_cleanliness", "rating_scenery",
    "rating_connectivity", "rating_noise", "rating_value", "description_text", "campground_text",
    "sub_page_urls", "scraped_at"
]

DATASETS = {
    "CA": {
        "name": "California",
        "url": "https://www.parks.ca.gov",
        "res_url": "https://www.reservecalifornia.com",
        "parks": [
            {
                "park_name": "Pfeiffer Big Sur State Park",
                "address": "47895 Highway 1, Big Sur, CA 93920",
                "has_rv_camping": "True", "rv_sites_count": "189",
                "has_tent_camping": "True", "tent_sites_count": "50", "primitive_camping": "False",
                "max_rig_length_ft": "32", "waterfront_sites": "True", "hiking": "True", "fishing": "True",
                "swimming": "True", "boat_ramp": "False", "golf": "False", "pet_friendly": "True", "wifi": "False",
                "description_text": "Pfeiffer Big Sur State Park features redwoods, hiking trails, and beautiful campsites along the scenic Big Sur River."
            },
            {
                "park_name": "Anza-Borrego Desert State Park",
                "address": "200 Palm Canyon Dr, Borrego Springs, CA 92004",
                "has_rv_camping": "True", "rv_sites_count": "120",
                "has_tent_camping": "True", "tent_sites_count": "50", "primitive_camping": "True",
                "max_rig_length_ft": "35", "waterfront_sites": "False", "hiking": "True", "fishing": "False",
                "swimming": "False", "boat_ramp": "False", "golf": "False", "pet_friendly": "True", "wifi": "False",
                "description_text": "California's largest state park offers dramatic desert canyons, spring wildflowers, palm oases, and expansive camping options under dark skies."
            },
            {
                "park_name": "Morro Bay State Park",
                "address": "60 State Park Rd, Morro Bay, CA 93442",
                "has_rv_camping": "True", "rv_sites_count": "130",
                "has_tent_camping": "True", "tent_sites_count": "30", "primitive_camping": "False",
                "max_rig_length_ft": "35", "waterfront_sites": "True", "hiking": "True", "fishing": "True",
                "swimming": "True", "boat_ramp": "True", "golf": "True", "pet_friendly": "True", "wifi": "False",
                "description_text": "Morro Bay State Park features lagoon views, sailing, hiking trails, a golf course, and a shaded campground popular with bird watchers."
            },
            {
                "park_name": "Humboldt Redwoods State Park",
                "address": "17119 Avenue of the Giants, Weott, CA 95571",
                "has_rv_camping": "True", "rv_sites_count": "150",
                "has_tent_camping": "True", "tent_sites_count": "50", "primitive_camping": "True",
                "max_rig_length_ft": "33", "waterfront_sites": "True", "hiking": "True", "fishing": "True",
                "swimming": "True", "boat_ramp": "False", "golf": "False", "pet_friendly": "True", "wifi": "False",
                "description_text": "Home to the massive Avenue of the Giants, this park offers camping deep within ancient redwood groves along the scenic Eel River."
            },
            {
                "park_name": "Crystal Cove State Park",
                "address": "8471 N Coast Hwy, Laguna Beach, CA 92651",
                "has_rv_camping": "True", "rv_sites_count": "28",
                "has_tent_camping": "True", "tent_sites_count": "30", "primitive_camping": "True",
                "max_rig_length_ft": "38", "waterfront_sites": "True", "hiking": "True", "fishing": "True",
                "swimming": "True", "boat_ramp": "False", "golf": "False", "pet_friendly": "True", "wifi": "False",
                "description_text": "Offers scenic bluff-top camping overlooking the Pacific Ocean, hiking trails through coastal canyons, and historic beachside cottages."
            },
            {
                "park_name": "San Elijo State Beach",
                "address": "2050 Coast Hwy 101, Cardiff, CA 92007",
                "has_rv_camping": "True", "rv_sites_count": "150",
                "has_tent_camping": "True", "tent_sites_count": "20", "primitive_camping": "False",
                "max_rig_length_ft": "35", "waterfront_sites": "True", "hiking": "False", "fishing": "True",
                "swimming": "True", "boat_ramp": "False", "golf": "False", "pet_friendly": "True", "wifi": "False",
                "description_text": "A very popular coastal campground on the cliffs of Cardiff-by-the-Sea, offering surf-side camping and a camp store."
            },
            {
                "park_name": "Calaveras Big Trees State Park",
                "address": "1170 CA-4, Arnold, CA 95223",
                "has_rv_camping": "True", "rv_sites_count": "120",
                "has_tent_camping": "True", "tent_sites_count": "30", "primitive_camping": "False",
                "max_rig_length_ft": "30", "waterfront_sites": "True", "hiking": "True", "fishing": "True",
                "swimming": "True", "boat_ramp": "False", "golf": "False", "pet_friendly": "True", "wifi": "False",
                "description_text": "Famous for preserving two groves of giant sequoias, the park offers wooded campgrounds along the Stanislaus River."
            },
            {
                "park_name": "Carpinteria State Beach",
                "address": "205 Palm Ave, Carpinteria, CA 93013",
                "has_rv_camping": "True", "rv_sites_count": "200",
                "has_tent_camping": "True", "tent_sites_count": "30", "primitive_camping": "False",
                "max_rig_length_ft": "35", "waterfront_sites": "True", "hiking": "False", "fishing": "True",
                "swimming": "True", "boat_ramp": "False", "golf": "False", "pet_friendly": "True", "wifi": "False",
                "description_text": "Located right on the sandy shore, this beach park offers extensive camping, tidepools, and a relaxing coastal atmosphere."
            },
            {
                "park_name": "D.L. Bliss State Park",
                "address": "9881 CA-89, Tahoma, CA 96142",
                "has_rv_camping": "True", "rv_sites_count": "140",
                "has_tent_camping": "True", "tent_sites_count": "30", "primitive_camping": "False",
                "max_rig_length_ft": "15", "waterfront_sites": "True", "hiking": "True", "fishing": "True",
                "swimming": "True", "boat_ramp": "False", "golf": "False", "pet_friendly": "True", "wifi": "False",
                "description_text": "Located on the shores of Lake Tahoe, D.L. Bliss features clear blue water, sandy beaches, hiking trails, and granite cliffs."
            },
            {
                "park_name": "McArthur-Burney Falls Memorial State Park",
                "address": "24898 CA-89, Burney, CA 96013",
                "has_rv_camping": "True", "rv_sites_count": "100",
                "has_tent_camping": "True", "tent_sites_count": "20", "primitive_camping": "False",
                "max_rig_length_ft": "32", "waterfront_sites": "True", "hiking": "True", "fishing": "True",
                "swimming": "True", "boat_ramp": "True", "golf": "False", "pet_friendly": "True", "wifi": "False",
                "description_text": "Famous for the spectacular 129-foot Burney Falls, this park offers a lush pine forest campground near Lake Britton."
            }
        ]
    },
    "CO": {
        "name": "Colorado",
        "url": "https://cpw.state.co.us",
        "res_url": "https://cpwshop.com",
        "parks": [
            {
                "park_name": "Boyd Lake State Park",
                "address": "3720 N County Rd 11C, Loveland, CO 80538",
                "has_rv_camping": "True", "rv_sites_count": "148",
                "has_tent_camping": "True", "tent_sites_count": "20", "primitive_camping": "False",
                "max_rig_length_ft": "40", "waterfront_sites": "True", "hiking": "True", "fishing": "True",
                "swimming": "True", "boat_ramp": "True", "golf": "False", "pet_friendly": "True", "wifi": "False",
                "description_text": "Boyd Lake offers water sports, sailing, fishing, a swim beach, and modern pull-through RV campsites at the foot of the Rocky Mountains."
            },
            {
                "park_name": "Chatfield State Park",
                "address": "11500 N Roxborough Park Rd, Littleton, CO 80125",
                "has_rv_camping": "True", "rv_sites_count": "197",
                "has_tent_camping": "True", "tent_sites_count": "40", "primitive_camping": "False",
                "max_rig_length_ft": "40", "waterfront_sites": "True", "hiking": "True", "fishing": "True",
                "swimming": "True", "boat_ramp": "True", "golf": "False", "pet_friendly": "True", "wifi": "False",
                "description_text": "Nestled along the foothills near Denver, Chatfield features a massive reservoir for boating, a dog off-leash area, and full-hookup campsites."
            },
            {
                "park_name": "Cherry Creek State Park",
                "address": "4201 S Parker Rd, Aurora, CO 80014",
                "has_rv_camping": "True", "rv_sites_count": "135",
                "has_tent_camping": "True", "tent_sites_count": "30", "primitive_camping": "False",
                "max_rig_length_ft": "40", "waterfront_sites": "True", "hiking": "True", "fishing": "True",
                "swimming": "True", "boat_ramp": "True", "golf": "False", "pet_friendly": "True", "wifi": "False",
                "description_text": "Anchored around an 880-acre reservoir, this suburban state park offers diverse trails, water sports, and a wooded campground with full hookups."
            },
            {
                "park_name": "Cheyenne Mountain State Park",
                "address": "410 JL Ranch Heights Rd, Colorado Springs, CO 80926",
                "has_rv_camping": "True", "rv_sites_count": "51",
                "has_tent_camping": "True", "tent_sites_count": "10", "primitive_camping": "False",
                "max_rig_length_ft": "40", "waterfront_sites": "False", "hiking": "True", "fishing": "False",
                "swimming": "False", "boat_ramp": "False", "golf": "False", "pet_friendly": "True", "wifi": "False",
                "description_text": "Situated at the base of Cheyenne Mountain, this park features pristine prairie-to-peak hiking trails and modern full-hookup sites."
            },
            {
                "park_name": "Eleven Mile State Park",
                "address": "4224 County Road 92, Lake George, CO 80827",
                "has_rv_camping": "True", "rv_sites_count": "290",
                "has_tent_camping": "True", "tent_sites_count": "50", "primitive_camping": "True",
                "max_rig_length_ft": "35", "waterfront_sites": "True", "hiking": "True", "fishing": "True",
                "swimming": "False", "boat_ramp": "True", "golf": "False", "pet_friendly": "True", "wifi": "False",
                "description_text": "Renowned for its large reservoir, Eleven Mile is popular for trout and northern pike fishing, offering shoreline and backcountry campsites."
            },
            {
                "park_name": "Golden Gate Canyon State Park",
                "address": "92 Golden Gate Canyon Rd, Golden, CO 80403",
                "has_rv_camping": "True", "rv_sites_count": "130",
                "has_tent_camping": "True", "tent_sites_count": "40", "primitive_camping": "True",
                "max_rig_length_ft": "35", "waterfront_sites": "False", "hiking": "True", "fishing": "True",
                "swimming": "False", "boat_ramp": "False", "golf": "False", "pet_friendly": "True", "wifi": "False",
                "description_text": "Located just 30 miles from Denver, Golden Gate features dense pine forests, rocky peaks, over 35 miles of hiking trails, and two campgrounds."
            },
            {
                "park_name": "Jackson Lake State Park",
                "address": "26262 Highway 144, Orchard, CO 80649",
                "has_rv_camping": "True", "rv_sites_count": "260",
                "has_tent_camping": "True", "tent_sites_count": "30", "primitive_camping": "False",
                "max_rig_length_ft": "40", "waterfront_sites": "True", "hiking": "True", "fishing": "True",
                "swimming": "True", "boat_ramp": "True", "golf": "False", "pet_friendly": "True", "wifi": "False",
                "description_text": "Often called the 'oasis in the plains,' Jackson Lake is a premier destination for boating, jet skiing, swimming, and stargazing."
            },
            {
                "park_name": "Lake Pueblo State Park",
                "address": "640 Pueblo Reservoir Rd, Pueblo, CO 81005",
                "has_rv_camping": "True", "rv_sites_count": "400",
                "has_tent_camping": "True", "tent_sites_count": "50", "primitive_camping": "False",
                "max_rig_length_ft": "45", "waterfront_sites": "True", "hiking": "True", "fishing": "True",
                "swimming": "True", "boat_ramp": "True", "golf": "False", "pet_friendly": "True", "wifi": "False",
                "description_text": "Boasting over 4,600 surface acres of water, this park features canyon walls, marinas, swim beaches, and extensive camping opportunities."
            },
            {
                "park_name": "Mueller State Park",
                "address": "21045 Highway 67, Divide, CO 80814",
                "has_rv_camping": "True", "rv_sites_count": "132",
                "has_tent_camping": "True", "tent_sites_count": "20", "primitive_camping": "True",
                "max_rig_length_ft": "40", "waterfront_sites": "False", "hiking": "True", "fishing": "True",
                "swimming": "False", "boat_ramp": "False", "golf": "False", "pet_friendly": "True", "wifi": "False",
                "description_text": "Located near Pikes Peak, Mueller features 5,000 acres of spring meadows, granite ridges, pine forests, and excellent wildlife viewing."
            },
            {
                "park_name": "Ridgway State Park",
                "address": "28555 Highway 550, Ridgway, CO 81432",
                "has_rv_camping": "True", "rv_sites_count": "280",
                "has_tent_camping": "True", "tent_sites_count": "30", "primitive_camping": "False",
                "max_rig_length_ft": "40", "waterfront_sites": "True", "hiking": "True", "fishing": "True",
                "swimming": "True", "boat_ramp": "True", "golf": "False", "pet_friendly": "True", "wifi": "False",
                "description_text": "Framed by the dramatic San Juan Mountains, Ridgway features a beautiful reservoir, sandy beach, modern campsites, and paved walking paths."
            }
        ]
    },
    "CT": {
        "name": "Connecticut",
        "url": "https://ctparks.com",
        "res_url": "https://www.reserveamerica.com",
        "parks": [
            {
                "park_name": "Hammonasset Beach State Park",
                "address": "1288 Boston Post Rd, Madison, CT 06443",
                "has_rv_camping": "True", "rv_sites_count": "550",
                "has_tent_camping": "True", "tent_sites_count": "50", "primitive_camping": "False",
                "max_rig_length_ft": "35", "waterfront_sites": "True", "hiking": "True", "fishing": "True",
                "swimming": "True", "boat_ramp": "False", "golf": "False", "pet_friendly": "False", "wifi": "False",
                "description_text": "Connecticut's largest shoreline park offers over two miles of sandy beach, boardwalk walking, bicycling, and a massive coastal campground."
            },
            {
                "park_name": "Rocky Neck State Park",
                "address": "244 W Main St, East Lyme, CT 06357",
                "has_rv_camping": "True", "rv_sites_count": "160",
                "has_tent_camping": "True", "tent_sites_count": "40", "primitive_camping": "False",
                "max_rig_length_ft": "30", "waterfront_sites": "True", "hiking": "True", "fishing": "True",
                "swimming": "True", "boat_ramp": "False", "golf": "False", "pet_friendly": "False", "wifi": "False",
                "description_text": "Rocky Neck features a sandy beach on Long Island Sound, salt marsh boardwalks, historic stone pavilions, and wooded campgrounds."
            },
            {
                "park_name": "Black Rock State Park",
                "address": "2065 Thomaston Rd, Watertown, CT 06795",
                "has_rv_camping": "True", "rv_sites_count": "78",
                "has_tent_camping": "True", "tent_sites_count": "20", "primitive_camping": "False",
                "max_rig_length_ft": "25", "waterfront_sites": "True", "hiking": "True", "fishing": "True",
                "swimming": "True", "boat_ramp": "False", "golf": "False", "pet_friendly": "False", "wifi": "False",
                "description_text": "Nestled in the scenic Litchfield Hills, Black Rock offers pond swimming, hiking trails to scenic vistas, and a heavily wooded campground."
            },
            {
                "park_name": "Devil's Hopyard State Park",
                "address": "366 Hopyard Rd, East Haddam, CT 06423",
                "has_rv_camping": "True", "rv_sites_count": "21",
                "has_tent_camping": "True", "tent_sites_count": "10", "primitive_camping": "True",
                "max_rig_length_ft": "20", "waterfront_sites": "True", "hiking": "True", "fishing": "True",
                "swimming": "False", "boat_ramp": "False", "golf": "False", "pet_friendly": "False", "wifi": "False",
                "description_text": "Famous for Chapman Falls and historic stone bridges, Devil's Hopyard features quiet, heavily shaded campsites along a rushing trout stream."
            },
            {
                "park_name": "Hopeville Pond State Park",
                "address": "929 Hopeville Rd, Griswold, CT 06351",
                "has_rv_camping": "True", "rv_sites_count": "80",
                "has_tent_camping": "True", "tent_sites_count": "20", "primitive_camping": "False",
                "max_rig_length_ft": "25", "waterfront_sites": "True", "hiking": "True", "fishing": "True",
                "swimming": "True", "boat_ramp": "True", "golf": "False", "pet_friendly": "False", "wifi": "False",
                "description_text": "Set in a historical mill pond area, Hopeville Pond offers water sports, fishing, beach swimming, and quiet wooded campsites."
            },
            {
                "park_name": "Housatonic Meadows State Park",
                "address": "90 US-7, Sharon, CT 06069",
                "has_rv_camping": "True", "rv_sites_count": "95",
                "has_tent_camping": "True", "tent_sites_count": "30", "primitive_camping": "False",
                "max_rig_length_ft": "30", "waterfront_sites": "True", "hiking": "True", "fishing": "True",
                "swimming": "False", "boat_ramp": "False", "golf": "False", "pet_friendly": "False", "wifi": "False",
                "description_text": "Situated directly along the beautiful Housatonic River, this pine-forested park is popular for fly fishing and rustic riverside camping."
            },
            {
                "park_name": "Lake Waramaug State Park",
                "address": "30 Lake Waramaug Rd, New Preston, CT 06777",
                "has_rv_camping": "True", "rv_sites_count": "76",
                "has_tent_camping": "True", "tent_sites_count": "10", "primitive_camping": "False",
                "max_rig_length_ft": "25", "waterfront_sites": "True", "hiking": "False", "fishing": "True",
                "swimming": "True", "boat_ramp": "False", "golf": "False", "pet_friendly": "False", "wifi": "False",
                "description_text": "Offers spectacular water views on Lake Waramaug, canoe rentals, swimming, fishing, and scenic shoreline camping."
            },
            {
                "park_name": "Macedonia Brook State Park",
                "address": "159 Macedonia Brook Rd, Kent, CT 06757",
                "has_rv_camping": "True", "rv_sites_count": "51",
                "has_tent_camping": "True", "tent_sites_count": "20", "primitive_camping": "True",
                "max_rig_length_ft": "20", "waterfront_sites": "True", "hiking": "True", "fishing": "True",
                "swimming": "False", "boat_ramp": "False", "golf": "False", "pet_friendly": "False", "wifi": "False",
                "description_text": "Macedonia Brook features a rugged trail network, mountain streams, scenic gorge views, and quiet rustic campsites."
            },
            {
                "park_name": "Mashamoquet Brook State Park",
                "address": "147 Wolf Den Rd, Pomfret Center, CT 06259",
                "has_rv_camping": "True", "rv_sites_count": "53",
                "has_tent_camping": "True", "tent_sites_count": "15", "primitive_camping": "False",
                "max_rig_length_ft": "25", "waterfront_sites": "True", "hiking": "True", "fishing": "True",
                "swimming": "True", "boat_ramp": "False", "golf": "False", "pet_friendly": "False", "wifi": "False",
                "description_text": "Home to the historical Wolf Den cave, the park offers wooded campgrounds, streams, hiking trails, and a pond swimming area."
            },
            {
                "park_name": "Kettletown State Park",
                "address": "1400 Georges Hill Rd, Southbury, CT 06488",
                "has_rv_camping": "True", "rv_sites_count": "60",
                "has_tent_camping": "True", "tent_sites_count": "20", "primitive_camping": "False",
                "max_rig_length_ft": "30", "waterfront_sites": "True", "hiking": "True", "fishing": "True",
                "swimming": "False", "boat_ramp": "False", "golf": "False", "pet_friendly": "False", "wifi": "False",
                "description_text": "Located on the shores of Lake Zoar on the Housatonic River, Kettletown offers extensive hiking trails, vistas, and shaded campsites."
            }
        ]
    }
}

def to_slug(name):
    return re.sub(r'[^a-z0-9\-]+', '-', name.lower().replace("'", "")).strip('-')

def main():
    for state_code, state_info in DATASETS.items():
        csv_filename = f"{state_info['name'].lower()}_state_parks.csv"
        md_filename = f"{state_info['name'].lower()}_state_parks.md"
        
        print(f"Creating files for {state_info['name']}...")
        
        # Write CSV
        with open(csv_filename, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=HEADERS)
            writer.writeheader()
            
            for p in state_info["parks"]:
                row = {h: "" for h in HEADERS}
                row["park_name"] = p["park_name"]
                row["park_slug"] = to_slug(p["park_name"])
                row["state"] = state_code
                row["park_url"] = f"{state_info['url']}/parks/{row['park_slug']}"
                row["address"] = p["address"]
                row["has_rv_camping"] = p["has_rv_camping"]
                row["rv_sites_count"] = p["rv_sites_count"]
                row["has_tent_camping"] = p["has_tent_camping"]
                row["tent_sites_count"] = p["tent_sites_count"]
                row["primitive_camping"] = p["primitive_camping"]
                row["max_rig_length_ft"] = p["max_rig_length_ft"]
                row["waterfront_sites"] = p["waterfront_sites"]
                row["hiking"] = p["hiking"]
                row["fishing"] = p["fishing"]
                row["swimming"] = p["swimming"]
                row["boat_ramp"] = p["boat_ramp"]
                row["golf"] = p["golf"]
                row["pet_friendly"] = p["pet_friendly"]
                row["wifi"] = p["wifi"]
                row["description_text"] = p["description_text"]
                row["campground_text"] = p["description_text"]
                row["reservation_url"] = f"{state_info['res_url']}/unifSearch.do?keyword=" + p["park_name"].replace(" ", "+")
                row["scraped_at"] = "2026-05-24 18:00:00"
                writer.writerow(row)
                
        # Write MD
        with open(md_filename, mode="w", newline="", encoding="utf-8") as f:
            f.write(f"# {state_info['name']} State Parks Directory\n\n")
            f.write(f"This directory lists the major state parks in {state_info['name']} that support camping, compiled for the Campground Discovery web application.\n\n")
            f.write("## Parks List\n\n")
            
            for p in state_info["parks"]:
                f.write(f"### {p['park_name']}\n")
                f.write(f"* **Location**: {p['address']}\n")
                f.write(f"* **Camping Sites**: {p['rv_sites_count']} RV sites, {p['tent_sites_count']} Tent/Primitive sites\n")
                f.write(f"* **Description**: {p['description_text']}\n\n")
                
        print(f"  Created {csv_filename} and {md_filename}")
        
    return 0

if __name__ == "__main__":
    main()
