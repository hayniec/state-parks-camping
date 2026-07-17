# StateParked — Product Roadmap & App Store Playbook

**A living planning document.** Use it to guide decisions, capture new ideas, and prepare everything the Apple App Store and Google Play will ask for.

- **Owner:** Eric Haynie
- **Repo:** github.com/hayniec/state-parks-camping
- **Last updated:** 2026-07-16
- **Version:** 1.2
- **Status:** Planning → early build (database foundation live, Alabama data loaded)

> **How to use this document.** This is meant to be edited. When your thinking changes, change the doc — don't work around it. Three sections are built for that: **§9 Ideas & Backlog** (drop new ideas here anytime, no need to slot them perfectly), **§10 Decision Log** (record *why* you chose something, so future-you and any collaborators understand the reasoning), and **§11 Changelog** (bump the version and note what changed). Keep the file in your repo so it versions alongside the code and you can edit it in Antigravity or anywhere else.

---

## 1. Product Vision

**StateParked** is a discovery tool for U.S. state-park campgrounds — RV and tent — that helps people find the right place to camp by location and amenities, then sends them to the official site to book. It does **not** handle reservations itself; it links out to each park's official reservation system. The experience centers on an interactive map, a filterable list, and a rich detail view per campground.

**Who it's for:** RV owners and tent campers planning trips who want to filter by what actually matters to them — hookups, rig length, dump stations, connectivity, activities, accessibility — without digging through 50 different state websites.

**What makes it worth using:** One consistent, well-filtered, trustworthy view across states that are otherwise scattered across wildly inconsistent official sites. The value is in the *aggregation and filtering*, and in the data being *accurate*.

**North-star principle:** Accuracy over coverage. A smaller set of parks with correct, verified data beats a large set with guessed data. An app that says a site has full hookups when it doesn't is worse than an app that stays quiet.

---

## 2. Current State (as of 2026-07-16)

Built in Antigravity, the current app is a **Progressive Web App (PWA)**, not yet a native store app:

- **Frontend:** vanilla HTML / CSS / JavaScript. Leaflet for the map, PapaParse to read CSV data at load time, Lucide for icons. Installable via `manifest.json` + service worker (`sw.js`), dark theme, portrait, standalone.
- **Data pipeline (Python):**
  - `scrape_alabama_parks.py` — `requests` + BeautifulSoup scraper for alapark.com. ~50 fields, largely by keyword inference over page text. Fragile but functional.
  - `generate_new_states.py` — **hardcoded** data for HI, ID, IL, IN, IA. Not scraped; entered directly in the file. **Accuracy risk — flagged for replacement.**
  - `geocode_parks.py` — Google Geocoding with Nominatim/OSM fallback, two-stage lookup, rate limiting, caching, CSV backups. **Well-built; keep.**
- **Data storage:** CSV files committed in the repo, parsed in the browser.

**Reachability note:** The Anthropic cloud workspace can't `git clone`/push directly (outbound git is blocked). Sync happens through GitHub — commit from Antigravity, and code/assets produced here get committed back by you or via the GitHub connector when enabled in-chat.

---

## 3. Target Architecture (the decision)

**Decision:** Rebuild the app natively as **React Native + Expo (TypeScript)**, keep the Python data pipeline, and move data into **Supabase**.

**Why React Native + Expo:**
- The current app is already JavaScript, so React Native reuses that familiarity; Flutter would mean learning Dart from scratch.
- Expo removes the hardest parts of native dev — building iOS/Android binaries and submitting to the stores — via cloud builds (EAS), which suits a solo/part-time developer.
- A real native app (with native map + location) comfortably clears Apple's "minimum functionality / not just a website" review bar, which a wrapped web view can stumble on.

**Map:** `react-native-maps` (Apple/Google Maps native) replaces Leaflet. Consider MapLibre if you want vector/offline map tiles later.

**What carries over vs. what gets rebuilt:**

| Carries over unchanged | Gets rebuilt / migrated |
|---|---|
| Entire Python data pipeline (scrape, geocode, expand) | UI layer: HTML/CSS → React Native components |
| Product design: features, filter scheme, IA | Map: Leaflet → react-native-maps |
| Branding, icons, dark theme, color palette | Data loading: browser CSV/PapaParse → bundled JSON or Supabase fetch |
| Reservation-link-out model (no in-app booking) | "Installable PWA" → real store binaries |

**Optional:** keep the PWA live as the web version — the two can coexist and share the Supabase data source.

---

## 4. Data Strategy

### 4.1 Source of truth: Supabase

