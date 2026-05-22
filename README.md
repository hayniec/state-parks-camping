# Campground Discovery App

A personal project (with potential to become a business) to build a discovery
tool for campgrounds across the US, with an initial focus on **state park RV
and tent campgrounds**. Discovery only — no bookings handled by the app;
users are linked out to the official reservation systems.

## Vision

- **Long-term:** searchable database of campgrounds across all 50 states,
  filterable by location and amenities, with ratings.
- **Phase 1 (current):** Alabama state parks only. Build the data pipeline,
  schema, and prove the model on a small, manageable dataset.
- **Phase 2:** expand to neighboring states (GA, FL, TN, MS), refine the app UI.
- **Phase 3:** federal lands (via Recreation.gov RIDB API) and additional
  state systems.
- **Out of scope (for now):** private RV parks (KOA, Good Sam, etc.) and
  online bookings.

## Design Decisions Made So Far

1. **Discovery only**, no bookings. We link out to reservation systems
   (e.g. `reserve.alapark.com`) rather than handle payments ourselves.
2. **State parks first** — they're publicly funded (data is accessible),
   geographically distributed, RV-friendly, and underserved by existing apps
   that lean toward private parks or federal lands.
3. **Alabama is the first state** — about 21 parks, the user lives there
   and can ground-truth the data, and the site (alapark.com) is a fairly
   standard Drupal 10 site that's scrapeable.
4. **Ratings via Google Places API**, not scraped reviews. Display the star
   rating from `places.googleapis.com`, make it a link to the Google Maps
   listing for the full reviews. Stays within Google's TOS. Pull the
   `place_id` once per park, fetch live rating on demand (the API has
   generous free credit and we'd be making pennies of requests).
5. **Two camping flags**, not one — `has_rv_camping` and `has_tent_camping`
   are tracked separately so users can filter for either or both. Many parks
   have both; one boolean would oversimplify.
6. **Scraper is gentle** — 2-second delay between requests, identifying
   User-Agent, public data only.

## Current State

- `scrape_alabama_parks.py` exists — fetches the 21 Alabama parks from
  alapark.com, extracts address, phones, sub-page links, and the raw
  description/campground text. Includes best-effort keyword inference for
  amenities (full hookups, pull-through, ADA, etc.).
- Tested against a Gulf State Park HTML fixture; parsing works correctly.
- **Has NOT been run live yet** — that's the next step.
- **Needs tent camping support added** — currently only flags RV camping.

## Schema (in `ParkRecord` dataclass)

Identity, location, contact, RV/camping fields, amenities, features,
operations, ratings (8 dimensions: overall, site quality, hookup reliability,
cleanliness, scenery, connectivity, noise, value), Google Places fields
(place_id, maps URL, rating, review count), and raw text fallback.

## Immediate Next Steps

1. **Add tent camping support to the scraper:**
   - Add `has_tent_camping`, `tent_sites_count`, `primitive_camping` fields
     to `ParkRecord`.
   - Extend `infer_amenities()` with tent keyword detection
     ("primitive", "tent-only", "tent sites", "walk-in").
   - Remove the `KNOWN_NO_RV` skip behavior — all parks should be scraped
     since a park with no RV camping may still have tent camping.
   - Rename the RV-specific count regex so it doesn't accidentally match
     tent-site counts.

2. **Run the scraper live** against alapark.com and inspect the CSV.

3. **Geocoding script** — convert addresses to lat/long so the app can do
   "near me" search. Free options: Nominatim (OpenStreetMap) for low volume,
   or the Google Geocoding API.

4. **Google Places lookup script** — for each park, find the `place_id` via
   the Places API text search. Store in CSV. Then a separate flow fetches
   the live rating at app runtime.

5. **First app prototype** — likely a simple React + map (Leaflet/Mapbox)
   that reads the CSV and renders filterable markers.

## Tech Notes

- Language: Python 3.10+ for data pipeline, dependencies in
  `requirements.txt` (`requests`, `beautifulsoup4`).
- Data format: CSV is the working format for now — easy to inspect, edit,
  and share. Will migrate to SQLite or Postgres once schema stabilizes and
  the app needs queries.
- The site is Drupal 10; pages are reliably structured with a
  `#main-content` region. Hosted at `alapark.com` (Alabama state government).

## Things to Watch

- **Keyword inference is best-effort.** The CSV always preserves
  `description_text` and `campground_text` so we can hand-verify or
  re-process. Don't trust the boolean flags blindly.
- **Site count regex is greedy** — first matching number wins, which can
  pick up unrelated counts. Verify by hand.
- **Google Places caching limit:** ratings can't be cached more than 30 days
  per their TOS. App should fetch live or refresh on a schedule.
- **Some "parks" in the alapark.com nav aren't traditional state parks**
  (e.g. Lake Jackson RV Park at Florala). Worth keeping but noting.
