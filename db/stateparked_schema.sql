-- ============================================================================
-- StateParked — Supabase schema: public.parks
-- Version 1.0  (2026-07-16)
--
-- Design goals:
--   1. Stable primary key + human-readable slug (NOT the URL as the key).
--   2. Reservation/official URLs are CURATED and PROTECTED — automated
--      re-scrapes must never overwrite them (see the upsert example at bottom).
--   3. Provenance on every row: where a fact came from, when it was verified,
--      and whether it was confirmed vs. inferred.
--   4. Geo-ready for "campgrounds near me" (PostGIS).
--   5. Safe for a mobile app to read with the public anon key (RLS).
--
-- Run this in the Supabase SQL editor, or as a migration.
-- ============================================================================

-- --- Extensions -------------------------------------------------------------
create extension if not exists postgis;      -- geography type + distance queries

-- --- Enum-ish reference via CHECK/text[] ------------------------------------
-- We use text[] for multi-value fields (camping types, hookups, activities)
-- to stay flexible as new categories appear. Validate in the app layer.

-- --- Main table -------------------------------------------------------------
create table if not exists public.parks (
    -- Identity ----------------------------------------------------------------
    id                bigint generated always as identity primary key,
    slug              text        not null unique,   -- stable key, e.g. 'al-gulf-state-park'
    name              text        not null,
    state             text        not null,          -- 2-letter code, e.g. 'AL'
    park_system       text,                           -- e.g. 'Alabama State Parks'

    -- Location ----------------------------------------------------------------
    address           text,
    city              text,
    county            text,
    zip               text,
    latitude          double precision,
    longitude         double precision,
    -- Generated geography point for fast distance queries (null if no coords).
    geo               geography(Point, 4326)
                        generated always as (
                          case
                            when longitude is not null and latitude is not null
                            then st_setsrid(st_makepoint(longitude, latitude), 4326)::geography
                          end
                        ) stored,

    -- Contact -----------------------------------------------------------------
    phone_general     text,
    phone_camping     text,
    email             text,

    -- URLs (CURATED / PROTECTED — see upsert rules) ---------------------------
    official_url      text,
    reservation_url   text unique,                    -- hard-won; unique to avoid dupes
    map_url           text,

    -- Camping specifications --------------------------------------------------
    camping_types     text[]  default '{}',           -- {rv, tent, primitive, cabin, group}
    total_sites       integer,
    rv_sites          integer,
    tent_sites        integer,
    max_rig_length_ft integer,
    hookup_types      text[]  default '{}',           -- {none, electric, water, sewer, full}
    amp_service       text[]  default '{}',           -- {20, 30, 50}

    -- Amenities (booleans; extend via `amenities` jsonb for anything unmodeled)
    has_dump_station  boolean,
    has_showers       boolean,
    has_restrooms     boolean,
    has_potable_water boolean,
    has_laundry       boolean,
    has_wifi          boolean,
    has_cell_service  boolean,
    is_ada_accessible boolean,
    allows_pets       boolean,
    amenities         jsonb   default '{}'::jsonb,     -- flexible bag for extras

    -- Activities --------------------------------------------------------------
    activities        text[]  default '{}',           -- {hiking, fishing, boating, swimming, biking, ...}

    -- Ratings -----------------------------------------------------------------
    rating            numeric(2,1),                   -- 0.0 - 5.0
    rating_count      integer default 0,

    -- Operations --------------------------------------------------------------
    season            text,                           -- e.g. 'Year-round', 'Mar-Oct'
    is_open           boolean,
    notes             text,

    -- Provenance & data quality ----------------------------------------------
    data_source       text,                           -- 'alapark_scrape', 'ridb_api', 'osm', 'manual'
    source_url        text,                           -- page/endpoint the data came from
    curated           boolean not null default false, -- true = a human verified this row
    -- Per-field confidence: mark which fields are 'confirmed' vs 'inferred'.
    -- e.g. {"hookup_types": "confirmed", "has_wifi": "inferred"}
    field_status      jsonb   default '{}'::jsonb,
    last_verified     timestamptz,

    -- Timestamps --------------------------------------------------------------
    created_at        timestamptz not null default now(),
    updated_at        timestamptz not null default now()
);