Move data out of repo CSVs into a Supabase Postgres database. Benefits: fix/add data without shipping an app update, one canonical schema, protected curated fields, and free user auth if you add favorites later.

### 4.2 Protecting hard-won URLs (the upsert pattern)

Reservation URLs are manually found and precious. Rather than making the URL the primary key (URLs are long and can change), use a **stable key** and protect the URL as a column:

- Primary key: `id` (serial/uuid) plus a stable `slug` (e.g., `al-gulf-state-park`) or a unique natural key (`state` + `name`).
- `reservation_url` and `official_url` stored as columns; add a `UNIQUE` constraint on `reservation_url` to prevent duplicates.
- **Re-scrapes upsert on the stable key and refresh volatile fields (phone, amenities, site counts) but explicitly exclude the curated URL columns** — so an automated run never clobbers a link you worked to find. In Postgres: `INSERT ... ON CONFLICT (slug) DO UPDATE SET ...` listing only the columns to refresh.
- Provenance columns on every park: `data_source`, `last_verified` (timestamp), `curated` (boolean), and per-field `*_confirmed` flags where a value was inferred vs. verified.

### 4.3 Better data sourcing (hybrid, tiered)

There is no universal 50-state scraper — every state site differs. Use tiers:

1. **Structured APIs first (reliable, free where noted):**
   - **Recreation.gov RIDB API** — federal campgrounds + some state data.
   - **OpenStreetMap Overpass API** — campgrounds tagged with amenities; query by state bounding box. Free, structured.
   - **State open-data / ArcGIS REST endpoints** — many states publish clean campground GIS datasets.
   - **Google Places API** — ratings, phone, hours.
2. **Targeted scraping second** — only for fields the structured sources lack, per state.
3. **Manual curation third** — the reservation URL and any hand-verified facts, protected from overwrite.

**Priority fix:** replace `generate_new_states.py`'s hardcoded data with sourced data before those states go live. Reconcile the two field schemas (~50 in Alabama, ~54 in the generator) into one canonical schema.

### 4.4 Accounts & user profiles (built 2026-07-16)

Accounts use **Supabase Auth** (built-in) — email/password, magic link, plus Sign in with Apple/Google. No custom auth to build. The account data model is already created and dormant until we switch auth on in the app; it's fully additive and never interferes with scraper writes. Every user table is row-level-security-locked so a person can only read/edit their own rows.

- `profiles` — 1:1 with `auth.users`; display name, home state, and rig info (`rig_type`, `rig_length_ft`, `hookup_needs`) so filters can default to what fits the user. Auto-created on signup via trigger.
- `saved_parks` — favorites (user ↔ park).
- `trips` + `trip_stops` — named trips with dates and an ordered list of park stops.
- `park_notes` — private per-park notes and a personal rating (one per user per park).

**Live connection details** (safe to ship in the app; RLS makes the publishable key read-only for park data and self-only for user data):
- Project URL: `https://tdcoqzojdqxyvjmskiff.supabase.co`
- Publishable key: `sb_publishable_ccaFeObNyUEzG-vLNqiOKg_ur8NtSyG`
- Service-role key (scrapers, server-side only): get from Supabase dashboard → Project Settings → API. **Never ship this in the app.**

---

## 5. Phased Roadmap

Each phase lists a goal, key tasks, and what "done" looks like. Check items off as you go.

### Phase 0 — Foundation
**Goal:** Data foundation + project scaffold ready.
- [x] Design & create the Supabase `parks` schema (stable key, protected URL, provenance columns). *Done 2026-07-16 — project `stateparked`, us-east-2.*
- [x] Create account-ready scaffold: `profiles`, `saved_parks`, `trips`, `trip_stops`, `park_notes`, all RLS-locked. *Done 2026-07-16 (see §4.4).*
- [x] Migrate Alabama (real) data into Supabase; reconcile canonical field schema. *Done 2026-07-16 — 22 parks loaded via `load_parks_csv.py`; all geocoded, 18 with reservation URLs, avg rating 4.54.*
- [ ] Scaffold the Expo (TypeScript) project; confirm it runs on your phone via Expo Go.
- [x] Apple Developer account ($99/yr) — *already have.*
- [x] Google Play Developer account ($25 one-time) — *already have.*

**Done when:** Alabama data lives in Supabase and a blank Expo app runs on a real device.

### Phase 1 — Feature Parity (MVP)
**Goal:** Recreate today's web app as a native app against real data.
- [ ] Map screen (react-native-maps) with campground pins.
- [ ] List view + map/list toggle.
- [ ] State selector / location search.
- [ ] Filter panel: camping type, capacity, rating, amenities, connectivity, activities, accessibility.
- [ ] Detail drawer: specs, ratings, contact, official + reservation links (link-out).
- [ ] Data layer reads from Supabase (or bundled JSON for offline).

