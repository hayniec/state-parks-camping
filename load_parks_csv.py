#!/usr/bin/env python3
"""
StateParked — CSV -> parks loader / SQL generator.

Maps the alapark-style scraper CSV into the Supabase `public.parks` schema and
emits an idempotent UPSERT keyed on `slug`. The UPSERT REFRESHES volatile data
but NEVER overwrites curated URL columns (reservation_url, official_url) — that
is the "protect the hard-won URL" rule from the roadmap.

Usage:
    python load_parks_csv.py INPUT.csv > load.sql     # generate SQL
Then run load.sql against your project (psql with the service-role connection
string, or the Supabase SQL editor).

Boolean rule: 'True' -> true, 'False' -> false, '' -> NULL (unknown).
Empty reservation_url -> NULL (so blanks don't collide on the UNIQUE constraint).
"""
import csv, sys

# --- SQL literal helpers ----------------------------------------------------
def q(v):
    """Quote a text value, or NULL."""
    if v is None or v == "":
        return "NULL"
    return "'" + str(v).replace("'", "''") + "'"

def b(v):
    """Boolean-ish: 'True'/'False'/'' -> true/false/NULL."""
    if v == "True":  return "true"
    if v == "False": return "false"
    return "NULL"

def i(v):
    if v is None or v == "":
        return "NULL"
    try:
        return str(int(float(v)))
    except ValueError:
        return "NULL"

def num(v):
    if v is None or v == "":
        return "NULL"
    try:
        return str(float(v))
    except ValueError:
        return "NULL"

def arr(items):
    """text[] literal from a python list of strings."""
    if not items:
        return "'{}'"
    inner = ",".join('"' + s.replace('"', '\\"') + '"' for s in items)
    return "'{" + inner + "}'"

def jsonb(d):
    import json
    clean = {k: v for k, v in d.items() if v not in (None, "", [])}
    if not clean:
        return "'{}'::jsonb"
    return q(json.dumps(clean)) + "::jsonb"

def truthy(v):
    return v == "True"

# --- Row transform ----------------------------------------------------------
def transform(r):
    camping_types = []
    if truthy(r.get("has_rv_camping")):   camping_types.append("rv")
    if truthy(r.get("has_tent_camping")): camping_types.append("tent")
    if truthy(r.get("primitive_camping")):camping_types.append("primitive")

    hookup_types = []
    if truthy(r.get("electric_30amp")) or truthy(r.get("electric_50amp")):
        hookup_types.append("electric")
    if truthy(r.get("water_hookup")):  hookup_types.append("water")
    if truthy(r.get("sewer_hookup")):  hookup_types.append("sewer")
    if truthy(r.get("full_hookups")):  hookup_types.append("full")

    amp = []
    if truthy(r.get("electric_30amp")): amp.append("30")
    if truthy(r.get("electric_50amp")): amp.append("50")

    activities = []
    for src, name in [("hiking","hiking"),("fishing","fishing"),
                      ("swimming","swimming"),("boat_ramp","boating"),
                      ("golf","golf")]:
        if truthy(r.get(src)): activities.append(name)

    # ADA: True if any ADA signal true; False if all explicit False; else NULL
    ada_vals = [r.get("ada_sites"), r.get("ada_restrooms"),
                r.get("ada_trails"), r.get("ada_water_access")]
    if any(v == "True" for v in ada_vals):
        ada = "true"
    elif any(v == "False" for v in ada_vals):
        ada = "false"
    else:
        ada = "NULL"

    notes = "; ".join(x for x in [r.get("seasonal_notes"), r.get("cell_signal_notes")] if x)

    extras = {
        "google_place_id": r.get("google_place_id") or None,
        "pull_through": truthy(r.get("pull_through_available")) or None,
        "waterfront_sites": truthy(r.get("waterfront_sites")) or None,
        "lake_river_access": truthy(r.get("lake_river_access")) or None,
        "ada_trails": True if r.get("ada_trails") == "True" else None,
        "ada_water_access": True if r.get("ada_water_access") == "True" else None,
        "subratings": {k: r.get(k) for k in (
            "rating_site_quality","rating_hookup_reliability","rating_cleanliness",
            "rating_scenery","rating_connectivity","rating_noise","rating_value")
            if r.get(k)} or None,
    }

    field_status = {"amenities": "inferred", "rating": "google"}

    return {
        "slug": r["park_slug"], "name": r["park_name"], "state": r["state"],
        "park_system": "Alabama State Parks",
        "address": r.get("address"),
        "latitude": num(r.get("latitude")), "longitude": num(r.get("longitude")),
        "phone_general": r.get("phone_general"),
        "phone_camping": r.get("phone_camping"),
        "official_url": r.get("park_url"),
        "reservation_url": r.get("reservation_url") or None,  # NULL if blank
        "map_url": r.get("google_maps_url"),
        "camping_types": camping_types, "hookup_types": hookup_types, "amp_service": amp,
        "total_sites": i(r.get("rv_sites_count")),  # only RV count available
        "rv_sites": i(r.get("rv_sites_count")),
        "tent_sites": i(r.get("tent_sites_count")),
        "max_rig_length_ft": i(r.get("max_rig_length_ft")),
        "has_dump_station": b(r.get("dump_station")),
        "has_showers": b(r.get("showers")),
        "has_laundry": b(r.get("laundry")),
        "has_wifi": b(r.get("wifi")),
        "allows_pets": b(r.get("pet_friendly")),
        "is_ada_accessible": ada,
        "activities": activities,
        "amenities": extras,
        "rating": num(r.get("google_rating")),
        "rating_count": i(r.get("google_review_count")),
        "notes": notes,
        "data_source": "alapark_scrape",
        "source_url": r.get("park_url"),
        "field_status": field_status,
        "last_verified": r.get("scraped_at"),
    }

