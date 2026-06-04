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

NEW_STATES_DATA = {
    "KS": [
        {
            "park_name": "Clinton State Park",
            "park_slug": "clinton-state-park",
            "park_url": "https://ksoutdoors.com/State-Parks/Locations/Clinton",
            "address": "798 N 1415 Rd, Lawrence, KS 66049",
            "phone_general": "785-842-8562",
            "has_rv_camping": True,
            "rv_sites_count": 240,
            "has_tent_camping": True,
            "tent_sites_count": 150,
            "primitive_camping": True,
            "max_rig_length_ft": 50,
            "electric_30amp": True,
            "electric_50amp": True,
            "water_hookup": True,
            "sewer_hookup": True,
            "dump_station": True,
            "showers": True,
            "pet_friendly": True,
            "hiking": True,
            "fishing": True,
            "swimming": True,
            "boat_ramp": True,
            "reservation_url": "https://www.kshuntfishcamp.com",
            "description_text": "Clinton State Park is situated on the north shore of Clinton Reservoir near Lawrence, featuring clear water, forested hills, sandy swimming beaches, and extensive hiking and mountain biking trails.",
            "campground_text": "Features 240 water and electric campsites, plus numerous primitive tent camping sites, modern shower facilities, playgrounds, and three dump stations."
        },
        {
            "park_name": "Tuttle Creek State Park",
            "park_slug": "tuttle-creek-state-park",
            "park_url": "https://ksoutdoors.com/State-Parks/Locations/Tuttle-Creek",
            "address": "5800 River Pond Rd, Manhattan, KS 66502",
            "phone_general": "785-539-7941",
            "has_rv_camping": True,
            "rv_sites_count": 100,
            "has_tent_camping": True,
            "tent_sites_count": 200,
            "primitive_camping": True,
            "max_rig_length_ft": 45,
            "electric_30amp": True,
            "electric_50amp": True,
            "water_hookup": True,
            "sewer_hookup": False,
            "dump_station": True,
            "showers": True,
            "pet_friendly": True,
            "hiking": True,
            "fishing": True,
            "swimming": True,
            "boat_ramp": True,
            "reservation_url": "https://www.kshuntfishcamp.com",
            "description_text": "Tuttle Creek State Park is located adjacent to Tuttle Creek Reservoir near Manhattan, offering scenic water recreation, disc golf courses, archery, and excellent wildlife viewing.",
            "campground_text": "Offers 100 electric/water hookup sites, over 200 designated primitive tent sites, restroom and shower facilities, and dump stations."
        },
        {
            "park_name": "El Dorado State Park",
            "park_slug": "el-dorado-state-park",
            "park_url": "https://ksoutdoors.com/State-Parks/Locations/El-Dorado",
            "address": "861 NE Eastbound Hwy 54, El Dorado, KS 67042",
            "phone_general": "316-321-7180",
            "has_rv_camping": True,
            "rv_sites_count": 500,
            "has_tent_camping": True,
            "tent_sites_count": 500,
            "primitive_camping": True,
            "max_rig_length_ft": 60,
            "electric_30amp": True,
            "electric_50amp": True,
            "water_hookup": True,
            "sewer_hookup": True,
            "dump_station": True,
            "showers": True,
            "pet_friendly": True,
            "hiking": True,
            "fishing": True,
            "swimming": True,
            "boat_ramp": True,
            "reservation_url": "https://www.kshuntfishcamp.com",
            "description_text": "El Dorado State Park is one of the largest and most popular state parks in Kansas, situated on the shores of El Dorado Reservoir, offering boating, fishing, hiking, and equestrian trails.",
            "campground_text": "Features massive campgrounds with nearly 500 utility sites (electric/water/sewer) and hundreds of primitive tent sites. Modern restrooms, hot showers, and group shelters."
        },
        {
            "park_name": "Kanopolis State Park",
            "park_slug": "kanopolis-state-park",
            "park_url": "https://ksoutdoors.com/State-Parks/Locations/Kanopolis",
            "address": "200 Horsethief Rd, Marquette, KS 67464",
            "phone_general": "785-546-2565",
            "has_rv_camping": True,
            "rv_sites_count": 130,
            "has_tent_camping": True,
            "tent_sites_count": 150,
            "primitive_camping": True,
            "max_rig_length_ft": 40,
            "electric_30amp": True,
            "electric_50amp": True,
            "water_hookup": True,
            "sewer_hookup": False,
            "dump_station": True,
            "showers": True,
            "pet_friendly": True,
            "hiking": True,
            "fishing": True,
            "swimming": True,
            "boat_ramp": True,
            "reservation_url": "https://www.kshuntfishcamp.com",
            "description_text": "Kanopolis State Park is the oldest state park in Kansas, featuring rugged sandstone canyons, caves, the famous Horsethief Canyon trail system, and access to Kanopolis Reservoir.",
            "campground_text": "Offers 130 sites with water and electricity, over 150 primitive tent sites, shower houses, dump stations, and horse camping areas."
        }
    ],
    "KY": [
        {
            "park_name": "Cumberland Falls State Resort Park",
            "park_slug": "cumberland-falls-state-resort-park",
            "park_url": "https://parks.ky.gov/corbin/parks/resort/cumberland-falls-state-resort-park",
            "address": "7351 Hwy 90, Corbin, KY 40701",
            "phone_general": "606-528-4121",
            "has_rv_camping": True,
            "rv_sites_count": 50,
            "has_tent_camping": True,
            "tent_sites_count": 30,
            "primitive_camping": False,
            "max_rig_length_ft": 35,
            "electric_30amp": True,
            "electric_50amp": True,
            "water_hookup": True,
            "sewer_hookup": False,
            "dump_station": True,
            "showers": True,
            "pet_friendly": True,
            "hiking": True,
            "fishing": True,
            "swimming": True,
            "boat_ramp": False,
            "reservation_url": "https://kentuckystateparks.reserveamerica.com",
            "description_text": "Cumberland Falls State Resort Park is famous for Cumberland Falls, a 68-foot-tall waterfall known for producing a rare 'moonbow' during full moons. The park features dense forests, hiking, and whitewater rafting.",
            "campground_text": "Features 50 sites with electric and water hookups, 30 tent-only sites, modern bathhouses, and a dump station. Resort lodge and cabins are also available on site."
        },
        {
            "park_name": "Natural Bridge State Resort Park",
            "park_slug": "natural-bridge-state-resort-park",
            "park_url": "https://parks.ky.gov/slade/parks/resort/natural-bridge-state-resort-park",
            "address": "2135 Natural Bridge Rd, Slade, KY 40376",
            "phone_general": "606-663-2214",
            "has_rv_camping": True,
            "rv_sites_count": 80,
            "has_tent_camping": True,
            "tent_sites_count": 40,
            "primitive_camping": False,
            "max_rig_length_ft": 40,
            "electric_30amp": True,
            "electric_50amp": True,
            "water_hookup": True,
            "sewer_hookup": False,
            "dump_station": True,
            "showers": True,
            "pet_friendly": True,
            "hiking": True,
            "fishing": True,
            "swimming": True,
            "boat_ramp": False,
            "reservation_url": "https://kentuckystateparks.reserveamerica.com",
            "description_text": "Natural Bridge State Resort Park features a spectacular, natural sandstone arch that spans 78 feet and stands 65 feet high, adjacent to the Red River Gorge Geological Area, offering world-class hiking and climbing.",
            "campground_text": "Offers two campgrounds (Whittleton Campground and Middle Fork Campground) with a combined 80 utility sites and 40 tent sites, showers, restrooms, and a dump station."
        },
        {
            "park_name": "Carter Caves State Resort Park",
            "park_slug": "carter-caves-state-resort-park",
            "park_url": "https://parks.ky.gov/olive-hill/parks/resort/carter-caves-state-resort-park",
            "address": "344 Caveland Dr, Olive Hill, KY 41164",
            "phone_general": "606-286-4411",
            "has_rv_camping": True,
            "rv_sites_count": 90,
            "has_tent_camping": True,
            "tent_sites_count": 30,
            "primitive_camping": True,
            "max_rig_length_ft": 40,
            "electric_30amp": True,
            "electric_50amp": True,
            "water_hookup": True,
            "sewer_hookup": False,
            "dump_station": True,
            "showers": True,
            "pet_friendly": True,
            "hiking": True,
            "fishing": True,
            "swimming": True,
            "boat_ramp": False,
            "reservation_url": "https://kentuckystateparks.reserveamerica.com",
            "description_text": "Carter Caves State Resort Park contains the highest concentration of caves in Kentucky, offering guided cave tours, scenic sandstone arches, hiking, canoeing on Carter Caves Lake, and a golf course.",
            "campground_text": "Features 90 sites with water and electricity, 30 primitive tent sites, shower houses, laundry, and a dump station, plus equestrian camping facilities."
        },
        {
            "park_name": "Kentucky Dam Village State Resort Park",
            "park_slug": "kentucky-dam-village-state-resort-park",
            "park_url": "https://parks.ky.gov/gilbertsville/parks/resort/kentucky-dam-village-state-resort-park",
            "address": "113 Great Oaks Dr, Gilbertsville, KY 42044",
            "phone_general": "270-362-4271",
            "has_rv_camping": True,
            "rv_sites_count": 74,
            "has_tent_camping": True,
            "tent_sites_count": 20,
            "primitive_camping": False,
            "max_rig_length_ft": 45,
            "electric_30amp": True,
            "electric_50amp": True,
            "water_hookup": True,
            "sewer_hookup": False,
            "dump_station": True,
            "showers": True,
            "pet_friendly": True,
            "hiking": True,
            "fishing": True,
            "swimming": True,
            "boat_ramp": True,
            "reservation_url": "https://kentuckystateparks.reserveamerica.com",
            "description_text": "Kentucky Dam Village State Resort Park is located on the shores of Kentucky Lake, offering a large marina, 18-hole championship golf course, beach area, and resort lodge/cabins.",
            "campground_text": "Offers 74 sites with water and electric hookups, 20 tent sites, modern bathhouse, laundry, and access to the park's beach, pool, and marina."
        }
    ],
    "LA": [
        {
            "park_name": "Fontainebleau State Park",
            "park_slug": "fontainebleau-state-park",
            "park_url": "https://www.lastateparks.com/parks-preserves/fontainebleau-state-park",
            "address": "62883 Hwy 1089, Mandeville, LA 70448",
            "phone_general": "985-624-4443",
            "has_rv_camping": True,
            "rv_sites_count": 120,
            "has_tent_camping": True,
            "tent_sites_count": 50,
            "primitive_camping": True,
            "max_rig_length_ft": 45,
            "electric_30amp": True,
            "electric_50amp": True,
            "water_hookup": True,
            "sewer_hookup": True,
            "dump_station": True,
            "showers": True,
            "pet_friendly": True,
            "hiking": True,
            "fishing": True,
            "swimming": True,
            "boat_ramp": False,
            "reservation_url": "https://reserve.la-stateparks.com",
            "description_text": "Fontainebleau State Park is located on the shores of Lake Pontchartrain, featuring the brick ruins of a historic sugar mill, a sandy swimming beach, a splash pad, and access to the Tammany Trace bike trail.",
            "campground_text": "Offers 120 improved campsites with water and electricity, sewer hookups at selected premium sites, primitive tent camping areas, group camp, modern restrooms, and hot showers."
        },
        {
            "park_name": "Chicot State Park",
            "park_slug": "chicot-state-park",
            "park_url": "https://www.lastateparks.com/parks-preserves/chicot-state-park",
            "address": "3469 Chicot Park Rd, Ville Platte, LA 70586",
            "phone_general": "337-363-2403",
            "has_rv_camping": True,
            "rv_sites_count": 108,
            "has_tent_camping": True,
            "tent_sites_count": 40,
            "primitive_camping": True,
            "max_rig_length_ft": 40,
            "electric_30amp": True,
            "electric_50amp": True,
            "water_hookup": True,
            "sewer_hookup": False,
            "dump_station": True,
            "showers": True,
            "pet_friendly": True,
            "hiking": True,
            "fishing": True,
            "swimming": False,
            "boat_ramp": True,
            "reservation_url": "https://reserve.la-stateparks.com",
            "description_text": "Chicot State Park covers 6,400 acres of rolling hills in south-central Louisiana, featuring a scenic 2,000-acre lake stocked with bass, crappie, and bluegill, surrounded by cypress-tupelo forests.",
            "campground_text": "Features 108 campsites with water and electric hookups, primitive hike-in camping sites, cabins, modern restrooms, showers, and a dump station."
        },
        {
            "park_name": "Grand Isle State Park",
            "park_slug": "grand-isle-state-park",
            "park_url": "https://www.lastateparks.com/parks-preserves/grand-isle-state-park",
            "address": "108 Admiral Craik Dr, Grand Isle, LA 70358",
            "phone_general": "985-787-2559",
            "has_rv_camping": True,
            "rv_sites_count": 49,
            "has_tent_camping": True,
            "tent_sites_count": 14,
            "primitive_camping": True,
            "max_rig_length_ft": 50,
            "electric_30amp": True,
            "electric_50amp": True,
            "water_hookup": True,
            "sewer_hookup": False,
            "dump_station": True,
            "showers": True,
            "pet_friendly": True,
            "hiking": True,
            "fishing": True,
            "swimming": True,
            "boat_ramp": False,
            "reservation_url": "https://reserve.la-stateparks.com",
            "description_text": "Grand Isle State Park is situated on the eastern tip of Grand Isle, Louisiana's only inhabited barrier island, offering direct access to the sandy beaches of the Gulf of Mexico, surf fishing, crabbing, and a 400-foot fishing pier.",
            "campground_text": "Offers 49 premium RV sites with water and electricity right behind the sand dunes, plus 14 primitive beach tent sites, restrooms, and hot showers."
        },
        {
            "park_name": "Lake Claiborne State Park",
            "park_slug": "lake-claiborne-state-park",
            "park_url": "https://www.lastateparks.com/parks-preserves/lake-claiborne-state-park",
            "address": "1425 State Park Rd, Homer, LA 71040",
            "phone_general": "318-927-2976",
            "has_rv_camping": True,
            "rv_sites_count": 87,
            "has_tent_camping": True,
            "tent_sites_count": 30,
            "primitive_camping": False,
            "max_rig_length_ft": 40,
            "electric_30amp": True,
            "electric_50amp": True,
            "water_hookup": True,
            "sewer_hookup": False,
            "dump_station": True,
            "showers": True,
            "pet_friendly": True,
            "hiking": True,
            "fishing": True,
            "swimming": True,
            "boat_ramp": True,
            "reservation_url": "https://reserve.la-stateparks.com",
            "description_text": "Lake Claiborne State Park is located on the shores of Lake Claiborne in northern Louisiana, offering a sandy beach, boating, water skiing, excellent freshwater fishing, and two top-rated disc golf courses.",
            "campground_text": "Features 87 campsites with water and electric hookups, modern bathhouses with hot showers, two dump stations, cabins, and rental pavilions."
        }
    ]
}