-- --- Indexes ----------------------------------------------------------------
create index if not exists parks_state_idx    on public.parks (state);
create index if not exists parks_geo_idx      on public.parks using gist (geo);
create index if not exists parks_camping_idx  on public.parks using gin (camping_types);
create index if not exists parks_activities_idx on public.parks using gin (activities);

-- --- Keep updated_at current ------------------------------------------------
create or replace function public.set_updated_at()
returns trigger language plpgsql
set search_path = public as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists parks_set_updated_at on public.parks;
create trigger parks_set_updated_at
  before update on public.parks
  for each row execute function public.set_updated_at();

-- ============================================================================
-- Row Level Security
--   Mobile app reads with the public ANON key  -> allow SELECT to everyone.
--   Writes (scrapers, curation) use the SERVICE ROLE key, which bypasses RLS.
-- ============================================================================
alter table public.parks enable row level security;

drop policy if exists parks_public_read on public.parks;
create policy parks_public_read
  on public.parks
  for select
  to anon, authenticated
  using (true);

-- (No insert/update/delete policies => only the service role can write.)

-- ============================================================================
-- "Campgrounds near me" helper — distance in meters, sorted nearest first.
--   select * from public.parks_near(30.25, -87.70, 80000);  -- 80 km radius
-- ============================================================================
create or replace function public.parks_near(
    lat double precision,
    lng double precision,
    radius_m double precision default 80000
)
returns table (id bigint, name text, state text, distance_m double precision)
language sql stable
set search_path = public as $$
  select p.id, p.name, p.state,
         st_distance(p.geo, st_setsrid(st_makepoint(lng, lat), 4326)::geography) as distance_m
  from public.parks p
  where p.geo is not null
    and st_dwithin(p.geo, st_setsrid(st_makepoint(lng, lat), 4326)::geography, radius_m)
  order by distance_m;
$$;

-- ============================================================================
-- UPSERT PATTERN — refresh volatile data WITHOUT clobbering curated URLs.
--
-- Scrapers should upsert on `slug`. The DO UPDATE list REFRESHES scraped
-- fields but DELIBERATELY OMITS: reservation_url, official_url, curated,
-- field_status, and last_verified. So a re-scrape can never overwrite a
-- reservation link you manually found and verified.
--
-- COALESCE lets a scraper fill a URL only if it is currently NULL (first
-- discovery) while never overwriting an existing value.
-- ============================================================================
-- Example (values would come from your Python pipeline):
--
-- insert into public.parks
--   (slug, name, state, phone_camping, total_sites, hookup_types,
--    reservation_url, data_source, source_url)
-- values
--   ('al-gulf-state-park', 'Gulf State Park', 'AL', '251-948-7275', 496,
--    '{full}', 'https://reserve.alapark.com/...', 'alapark_scrape',
--    'https://alapark.com/parks/gulf-state-park')
-- on conflict (slug) do update set
--   name          = excluded.name,
--   phone_camping = excluded.phone_camping,
--   total_sites   = excluded.total_sites,
--   hookup_types  = excluded.hookup_types,
--   data_source   = excluded.data_source,
--   source_url    = excluded.source_url,
--   -- fill URL ONLY if we don't already have one; never overwrite a curated value:
--   reservation_url = coalesce(public.parks.reservation_url, excluded.reservation_url)
--   -- NOTE: official_url, curated, field_status, last_verified intentionally NOT touched.
-- ;
--
-- ============================================================================
-- FUTURE OPTION (not created here): a separate `park_overrides` table holding
-- only human-curated values, merged over scraped data via a view. Cleaner
-- separation once curation volume grows — ask when you want it.
-- ============================================================================


-- ############################################################################
-- PART 2 — ACCOUNTS SCAFFOLD (profiles + saved data)
--
-- Ties to Supabase's built-in auth.users. Accounts stay dormant until you
-- enable auth in the app. All user data is RLS-locked so each person can only
-- see/edit their own rows. None of this touches the parks data scrapers write.
-- ############################################################################