# --- Emit SQL ---------------------------------------------------------------
COLS = ["slug","name","state","park_system","address","latitude","longitude",
        "phone_general","phone_camping","official_url","reservation_url","map_url",
        "camping_types","hookup_types","amp_service","total_sites","rv_sites",
        "tent_sites","max_rig_length_ft","has_dump_station","has_showers",
        "has_laundry","has_wifi","allows_pets","is_ada_accessible","activities",
        "amenities","rating","rating_count","notes","data_source","source_url",
        "field_status","last_verified"]

# Columns refreshed on conflict — note: reservation_url, official_url, curated,
# field_status are intentionally EXCLUDED so re-loads never clobber curated data.
REFRESH = ["name","state","park_system","address","latitude","longitude",
           "phone_general","phone_camping","map_url","camping_types","hookup_types",
           "amp_service","total_sites","rv_sites","tent_sites","max_rig_length_ft",
           "has_dump_station","has_showers","has_laundry","has_wifi","allows_pets",
           "is_ada_accessible","activities","amenities","rating","rating_count",
           "notes","data_source","source_url","last_verified"]

def fmt(t, col):
    v = t[col]
    if col in ("latitude","longitude","rating"):                       return v  # already num()/NULL
    if col in ("total_sites","rv_sites","tent_sites","max_rig_length_ft","rating_count"): return v
    if col in ("has_dump_station","has_showers","has_laundry","has_wifi",
               "allows_pets","is_ada_accessible"):                      return v  # true/false/NULL
    if col in ("camping_types","hookup_types","amp_service","activities"): return arr(v)
    if col in ("amenities","field_status"):                            return jsonb(v)
    if col == "last_verified":                                         return q(v) + "::timestamptz" if v else "NULL"
    return q(v)

def main():
    reader = csv.DictReader(open(sys.argv[1]))
    rows = [transform(r) for r in reader]
    values = []
    for t in rows:
        vals = ", ".join(fmt(t, c) for c in COLS)
        values.append(f"  ({vals})")
    set_clause = ",\n  ".join(f"{c} = excluded.{c}" for c in REFRESH)
    # protect reservation_url: only fill if currently NULL
    set_clause += ",\n  reservation_url = coalesce(public.parks.reservation_url, excluded.reservation_url)"
    print(f"insert into public.parks ({', '.join(COLS)}) values")
    print(",\n".join(values))
    print(f"on conflict (slug) do update set\n  {set_clause};")

if __name__ == "__main__":
    main()
