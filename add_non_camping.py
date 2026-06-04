#!/usr/bin/env python3
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

NON_CAMPING_PARKS = {
    "AL": [],
    "AK": [
        {
            "park_name": "Potter Section House State Historic Site",
            "park_url": "https://dnr.alaska.gov/parks/aspunits/chugach/potrangerst.htm",
            "address": "MHT 9400234 Seward Hwy, Anchorage, AK 99516",
            "latitude": 61.0416,
            "longitude": -149.7947,
            "phone_general": "907-269-8400",
            "pet_friendly": True,
            "hiking": True,
            "description_text": "Potter Section House State Historic Site features rail history exhibits, a historic rotary snowplow, and access to wildlife viewing along the Turnagain Arm.",
        },
        {
            "park_name": "Refuge Cove State Recreation Site",
            "park_url": "https://dnr.alaska.gov/parks/aspunits/southeast/refugecvsrs.htm",
            "address": "Refuge Cove Rd, Ketchikan, AK 99901",
            "latitude": 55.4019,
            "longitude": -131.7514,
            "phone_general": "907-225-2422",
            "pet_friendly": True,
            "hiking": False,
            "description_text": "Refuge Cove State Recreation Site offers beach access, picnicking facilities, and beautiful views of the coastal waters for day visitors.",
        },
        {
            "park_name": "Baranof Castle State Historic Site",
            "park_url": "http://dnr.alaska.gov/parks/aspunits/southeast/baranofcastle.htm",
            "address": "Castle Hill, Sitka, AK 99835",
            "latitude": 57.0494,
            "longitude": -135.3375,
            "phone_general": "907-269-8738",
            "pet_friendly": True,
            "hiking": True,
            "description_text": "Baranof Castle State Historic Site, located on Castle Hill in Sitka, is one of the most historically significant sites in Alaska, where the formal transfer of Alaska from Russia to the US occurred.",
        }
    ],
    "AZ": [
        {
            "park_name": "Red Rock State Park",
            "park_url": "https://azstateparks.com/red-rock",
            "address": "4050 Red Rock Loop Rd, Sedona, AZ 86336",
            "latitude": 34.8105,
            "longitude": -111.8315,
            "phone_general": "928-282-6907",
            "pet_friendly": False,
            "hiking": True,
            "description_text": "Red Rock State Park is a day-use environmental education center and nature preserve with stunning red rock vistas, hiking trails, and riparian habitats along Oak Creek.",
        },
        {
            "park_name": "Slide Rock State Park",
            "park_url": "https://azstateparks.com/slide-rock",
            "address": "6871 AZ-89A, Sedona, AZ 86336",
            "latitude": 34.9439,
            "longitude": -111.7533,
            "phone_general": "928-282-3034",
            "pet_friendly": False,
            "hiking": True,
            "swimming": True,
            "description_text": "Slide Rock State Park features a famous natural water slide formed by the slippery bed of Oak Creek, historic apple orchards, and scenic day-use picnic areas.",
        },
        {
            "park_name": "Tonto Natural Bridge State Park",
            "park_url": "https://azstateparks.com/tonto",
            "address": "nf-583, Payson, AZ 85541",
            "latitude": 34.3217,
            "longitude": -111.4538,
            "phone_general": "928-476-4205",
            "pet_friendly": False,
            "hiking": True,
            "description_text": "Tonto Natural Bridge State Park preserves what is believed to be the largest natural travertine bridge in the world, surrounded by beautiful pine forests and canyon hiking trails.",
        },
        {
            "park_name": "Riordan Mansion State Historic Park",
            "park_url": "https://azstateparks.com/riordan-mansion",
            "address": "409 W Riordan Rd, Flagstaff, AZ 86001",
            "latitude": 35.1897,
            "longitude": -111.6624,
            "phone_general": "928-779-4395",
            "pet_friendly": False,
            "hiking": False,
            "description_text": "Riordan Mansion State Historic Park features a magnificent 1904 Arts and Crafts style mansion built by timber barons Michael and Timothy Riordan, offering day tours.",
        }
    ],
    "AR": [
        {
            "park_name": "Mammoth Spring State Park",
            "park_url": "https://www.arkansasstateparks.com/parks/mammoth-spring-state-park",
            "address": "17 Park Rd, Mammoth Spring, AR 72554",
            "latitude": 36.4912,
            "longitude": -91.5361,
            "phone_general": "870-625-7364",
            "pet_friendly": True,
            "hiking": True,
            "description_text": "Mammoth Spring State Park surrounds Arkansas's largest natural spring, flowing nine million gallons hourly; features a historic train depot, hiking paths, and river fishing.",
        },
        {
            "park_name": "Plum Bayou Mounds Archeological State Park",
            "park_url": "https://www.arkansasstateparks.com/parks/plum-bayou-mounds-archeological-state-park",
            "address": "490 Toltec Mounds Rd, Scott, AR 72142",
            "latitude": 34.6469,
            "longitude": -92.0642,
            "phone_general": "501-961-9442",
            "pet_friendly": False,
            "hiking": True,
            "description_text": "Plum Bayou Mounds Archeological State Park (formerly Toltec Mounds) preserves prehistoric Native American ceremonial mounds with day-use educational exhibits and walking trails.",
        },
        {
            "park_name": "Logoly State Park",
            "park_url": "https://www.arkansasstateparks.com/parks/logoly-state-park",
            "address": "County Road 47, Magnolia, AR 71753",
            "latitude": 33.3444,
            "longitude": -93.1889,
            "phone_general": "870-695-3561",
            "pet_friendly": True,
            "hiking": True,
            "description_text": "Logoly State Park is Arkansas's first environmental education state park, featuring mineral springs, hiking trails through old-growth forests, and day-use visitor exhibits.",
        }
    ],
    "CA": [
        {
            "park_name": "Torrey Pines State Natural Reserve",
            "park_url": "https://www.parks.ca.gov/?page_id=657",
            "address": "12600 N Torrey Pines Rd, La Jolla, CA 92037",
            "latitude": 32.9218,
            "longitude": -117.2528,
            "phone_general": "858-755-2063",
            "pet_friendly": False,
            "hiking": True,
            "description_text": "Torrey Pines State Natural Reserve preserves one of the world's rarest pine trees, the Torrey Pine, featuring rugged sandstone cliffs, hiking trails, and beautiful day-use beaches.",
        },
        {
            "park_name": "Point Lobos State Natural Reserve",
            "park_url": "https://www.parks.ca.gov/?page_id=571",
            "address": "27240 CA-1, Carmel-By-The-Sea, CA 93923",
            "latitude": 36.5235,
            "longitude": -121.9427,
            "phone_general": "831-624-4909",
            "pet_friendly": False,
            "hiking": True,
            "description_text": "Point Lobos State Natural Reserve is often called the crown jewel of California state parks, offering hiking trails, tidepools, sea otter habitats, and historic whaling museums.",
        },
        {
            "park_name": "Wilder Ranch State Park",
            "park_url": "https://www.parks.ca.gov/?page_id=549",
            "address": "1401 Coast Rd, Santa Cruz, CA 95060",
            "latitude": 36.9634,
            "longitude": -122.0839,
            "phone_general": "831-423-9703",
            "pet_friendly": False,
            "hiking": True,
            "description_text": "Wilder Ranch State Park preserves a historic 19th-century dairy ranch and features extensive day-use hiking, biking, and equestrian trails along scenic coastal bluffs.",
        },
        {
            "park_name": "Tomales Bay State Park",
            "park_url": "https://www.parks.ca.gov/?page_id=470",
            "address": "1208 Pierce Point Rd, Inverness, CA 94937",
            "latitude": 38.1256,
            "longitude": -122.8833,
            "phone_general": "415-669-1140",
            "pet_friendly": False,
            "hiking": True,
            "swimming": True,
            "description_text": "Tomales Bay State Park provides calm water beaches sheltered from winds, picnic tables, and hiking trails through coastal bishop pine forests, day-use only.",
        }
    ],
    "CO": [
        {
            "park_name": "Barr Lake State Park",
            "park_url": "https://cpw.state.co.us/state-parks/barr-lake-state-park",
            "address": "13401 Picadilly Rd, Brighton, CO 80603",
            "latitude": 39.9497,
            "longitude": -104.7571,
            "phone_general": "303-659-6005",
            "pet_friendly": True,
            "hiking": True,
            "fishing": True,
            "description_text": "Barr Lake State Park is a day-use sanctuary popular with bird watchers and boaters, offering a nature center, multi-use trails, and excellent viewing of bald eagles.",
        },
        {
            "park_name": "Castlewood Canyon State Park",
            "park_url": "https://cpw.state.co.us/state-parks/castlewood-canyon-state-park",
            "address": "2989 S State Hwy 83, Franktown, CO 80116",
            "latitude": 39.3364,
            "longitude": -104.7578,
            "phone_general": "303-688-5242",
            "pet_friendly": True,
            "hiking": True,
            "description_text": "Castlewood Canyon State Park features dramatic canyon hiking trails, historical ruins of the Castlewood Dam, rock climbing areas, and day-use picnicking.",
        },
        {
            "park_name": "Fishers Peak State Park",
            "park_url": "https://cpw.state.co.us/state-parks/fishers-peak-state-park",
            "address": "Trinidad, CO 81082",
            "latitude": 37.1006,
            "longitude": -104.4447,
            "phone_general": "719-846-6951",
            "pet_friendly": False,
            "hiking": True,
            "description_text": "Fishers Peak State Park surrounds the iconic 9,633-foot Fishers Peak; currently open to public day visitors for trail hiking, picnicking, and wildlife observation.",
        },
        {
            "park_name": "Roxborough State Park",
            "park_url": "https://cpw.state.co.us/state-parks/roxborough-state-park",
            "address": "4751 Roxborough Drive, Littleton, CO 80125",
            "latitude": 39.4289,
            "longitude": -105.0683,
            "phone_general": "303-973-3959",
            "pet_friendly": False,
            "hiking": True,
            "description_text": "Roxborough State Park is a National Natural Landmark offering spectacular red rock formations, geological history, and quiet nature trails for day hikers.",
        }
    ],
    "CT": [
        {
            "park_name": "Sherwood Island State Park",
            "park_url": "https://portal.ct.gov/deep/state-parks/parks/sherwood-island-state-park",
            "address": "Sherwood Island Connector, Westport, CT 06880",
            "latitude": 41.1158,
            "longitude": -73.3325,
            "phone_general": "203-226-6981",
            "pet_friendly": False,
            "hiking": True,
            "swimming": True,
            "description_text": "Sherwood Island State Park, Connecticut's first state park, offers sandy beaches, shoreline walking, a nature center, and scenic picnic grounds along Long Island Sound.",
        },
        {
            "park_name": "Gillette Castle State Park",
            "park_url": "https://portal.ct.gov/deep/state-parks/parks/gillette-castle-state-park",
            "address": "67 River Rd, East Haddam, CT 06423",
            "latitude": 41.4223,
            "longitude": -72.4308,
            "phone_general": "860-526-2336",
            "pet_friendly": False,
            "hiking": True,
            "description_text": "Gillette Castle State Park features the fieldstone castle built by actor William Gillette, overlooking the Connecticut River, with day tours and wooded trails.",
        },
        {
            "park_name": "Kent Falls State Park",
            "park_url": "https://portal.ct.gov/deep/state-parks/parks/kent-falls-state-park",
            "address": "462 Kent Cornwall Rd, Kent, CT 06757",
            "latitude": 41.7779,
            "longitude": -73.4173,
            "phone_general": "860-927-3238",
            "pet_friendly": False,
            "hiking": True,
            "description_text": "Kent Falls State Park features a series of cascading waterfalls on Kent Falls Brook, a covered bridge, and a winding trail with viewing platforms.",
        },
        {
            "park_name": "Dinosaur State Park",
            "park_url": "https://portal.ct.gov/deep/state-parks/parks/dinosaur-state-park",
            "address": "400 West St, Rocky Hill, CT 06067",
            "latitude": 41.6514,
            "longitude": -72.6569,
            "phone_general": "860-529-8423",
            "pet_friendly": False,
            "hiking": True,
            "description_text": "Dinosaur State Park features one of the largest dinosaur trackways in North America, preserved under a large geodesic dome, with educational nature trails.",
        },
        {
            "park_name": "Sleeping Giant State Park",
            "park_url": "https://portal.ct.gov/deep/state-parks/parks/sleeping-giant-state-park",
            "address": "200 Mount Carmel Ave, Hamden, CT 06518",
            "latitude": 41.4211,
            "longitude": -72.8988,
            "phone_general": "203-789-7494",
            "pet_friendly": False,
            "hiking": True,
            "description_text": "Sleeping Giant State Park features a mountaintop stone observation tower at the end of a scenic trail resembling a giant lying down, popular for hiking and views.",
        }
    ],
    "HI": [
        {
            "park_name": "Diamond Head State Monument",
            "park_url": "https://dlnr.hawaii.gov/dsp/parks/oahu/diamond-head-state-monument/",
            "address": "Diamond Head Road, Honolulu, HI 96815",
            "latitude": 21.2625,
            "longitude": -157.8062,
            "phone_general": "808-587-0300",
            "pet_friendly": False,
            "hiking": True,
            "description_text": "Diamond Head State Monument features the iconic volcanic tuff cone of Diamond Head (Leahi), offering a steep historic hiking trail to the summit with panoramic views of Waikiki and the Pacific Ocean.",
        }
    ],
    "ID": [
        {
            "park_name": "Lucky Peak State Park",
            "park_url": "https://parksandrecreation.idaho.gov/parks/lucky-peak/",
            "address": "9725 E Highway 21, Boise, ID 83716",
            "latitude": 43.5228,
            "longitude": -116.0592,
            "phone_general": "208-334-2432",
            "pet_friendly": True,
            "hiking": True,
            "swimming": True,
            "boat_ramp": True,
            "description_text": "Lucky Peak State Park, located close to Boise, consists of three units (Discovery, Sandy Point, Spring Shores) offering swimming, boating, and picnicking along the Boise River and Lucky Peak Reservoir.",
        }
    ],
    "IL": [
        {
            "park_name": "Matthiessen State Park",
            "park_url": "https://dnr.illinois.gov/parks/park.matthiessen.html",
            "address": "2500 IL-178, Utica, IL 61373",
            "latitude": 41.2959,
            "longitude": -89.027,
            "phone_general": "815-667-4868",
            "pet_friendly": True,
            "hiking": True,
            "description_text": "Matthiessen State Park features beautiful sandstone canyons, mineral springs, and unusual rock formations along a scenic mile-long canyon, located just south of Starved Rock.",
        }
    ],
    "IN": [
        {
            "park_name": "Fort Harrison State Park",
            "park_url": "https://www.in.gov/dnr/state-parks/parks-lakes/fort-harrison-state-park/",
            "address": "6000 N Post Rd, Indianapolis, IN 46216",
            "latitude": 39.8667,
            "longitude": -86.0167,
            "phone_general": "317-591-0904",
            "pet_friendly": True,
            "hiking": True,
            "description_text": "Fort Harrison State Park features scenic walking trails along Fall Creek, a championship golf course, a historic military base museum, and popular sledding hills.",
        }
    ],
    "IA": [
        {
            "park_name": "Mines of Spain State Recreation Area",
            "park_url": "https://www.iowadnr.gov/places-go/state-parks/all-parks/mines-spain-state-recreation-area",
            "address": "8991 Bellevue Heights Rd, Dubuque, IA 52003",
            "latitude": 42.4633,
            "longitude": -90.6472,
            "phone_general": "563-556-0620",
            "pet_friendly": True,
            "hiking": True,
            "description_text": "Mines of Spain State Recreation Area features rugged limestone bluffs overlooking the Mississippi River, historic lead mining sites, and the Julien Dubuque Monument.",
        }
    ],
    "KS": [
        {
            "park_name": "Little Jerusalem Badlands State Park",
            "park_url": "https://ksoutdoors.com/State-Parks/Locations/Little-Jerusalem-Badlands",
            "address": "County Rd 400, Oakley, KS 67748",
            "latitude": 38.8048,
            "longitude": -100.9328,
            "phone_general": "785-877-2953",
            "pet_friendly": False,
            "hiking": True,
            "description_text": "Little Jerusalem Badlands State Park features 220 acres of dramatic, 100-foot-tall chalk rock formations, providing habitat for unique plants and wildlife, with trails offering scenic overlooks.",
        }
    ],
    "KY": [
        {
            "park_name": "Perryville Battlefield State Historic Site",
            "park_url": "https://parks.ky.gov/perryville/parks/historic/perryville-battlefield-state-historic-site",
            "address": "1825 Battlefield Rd, Perryville, KY 40468",
            "latitude": 37.6728,
            "longitude": -84.9756,
            "phone_general": "859-332-8631",
            "pet_friendly": True,
            "hiking": True,
            "description_text": "Perryville Battlefield State Historic Site preserves the site of the most destructive Civil War battle in Kentucky, featuring a museum, walking trails, and historical markers.",
        }
    ],
    "LA": [
        {
            "park_name": "Longfellow-Evangeline State Historic Site",
            "park_url": "https://www.lastateparks.com/historic-sites/longfellow-evangeline-state-historic-site",
            "address": "1200 N Main St, St. Martinville, LA 70582",
            "latitude": 30.1367,
            "longitude": -91.8267,
            "phone_general": "337-394-3754",
            "pet_friendly": False,
            "hiking": True,
            "description_text": "Longfellow-Evangeline State Historic Site explores the cultural history of the Bayou Teche region, featuring a historic plantation home, reproduction Acadian cabin, and museum exhibits.",
        }
    ]
}