**Done when:** The native app matches the web app's functionality on your own iPhone and Android device.

### Phase 2 — Native Polish
**Goal:** Use what native gives you.
- [ ] GPS "campgrounds near me" + distance sorting.
- [ ] Map clustering for dense areas.
- [ ] "Directions" → open Apple/Google Maps.
- [ ] Offline data support; graceful loading/empty/error states.
- [ ] Device testing on multiple screen sizes.

**Done when:** The app feels like a native app, not a ported website.

### Phase 3 — Store Submission
**Goal:** Live on both stores. (See §7 for the full checklist.)
- [ ] Produce app icons, screenshots, feature graphic.
- [ ] Write store listings (descriptions, keywords) and privacy policy.
- [ ] EAS build → TestFlight (Apple) + Internal testing (Google) beta.
- [ ] Complete privacy/data-safety/age-rating forms.
- [ ] Submit for review; address feedback; release to production.

**Done when:** StateParked is downloadable from the App Store and Google Play.

### Phase 4 — Expansion & Growth
**Goal:** Scale coverage and depth.
- [ ] Add states via the hybrid data pipeline (structured-source-first).
- [ ] Expand to federal lands (Recreation.gov: national parks, USFS, Corps of Engineers).
- [ ] Consider accounts + saved/favorite campgrounds (Supabase auth).
- [ ] Consider reviews, photos, trip planning, availability alerts (see backlog).

**Done when:** Ongoing — driven by §9 backlog priorities.

---

## 6. Feature List

Doubles as raw material for your store descriptions. Keep it current — it's your canonical answer to "what does the app do?"

### 6.1 MVP (current + Phase 1)
- Interactive map of state-park campgrounds with tappable pins.
- List view with map/list toggle.
- Search / filter by state and location.
- Filtering by: camping type (RV / tent / primitive), site capacity, rating, amenities (hookups, dump station, showers, restrooms, potable water, laundry), connectivity (cell / Wi-Fi), activities (hiking, fishing, boating, swimming), accessibility (ADA).
- Campground detail view: site specs (count, max rig length, hookup types), ratings, contact info, official website, and direct link to the official reservation system.
- Links out to official booking — no in-app reservations.
- Dark theme; offline-capable data.

### 6.2 Near-term (Phase 2)
- GPS "near me" and distance-based sorting.
- Map pin clustering.
- One-tap directions via native maps.
- Weather at/near a campground.

### 6.3 Backlog / future (Phase 4+) — see §9 for the running idea list
- User accounts and saved/favorite campgrounds.
- Trip planning (multi-stop routes).
- User reviews, ratings, and photos.
- Real-time availability via reservation APIs (e.g., Recreation.gov).
- Availability / cancellation alerts (push notifications).
- Federal-lands coverage (national parks, USFS, COE).
- Offline vector maps.

---

## 7. App Store Submission Requirements

You already have both developer accounts. This is the full list of what each store requires so nothing surprises you at submission. Build binaries with **Expo EAS** (`.ipa` for Apple, `.aab` for Google).

### 7.1 Shared assets to prepare (needed for both)
- [ ] **App icon** — high-res source (1024×1024) to generate all sizes.
- [ ] **Screenshots** — captured on real device sizes (see per-store specs below).
- [ ] **Privacy policy** — a hosted URL. *Required by both.* (I can draft this.)
- [ ] **Support/contact** — a support URL and support email.
- [ ] **App name, description, keywords/short description** (see §6 for source material).
- [ ] **Category** — Travel or Navigation.
- [ ] **Age rating** answers (no objectionable content → lowest rating).