def main():
    print("Generating KS, KY, LA state parks CSVs...")
    
    state_names = {
        "KS": "kansas",
        "KY": "kentucky",
        "LA": "louisiana"
    }
    
    for state_code, parks in NEW_STATES_DATA.items():
        state_name = state_names[state_code]
        csv_filename = f"{state_name}_state_parks.csv"
        
        records = []
        for p in parks:
            row = {h: "" for h in HEADERS}
            
            # Copy all fields present
            for key, val in p.items():
                if key in row:
                    row[key] = val
            
            # Fill booleans/types
            for key in ["has_rv_camping", "has_tent_camping", "primitive_camping", 
                        "pull_through_available", "electric_30amp", "electric_50amp", 
                        "water_hookup", "sewer_hookup", "dump_station", "full_hookups", 
                        "showers", "laundry", "wifi", "pet_friendly", "ada_sites", 
                        "waterfront_sites", "lake_river_access", "hiking", "fishing", 
                        "swimming", "boat_ramp", "golf", "open_year_round", 
                        "ada_restrooms", "ada_trails", "ada_water_access"]:
                if key in p:
                    row[key] = str(p[key])
                else:
                    row[key] = ""
                    
            for key in ["rv_sites_count", "tent_sites_count", "max_rig_length_ft"]:
                if key in p:
                    row[key] = str(p[key]) if p[key] > 0 else ""
                    
            row["state"] = state_code
            row["scraped_at"] = "2026-06-03 18:00:00"
            records.append(row)
            
        with open(csv_filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=HEADERS)
            writer.writeheader()
            writer.writerows(records)
            
        print(f"  Created {csv_filename} with {len(records)} parks.")
        
    return 0

if __name__ == "__main__":
    main()