def to_slug(name):
    return re.sub(r'[^a-z0-9\-]+', '-', name.lower().replace("'", "")).strip('-')

def main():
    state_files = {
        "AL": "alabama_state_parks.csv",
        "AK": "alaska_state_parks.csv",
        "AZ": "arizona_state_parks.csv",
        "AR": "arkansas_state_parks.csv",
        "CA": "california_state_parks.csv",
        "CO": "colorado_state_parks.csv",
        "CT": "connecticut_state_parks.csv",
        "HI": "hawaii_state_parks.csv",
        "ID": "idaho_state_parks.csv",
        "IL": "illinois_state_parks.csv",
        "IN": "indiana_state_parks.csv",
        "IA": "iowa_state_parks.csv",
        "KS": "kansas_state_parks.csv",
        "KY": "kentucky_state_parks.csv",
        "LA": "louisiana_state_parks.csv"
    }

    for state_code, file_name in state_files.items():
        if not os.path.exists(file_name):
            print(f"Error: {file_name} not found. Skipping.")
            continue
            
        print(f"Appending non-camping parks to {file_name}...")
        
        # Read existing records
        records = []
        with open(file_name, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            for row in reader:
                records.append(row)

        # Check if already added
        existing_names = {r["park_name"] for r in records}
        added_count = 0
        
        new_parks = NON_CAMPING_PARKS.get(state_code, [])
        for p in new_parks:
            if p["park_name"] in existing_names:
                print(f"  Park '{p['park_name']}' already exists. Skipping.")
                continue
                
            # Create a row matching header format
            row = {h: "" for h in HEADERS}
            row["park_name"] = p["park_name"]
            row["park_slug"] = to_slug(p["park_name"])
            row["state"] = state_code
            row["park_url"] = p["park_url"]
            row["address"] = p["address"]
            row["latitude"] = str(p["latitude"])
            row["longitude"] = str(p["longitude"])
            row["phone_general"] = p.get("phone_general", "")
            row["has_rv_camping"] = "False"
            row["rv_sites_count"] = "0"
            row["has_tent_camping"] = "False"
            row["tent_sites_count"] = "0"
            row["primitive_camping"] = "False"
            row["max_rig_length_ft"] = "0"
            row["pull_through_available"] = "False"
            row["electric_30amp"] = "False"
            row["electric_50amp"] = "False"
            row["water_hookup"] = "False"
            row["sewer_hookup"] = "False"
            row["dump_station"] = "False"
            row["full_hookups"] = "False"
            row["showers"] = "False"
            row["laundry"] = "False"
            row["wifi"] = "False"
            row["pet_friendly"] = "True" if p.get("pet_friendly") else "False"
            row["hiking"] = "True" if p.get("hiking") else "False"
            row["swimming"] = "True" if p.get("swimming") else "False"
            row["fishing"] = "True" if p.get("fishing") else "False"
            row["boat_ramp"] = "True" if p.get("boat_ramp") else "False"
            row["golf"] = "True" if p.get("golf") else "False"
            row["description_text"] = p["description_text"]
            row["campground_text"] = ""
            row["scraped_at"] = "2026-05-29 18:00:00"
            
            records.append(row)
            added_count += 1
            
        if added_count > 0:
            with open(file_name, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames if fieldnames else HEADERS)
                writer.writeheader()
                writer.writerows(records)
            print(f"  Appended {added_count} parks to {file_name}.")
        else:
            print("  No new parks added.")

    print("\nSuccessfully finished appending non-camping parks.")

if __name__ == "__main__":
    main()