-- --- Profiles: 1:1 with auth.users -----------------------------------------
create table if not exists public.profiles (
    id             uuid primary key references auth.users(id) on delete cascade,
    display_name   text,
    home_state     text,
    rig_type       text,                    -- tent, travel_trailer, fifth_wheel, class_a/b/c, van, popup
    rig_length_ft  integer,
    hookup_needs   text[]  default '{}',    -- {electric, water, sewer, full}
    preferences    jsonb   default '{}'::jsonb,
    created_at     timestamptz not null default now(),
    updated_at     timestamptz not null default now()
);

-- --- Favorites --------------------------------------------------------------
create table if not exists public.saved_parks (
    id         bigint generated always as identity primary key,
    user_id    uuid   not null references auth.users(id) on delete cascade,
    park_id    bigint not null references public.parks(id) on delete cascade,
    created_at timestamptz not null default now(),
    unique (user_id, park_id)
);

-- --- Trips + ordered stops with dates --------------------------------------
create table if not exists public.trips (
    id         bigint generated always as identity primary key,
    user_id    uuid   not null references auth.users(id) on delete cascade,
    name       text   not null,
    start_date date,
    end_date   date,
    notes      text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.trip_stops (
    id             bigint generated always as identity primary key,
    trip_id        bigint not null references public.trips(id) on delete cascade,
    park_id        bigint not null references public.parks(id) on delete cascade,
    position       integer,
    arrival_date   date,
    departure_date date,
    notes          text,
    created_at     timestamptz not null default now()
);

-- --- Private notes + personal rating (1 per user per park) ------------------
create table if not exists public.park_notes (
    id              bigint generated always as identity primary key,
    user_id         uuid   not null references auth.users(id) on delete cascade,
    park_id         bigint not null references public.parks(id) on delete cascade,
    note            text,
    personal_rating numeric(2,1),
    created_at      timestamptz not null default now(),
    updated_at      timestamptz not null default now(),
    unique (user_id, park_id)
);

-- --- Indexes ----------------------------------------------------------------
create index if not exists saved_parks_user_idx on public.saved_parks (user_id);
create index if not exists trips_user_idx        on public.trips (user_id);
create index if not exists trip_stops_trip_idx   on public.trip_stops (trip_id);
create index if not exists park_notes_user_idx   on public.park_notes (user_id);

-- --- updated_at triggers -----------------------------------------------------
drop trigger if exists profiles_set_updated_at on public.profiles;
create trigger profiles_set_updated_at before update on public.profiles
  for each row execute function public.set_updated_at();
drop trigger if exists trips_set_updated_at on public.trips;
create trigger trips_set_updated_at before update on public.trips
  for each row execute function public.set_updated_at();
drop trigger if exists park_notes_set_updated_at on public.park_notes;
create trigger park_notes_set_updated_at before update on public.park_notes
  for each row execute function public.set_updated_at();

-- --- Auto-create a profile on signup ---------------------------------------
create or replace function public.handle_new_user()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into public.profiles (id, display_name)
  values (new.id, new.raw_user_meta_data->>'display_name')
  on conflict (id) do nothing;
  return new;
end;
$$;
-- Trigger function only; must NOT be callable directly via the API:
revoke execute on function public.handle_new_user() from anon, authenticated;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- --- RLS: each user sees/edits ONLY their own rows -------------------------
alter table public.profiles    enable row level security;
alter table public.saved_parks enable row level security;
alter table public.trips       enable row level security;
alter table public.trip_stops  enable row level security;
alter table public.park_notes  enable row level security;

drop policy if exists profiles_own on public.profiles;
create policy profiles_own on public.profiles for all to authenticated
  using (auth.uid() = id) with check (auth.uid() = id);

drop policy if exists saved_parks_own on public.saved_parks;
create policy saved_parks_own on public.saved_parks for all to authenticated
  using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists trips_own on public.trips;
create policy trips_own on public.trips for all to authenticated
  using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists park_notes_own on public.park_notes;
create policy park_notes_own on public.park_notes for all to authenticated
  using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists trip_stops_own on public.trip_stops;
create policy trip_stops_own on public.trip_stops for all to authenticated
  using (exists (select 1 from public.trips t
                 where t.id = trip_stops.trip_id and t.user_id = auth.uid()))
  with check (exists (select 1 from public.trips t
                      where t.id = trip_stops.trip_id and t.user_id = auth.uid()));
-- ############################################################################