### 7.2 Apple App Store (App Store Connect)
- [ ] App record created; bundle ID registered.
- [ ] **Name** (30 char), **subtitle** (30 char), **promotional text** (170 char), **description** (up to 4000 char), **keywords** (100 char total).
- [ ] **App icon** 1024×1024 (no alpha/transparency).
- [ ] **Screenshots**: 6.7" and 6.5" iPhone required; 5.5" if supporting older devices; iPad sizes if iPad-enabled.
- [ ] **App preview video** (optional).
- [ ] **Privacy Policy URL** (required).
- [ ] **App Privacy** "nutrition label" — declare what data you collect and why (likely: coarse location for "near me"; none if you don't collect accounts).
- [ ] **Age rating** questionnaire.
- [ ] **Export compliance** (encryption) — typically "uses standard encryption only."
- [ ] **Sign-in info** for reviewers if any login exists (none at MVP).
- [ ] **TestFlight** beta before production.
- [ ] Compliance with **App Review Guideline 4.2** (minimum functionality) — the native map + location features satisfy this.

### 7.3 Google Play (Play Console)
- [ ] App created; package name set.
- [ ] **Title** (30 char), **short description** (80 char), **full description** (4000 char).
- [ ] **App icon** 512×512.
- [ ] **Feature graphic** 1024×500 (required for the store listing).
- [ ] **Screenshots** — at least 2 phone (up to 8); 7"/10" tablet optional.
- [ ] **Category** and contact details.
- [ ] **Privacy Policy URL** (required).
- [ ] **Data safety form** — declare data collection/sharing (mirror the Apple privacy answers).
- [ ] **Content rating** questionnaire (IARC).
- [ ] **Target audience & content** settings.
- [ ] **Ads** declaration (No, unless you add ads).
- [ ] **App access** (any gated features → provide test credentials; none at MVP).
- [ ] **Internal/closed testing** track before production release.
- [ ] Build as **Android App Bundle (.aab)**; enroll in Play App Signing.

### 7.4 Store-listing content checklist (fill these in as you go)
- [ ] App name / title finalized.
- [ ] Short tagline / subtitle.
- [ ] Long description (draft from §6 feature list).
- [ ] Keyword set.
- [ ] 3–8 screenshots showing map, filters, and a detail view.
- [ ] Privacy policy published at a stable URL.
- [ ] Support email + support/marketing URL live.

---

## 8. Roles & Workflow

- **Antigravity** — in-editor coding agent with live repo context; primary place to write/commit React Native code.
- **Claude (here)** — planning, data-source research, Supabase schema/setup, store assets, privacy policy, and generated code/docs handed back for you to commit.
- **GitHub** — the bridge and single source of truth. Commit often; pull before editing in either tool so you never edit the same file in two places at once.

---

## 9. Ideas & Backlog *(add freely — this is the catch-all)*

Drop new ideas here the moment you have them; sort/prioritize later. Suggested tags: `[must]` `[nice]` `[maybe]` `[research]`.

- `[research]` Real-time availability via Recreation.gov / reservation APIs.
- `[nice]` Save/favorite campgrounds (requires accounts).
- `[nice]` Trip planning with multiple stops.
- `[maybe]` User reviews & photos (adds moderation burden).
- `[nice]` Push alerts for availability/cancellations.
- `[nice]` Federal lands expansion (national parks, USFS, COE).
- `[maybe]` Offline vector maps.
- _(your next idea here…)_

---

## 10. Decision Log *(why we chose what we chose)*

| Date | Decision | Rationale | Alternatives considered |
|---|---|---|---|
| 2026-07-16 | Rebuild native with React Native + Expo | Reuses existing JS skills; Expo simplifies builds/store submission; clears Apple 4.2 | Capacitor wrap (fast but web-view); Flutter (new language); stay PWA (no stores) |
| 2026-07-16 | Move data to Supabase | Single source of truth; update data without app releases; protect curated fields; free auth later | Keep CSVs in repo (requires app release to update); bundled JSON only |
| 2026-07-16 | Protect reservation URLs via upsert on stable key | URLs are hand-found and precious; must survive re-scrapes | URL as primary key (fragile — URLs change) |
| 2026-07-16 | Replace hardcoded state data; hybrid sourcing | Accuracy is the north star; invented data is a liability | Keep hardcoding (fast but unreliable) |
| 2026-07-16 | Build accounts scaffold now (dormant) on Supabase Auth | Future-proofs profiles/saved data with zero rebuild; additive; no custom auth needed | Defer entirely (risks schema churn later); build custom auth (unnecessary) |
| 2026-07-16 | Store saved data in per-user RLS tables keyed to auth.users + park id | Isolates user data from scraper writes; each user sees only their own rows | Denormalize into parks (couples user + source data) |

---

## 11. Changelog

- **v1.2 (2026-07-16)** — Loaded 22 real Alabama parks into `public.parks` via the reusable `load_parks_csv.py` loader (protect-the-URL upsert). Verified geo "near me" and all columns. Phase 0 Alabama task checked off.
- **v1.1 (2026-07-16)** — Supabase project `stateparked` created; `parks` schema + accounts scaffold (profiles, saved_parks, trips, trip_stops, park_notes) applied with RLS. Added §4.4 accounts model, connection details, Phase 0 items checked, decision-log entries.
- **v1.0 (2026-07-16)** — Initial roadmap: vision, current-state assessment, native architecture decision, data strategy, phased plan, feature list, app-store checklist, workflow, backlog, decision log.
