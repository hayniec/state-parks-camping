// Force cache flush when app version changes
const CURRENT_VERSION = "stateparked-v21";
if (localStorage.getItem("app_version") !== CURRENT_VERSION) {
  localStorage.setItem("app_version", CURRENT_VERSION);
  if ("caches" in window) {
    caches.keys().then((names) => {
      Promise.all(names.map(name => caches.delete(name))).then(() => {
        if ("serviceWorker" in navigator) {
          navigator.serviceWorker.getRegistrations().then((registrations) => {
            Promise.all(registrations.map(r => r.unregister())).then(() => {
              window.location.reload(true);
            });
          });
        } else {
          window.location.reload(true);
        }
      });
    });
  }
}

// Register Service Worker for PWA Offline support
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker
      .register("./sw.js")
      .then((reg) => {
        console.log("Service Worker registered successfully!");
        reg.onupdatefound = () => {
          const installingWorker = reg.installing;
          if (installingWorker) {
            installingWorker.onstatechange = () => {
              if (installingWorker.state === "installed" && navigator.serviceWorker.controller) {
                console.log("New content available, reloading...");
                window.location.reload();
              }
            };
          }
        };
      })
      .catch((err) => console.warn("Service Worker registration failed:", err));
  });

  // Automatically reload the page when the active service worker changes (e.g., after skipWaiting)
  let refreshing = false;
  navigator.serviceWorker.addEventListener("controllerchange", () => {
    if (!refreshing) {
      refreshing = true;
      window.location.reload();
    }
  });
}

/* ==========================================================================
   State & Constants
   ========================================================================== */
let map;
let allParks = [];
let markersLayer;
let activeMarker = null;
let selectedPark = null;
let userCoords = null;
let userLocationMarker = null;

// CartoDB Tile Layers (Dark Matter and Positron Light)
const TILE_URL_DARK = "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png";
const TILE_URL_LIGHT = "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png";
const TILE_ATTR =
  '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>';
let tileLayerInstance;

// State configurations: Centers, default zoom levels, and CSV filenames
const STATE_CONFIG = {
  ALL: {
    name: "All States",
    center: [39.8283, -98.5795],
    zoom: 4.0,
    csv: "all_state_parks.csv"
  },
  AL: {
    name: "Alabama",
    center: [32.806671, -86.79113],
    zoom: 7.5,
    csv: "alabama_state_parks.csv"
  },
  AK: {
    name: "Alaska",
    center: [63.588753, -154.493062],
    zoom: 4.5,
    csv: "alaska_state_parks.csv"
  },
  AZ: {
    name: "Arizona",
    center: [34.048928, -111.093731],
    zoom: 7.0,
    csv: "arizona_state_parks.csv"
  },
  AR: {
    name: "Arkansas",
    center: [34.799999, -92.199997],
    zoom: 7.5,
    csv: "arkansas_state_parks.csv"
  },
  CA: {
    name: "California",
    center: [36.7783, -119.4179],
    zoom: 6.0,
    csv: "california_state_parks.csv"
  },
  CO: {
    name: "Colorado",
    center: [39.5501, -105.7821],
    zoom: 7.0,
    csv: "colorado_state_parks.csv"
  },
  CT: {
    name: "Connecticut",
    center: [41.6032, -72.6999],
    zoom: 9.0,
    csv: "connecticut_state_parks.csv"
  }
};
let activeState = "ALL";

/* ==========================================================================
   Map & Application Initialization
   ========================================================================== */
document.addEventListener("DOMContentLoaded", () => {
  // Load saved accessibility mode before initializing layout/map
  if (localStorage.getItem("accessibilityMode") === "enabled") {
    document.body.classList.add("high-contrast");
  }
  
  initMap();
  setupUIEventListeners();
  loadParkData();
});

function initMap() {
  const config = STATE_CONFIG[activeState];
  // Initialize Leaflet Map
  map = L.map("map", {
    zoomControl: true,
    tap: false, // Prevents mobile touch double-tap delay issues
  }).setView(config.center, config.zoom);

  // Set correct tile layer based on accessibility setting
  const isHighContrast = document.body.classList.contains("high-contrast");
  const tileUrl = isHighContrast ? TILE_URL_LIGHT : TILE_URL_DARK;

  tileLayerInstance = L.tileLayer(tileUrl, {
    attribution: TILE_ATTR,
    maxZoom: 19,
  }).addTo(map);

  // Layer group for managing markers dynamically
  markersLayer = L.layerGroup().addTo(map);
}

/* ==========================================================================
   Data Fetching & Parsing
   ========================================================================== */
function loadParkData() {
  const unifiedCsv = "all_state_parks.csv?v=11";
  Papa.parse(unifiedCsv, {
    download: true,
    header: true,
    dynamicTyping: true,
    skipEmptyLines: true,
    complete: function (results) {
      allParks = results.data;
      console.log(`Loaded ${allParks.length} parks from ${unifiedCsv}.`);
      applyFilters(); // Initial render
    },
    error: function (error) {
      console.error(`Error reading ${unifiedCsv}:`, error);
    },
  });
}

/* ==========================================================================
   Markers Rendering
   ========================================================================== */
function renderMarkers(parks) {
  // Clear old markers
  markersLayer.clearLayers();
  
  if (activeMarker) {
    activeMarker = null;
  }

  parks.forEach((park) => {
    const lat = parseFloat(park.latitude);
    const lon = parseFloat(park.longitude);

    if (isNaN(lat) || isNaN(lon)) return; // Skip parks without geocoding data

    // Create custom styled marker
    const customIcon = L.divIcon({
      className: "custom-div-icon",
      html: `<div class="marker-pin" id="pin-${park.park_slug}"></div>`,
      iconSize: [30, 42],
      iconAnchor: [15, 42],
    });

    const marker = L.marker([lat, lon], { icon: customIcon });
    
    // Bind popup label on hover/click
    marker.bindPopup(`
      <div class="popup-subtitle">${STATE_CONFIG[park.state]?.name || park.state} State Park</div>
      <div class="popup-title">${park.park_name}</div>
    `, {
      closeButton: false,
      offset: L.point(0, -32)
    });

    // Handle marker click
    marker.on("click", () => {
      selectPark(park, marker);
    });

    markersLayer.addLayer(marker);
  });
}

/* ==========================================================================
   Filtering Logic
   ========================================================================== */
function applyFilters() {
  // 1. Core Filter States
  const filterRv = document.getElementById("filter-rv").checked;
  const filterTent = document.getElementById("filter-tent").checked;
  
  const minRvSites = parseInt(document.getElementById("min-rv-sites").value) || 0;
  const minTentSites = parseInt(document.getElementById("min-tent-sites").value) || 0;
  const minRating = parseFloat(document.getElementById("min-rating").value) || 0.0;

  // Site Types
  const filterConcrete = document.getElementById("site-concrete") ? document.getElementById("site-concrete").checked : false;
  const filterDirt = document.getElementById("site-dirt") ? document.getElementById("site-dirt").checked : false;
  const filterGravel = document.getElementById("site-gravel") ? document.getElementById("site-gravel").checked : false;

  // 2. Boolean Amenities Toggles
  const amenities = {
    full_hookups: document.getElementById("amenity-full").checked,
    electric_50amp: document.getElementById("amenity-50amp").checked,
    sewer_hookup: document.getElementById("amenity-sewer").checked,
    water_hookup: document.getElementById("amenity-water").checked,
    dump_station: document.getElementById("amenity-dump").checked,
    pull_through_available: document.getElementById("amenity-pullthru").checked,
    pet_friendly: document.getElementById("amenity-pet").checked,
    showers: document.getElementById("amenity-showers").checked,
    wifi: document.getElementById("amenity-wifi").checked,
    laundry: document.getElementById("amenity-laundry").checked,
    waterfront_sites: document.getElementById("amenity-waterfront") ? document.getElementById("amenity-waterfront").checked : false,
  };

  // 3. Activity Toggles
  const activities = {
    hiking: document.getElementById("activity-hiking").checked,
    fishing: document.getElementById("activity-fishing").checked,
    swimming: document.getElementById("activity-swimming").checked,
    boat_ramp: document.getElementById("activity-boat").checked,
    golf: document.getElementById("activity-golf").checked,
  };

  // 4. Accessibility Toggles
  const accessibility = {
    ada_sites: document.getElementById("filter-ada-sites").checked,
    ada_restrooms: document.getElementById("filter-ada-restrooms").checked,
    ada_trails: document.getElementById("filter-ada-trails").checked,
    ada_water_access: document.getElementById("filter-ada-water").checked,
  };

  // Filter list
  const filtered = allParks.filter((park) => {
    // State Filter
    if (activeState !== "ALL" && park.state !== activeState) return false;

    // Camping Toggles
    if (filterRv && park.has_rv_camping !== true && park.has_rv_camping !== "True") return false;
    if (filterTent && park.has_tent_camping !== true && park.has_tent_camping !== "True") return false;

    // Site Type Toggles
    if (filterConcrete && park.site_type_concrete !== true && park.site_type_concrete !== "True" && park.site_type !== "Concrete") return false;
    if (filterDirt && park.site_type_dirt !== true && park.site_type_dirt !== "True" && park.site_type !== "Dirt") return false;
    if (filterGravel && park.site_type_gravel !== true && park.site_type_gravel !== "True" && park.site_type !== "Gravel") return false;

    // Minimum Counts
    const rvCount = parseInt(park.rv_sites_count) || 0;
    const tentCount = parseInt(park.tent_sites_count) || 0;
    if (rvCount < minRvSites) return false;
    if (tentCount < minTentSites) return false;

    // Minimum Rating
    const rating = parseFloat(park.google_rating) || 0.0;
    if (rating < minRating) return false;

    // Amenities
    for (const [key, value] of Object.entries(amenities)) {
      if (value) {
        const isTrue = park[key] === true || park[key] === "True";
        if (!isTrue) return false;
      }
    }

    // Activities
    for (const [key, value] of Object.entries(activities)) {
      if (value) {
        const isTrue = park[key] === true || park[key] === "True";
        if (!isTrue) return false;
      }
    }

    // Accessibility
    for (const [key, value] of Object.entries(accessibility)) {
      if (value) {
        const isTrue = park[key] === true || park[key] === "True";
        if (!isTrue) return false;
      }
    }

    return true;
  });

  renderMarkers(filtered);
  renderListView(filtered);
}

/* ==========================================================================
   Helper: Calculate distance between two coordinates in miles (Haversine)
   ========================================================================== */
function calculateDistance(lat1, lon1, lat2, lon2) {
  const R = 3958.8; // Radius of the Earth in miles
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

/* ==========================================================================
   Helper: Locate the user using HTML5 Geolocation API
   ========================================================================== */
function locateUser() {
  const btn = document.getElementById("btn-locate-me");
  if (!navigator.geolocation) {
    alert("Geolocation is not supported by your browser.");
    return;
  }

  btn.classList.add("active");
  btn.innerHTML = '<i data-lucide="loader" class="icon animate-spin" style="width: 16px; height: 16px;"></i>';
  lucide.createIcons();

  navigator.geolocation.getCurrentPosition(
    (position) => {
      const lat = position.coords.latitude;
      const lng = position.coords.longitude;
      userCoords = [lat, lng];

      // Create or update Leaflet pulsing user location marker
      const userIcon = L.divIcon({
        className: "custom-user-icon",
        html: '<div class="user-location-pin"></div>',
        iconSize: [32, 32],
        iconAnchor: [16, 16]
      });

      if (userLocationMarker) {
        userLocationMarker.setLatLng(userCoords);
      } else {
        userLocationMarker = L.marker(userCoords, { icon: userIcon }).addTo(map);
      }

      // Find the closest state in our configs based on user location
      let closestState = activeState;
      let minDistance = Infinity;
      for (const [code, state] of Object.entries(STATE_CONFIG)) {
        if (code === "ALL") continue; // Skip national configuration
        const dist = calculateDistance(lat, lng, state.center[0], state.center[1]);
        if (dist < minDistance) {
          minDistance = dist;
          closestState = code;
        }
      }

      // Automatically switch the state if user is closest to another configured state
      if (closestState !== activeState) {
        activeState = closestState;
        document.getElementById("state-select").value = activeState;
        applyFilters();
      }

      // Smoothly pan and zoom map to user's location
      map.flyTo(userCoords, 10);

      // Restore button status
      btn.innerHTML = '<i data-lucide="navigation"></i>';
      lucide.createIcons();
    },
    (error) => {
      console.warn("Geolocation error:", error);
      btn.classList.remove("active");
      btn.innerHTML = '<i data-lucide="navigation"></i>';
      lucide.createIcons();
      alert("Unable to retrieve your location. Please check your browser permissions.");
    },
    {
      enableHighAccuracy: true,
      timeout: 10000,
      maximumAge: 0
    }
  );
}

/* ==========================================================================
   Helper: Extract Hours from raw description text
   ========================================================================== */
function extractHours(text) {
  if (!text) return null;
  const hoursMatch = text.match(/HOURS\s+/i);
  if (!hoursMatch) return null;
  const hoursStart = hoursMatch.index + hoursMatch[0].length;
  const searchArea = text.substring(hoursStart);
  
  // Find the next sentence start (capital letter followed by lowercase) or PLAN YOUR VISIT
  const limitMatch = searchArea.match(/(?:PLAN\s+YOUR\s+VISIT:|[A-Z][a-z]+)/i);
  if (limitMatch) {
    return searchArea.substring(0, limitMatch.index).trim();
  }
  return searchArea.trim();
}

/* ==========================================================================
   Helper: Clean up raw description text
   ========================================================================== */
function cleanDescription(text, parkName) {
  if (!text) return "No description available.";
  
  let clean = text.trim();
  
  // 1. Cut off footer boilerplate (from 'Park Reservations' onwards)
  const footerMatch = clean.match(/Park\s+Reservations\s+All\s+Parks/i);
  if (footerMatch) {
    clean = clean.substring(0, footerMatch.index).trim();
  }
  
  const giftCardsMatch = clean.match(/Gift\s+Cards\s+Camping/i);
  if (giftCardsMatch) {
    clean = clean.substring(0, giftCardsMatch.index).trim();
  }
  
  // 2. Cut off header boilerplate
  const planMatch = clean.match(/PLAN\s+YOUR\s+VISIT:/i);
  if (planMatch) {
    const planStart = planMatch.index;
    const searchArea = clean.substring(planStart + 15);
    const descStartMatch = searchArea.match(/[A-Z][a-z]+/);
    if (descStartMatch) {
      const descStart = planStart + 15 + descStartMatch.index;
      clean = clean.substring(descStart).trim();
    }
  } else {
    // If no PLAN YOUR VISIT:, look for HOURS
    const hoursMatch = clean.match(/HOURS\s+/i);
    if (hoursMatch) {
      const hoursStart = hoursMatch.index;
      const searchArea = clean.substring(hoursStart + 6);
      const descStartMatch = searchArea.match(/[A-Z][a-z]+/);
      if (descStartMatch) {
        const descStart = hoursStart + 6 + descStartMatch.index;
        clean = clean.substring(descStart).trim();
      }
    }
  }
  
  // 3. Remove leading line separators, underscores, or stray characters
  clean = clean.replace(/^[_\s\-\u2014\n\r]+/, "");
  
  // 4. Format list items of admission fees and passes onto separate lines
  clean = clean.replace(/\b(Age\s+\d+-\d+:|Age\s+\d+\s+and\s+older:|\d+\s+and\s+older:|Senior\s+Citizen\s+age|Parks\s+for\s+Patriots|ANNUAL\s+PASSES|Senior\s+and\s+Disability|Individuals\s+Pass|Family\s+Pass)\b/g, "\n$1");

  // 5. Fallback if cleanup left us with almost nothing
  if (clean.length < 50) {
    return text.trim();
  }
  
  return clean;
}

/* ==========================================================================
   Details Drawer Control
   ========================================================================== */
function selectPark(park, marker) {
  selectedPark = park;

  // Un-highlight previous marker pin
  if (activeMarker) {
    const prevPin = document.querySelector(".marker-pin.active");
    if (prevPin) prevPin.classList.remove("active");
  }

  // Highlight current marker pin
  activeMarker = marker;
  setTimeout(() => {
    const pin = document.getElementById(`pin-${park.park_slug}`);
    if (pin) pin.classList.add("active");
  }, 50);

  // Center map on coordinates with a slight offset so drawer doesn't overlap
  const lat = parseFloat(park.latitude);
  const lon = parseFloat(park.longitude);
  
  // Adjust offset based on desktop vs mobile screen
  const isMobile = window.innerWidth < 768;
  const offsetLat = isMobile ? lat - 0.08 : lat;
  const offsetLon = isMobile ? lon : lon - 0.05;
  map.setView([offsetLat, offsetLon], 10);

  // Populate Slide-up Detail Drawer UI
  document.getElementById("drawer-park-name").textContent = park.park_name;
  document.getElementById("drawer-slug").textContent = `${STATE_CONFIG[park.state]?.name || park.state} State Park`;

  // Ratings block
  const rating = parseFloat(park.google_rating);
  const reviewCount = parseInt(park.google_review_count);
  const ratingContainer = document.getElementById("drawer-rating-block");

  if (!isNaN(rating)) {
    ratingContainer.classList.remove("hidden");
    document.getElementById("drawer-rating-score").textContent = rating.toFixed(1);
    document.getElementById("drawer-review-count").textContent = `${reviewCount.toLocaleString()} Google reviews`;
    
    // Generate Stars HTML
    const starsRow = document.getElementById("drawer-stars");
    starsRow.innerHTML = "";
    const roundedStars = Math.round(rating);
    for (let i = 1; i <= 5; i++) {
      if (i <= roundedStars) {
        starsRow.innerHTML += '<i data-lucide="star" class="icon"></i>';
      } else {
        starsRow.innerHTML += '<i data-lucide="star" class="icon empty"></i>';
      }
    }
  } else {
    ratingContainer.classList.add("hidden");
  }

  // Update Distance Badge if user location is available
  const distanceBadge = document.getElementById("drawer-distance");
  const distanceValue = document.getElementById("drawer-distance-value");

  if (userCoords && !isNaN(lat) && !isNaN(lon)) {
    const dist = calculateDistance(userCoords[0], userCoords[1], lat, lon);
    distanceValue.textContent = `${dist.toFixed(1)} mi away`;
    distanceBadge.classList.remove("hidden");
  } else {
    distanceBadge.classList.add("hidden");
  }

  // Description text & Quick details block (address, phone, hours)
  const rawDesc = park.description_text || park.campground_text || "";
  const desc = cleanDescription(rawDesc, park.park_name);
  document.getElementById("drawer-desc").textContent = desc;

  // Render the structured quick info block
  const quickInfoContainer = document.getElementById("drawer-quick-info");
  quickInfoContainer.innerHTML = "";
  let hasQuickInfo = false;

  if (park.address) {
    quickInfoContainer.innerHTML += `
      <div class="quick-info-item">
        <i data-lucide="map-pin" class="icon"></i>
        <span><span class="label">Address:</span> ${park.address}</span>
      </div>
    `;
    hasQuickInfo = true;
  }

  const phone = park.phone_camping || park.phone_general;
  if (phone) {
    quickInfoContainer.innerHTML += `
      <div class="quick-info-item">
        <i data-lucide="phone" class="icon"></i>
        <span><span class="label">Phone:</span> ${phone}</span>
      </div>
    `;
    hasQuickInfo = true;
  }



  if (hasQuickInfo) {
    quickInfoContainer.classList.remove("hidden");
  } else {
    quickInfoContainer.classList.add("hidden");
  }

  // Detail Cards Grid
  const rvCount = parseInt(park.rv_sites_count);
  document.getElementById("drawer-rv-count").textContent = isNaN(rvCount)
    ? (park.has_rv_camping === true || park.has_rv_camping === "True" ? "Yes" : "None")
    : `${rvCount} Sites`;

  const tentCount = parseInt(park.tent_sites_count);
  document.getElementById("drawer-tent-count").textContent = isNaN(tentCount)
    ? (park.has_tent_camping === true || park.has_tent_camping === "True" ? "Yes" : "None")
    : `${tentCount} Sites`;

  const prim = park.primitive_camping;
  document.getElementById("drawer-primitive").textContent = (prim === true || prim === "True") ? "Available" : "No";

  const rig = park.max_rig_length_ft;
  document.getElementById("drawer-rig-length").textContent = rig ? `${rig} feet` : "Unspecified";

  // Render Amenities Chips list
  const amenitiesList = [
    { label: "Full Hookups", key: "full_hookups" },
    { label: "50 Amp", key: "electric_50amp" },
    { label: "30 Amp", key: "electric_30amp" },
    { label: "Water Hookup", key: "water_hookup" },
    { label: "Sewer Hookup", key: "sewer_hookup" },
    { label: "Dump Station", key: "dump_station" },
    { label: "Pull-Thru", key: "pull_through_available" },
    { label: "Pet Friendly", key: "pet_friendly" },
    { label: "Showers", key: "showers" },
    { label: "Laundry", key: "laundry" },
    { label: "WiFi", key: "wifi" },
    { label: "ADA Sites", key: "ada_sites" },
    { label: "Waterfront", key: "waterfront_sites" }
  ];

  const amenitiesContainer = document.getElementById("drawer-amenities-container");
  amenitiesContainer.innerHTML = "";
  amenitiesList.forEach(item => {
    const isTrue = park[item.key] === true || park[item.key] === "True";
    const statusClass = isTrue ? "active" : "inactive";
    const iconName = isTrue ? "check" : "x";
    amenitiesContainer.innerHTML += `
      <div class="badge-item ${statusClass}">
        <i data-lucide="${iconName}" style="width: 12px; height: 12px;"></i>
        ${item.label}
      </div>
    `;
  });

  // Render Activities Chips list
  const activitiesList = [
    { label: "Hiking Trails", key: "hiking", icon: "footprints" },
    { label: "Fishing", key: "fishing", icon: "fish" },
    { label: "Swimming Area", key: "swimming", icon: "waves" },
    { label: "Boat Ramp", key: "boat_ramp", icon: "ship" },
    { label: "Golf Course", key: "golf", icon: "flag" },
    { label: "Lake/River Access", key: "lake_river_access", icon: "droplets" }
  ];

  const activitiesContainer = document.getElementById("drawer-activities-container");
  activitiesContainer.innerHTML = "";
  activitiesList.forEach(item => {
    const isTrue = park[item.key] === true || park[item.key] === "True";
    if (isTrue) {
      activitiesContainer.innerHTML += `
        <div class="badge-item activity">
          <i data-lucide="${item.icon}" style="width: 12px; height: 12px;"></i>
          ${item.label}
        </div>
      `;
    }
  });
  
  if (activitiesContainer.innerHTML === "") {
    activitiesContainer.innerHTML = `<span class="helper-text">None specified.</span>`;
  }

  // Render Accessibility Chips list
  const accessibilityList = [
    { label: "ADA Campsites", key: "ada_sites" },
    { label: "ADA Restrooms", key: "ada_restrooms" },
    { label: "Paved Trails", key: "ada_trails" },
    { label: "ADA Water Access", key: "ada_water_access" }
  ];

  const accessibilityContainer = document.getElementById("drawer-accessibility-container");
  accessibilityContainer.innerHTML = "";
  accessibilityList.forEach(item => {
    const isTrue = park[item.key] === true || park[item.key] === "True";
    const statusClass = isTrue ? "accessibility-active" : "inactive";
    const iconName = isTrue ? "check" : "x";
    accessibilityContainer.innerHTML += `
      <div class="badge-item ${statusClass}">
        <i data-lucide="${iconName}" style="width: 12px; height: 12px;"></i>
        ${item.label}
      </div>
    `;
  });

  // Contacts
  const address = park.address;
  const addressElement = document.getElementById("drawer-address");
  addressElement.innerHTML = `<i data-lucide="map-pin" class="icon"></i> ${address || "No address listed"}`;
  if (address && park.google_maps_url) {
    addressElement.href = park.google_maps_url;
  } else {
    addressElement.removeAttribute("href");
  }

  const phoneCamping = park.phone_camping;
  const phoneGeneral = park.phone_general;
  const phoneCampElement = document.getElementById("drawer-phone-camp");
  const phoneGenElement = document.getElementById("drawer-phone-gen");

  if (phoneCamping) {
    phoneCampElement.classList.remove("hidden");
    phoneCampElement.href = `tel:${phoneCamping.replace(/\D/g, "")}`;
    phoneCampElement.innerHTML = `<i data-lucide="phone-call" class="icon"></i> Call Camping: ${phoneCamping}`;
  } else {
    phoneCampElement.classList.add("hidden");
  }

  if (phoneGeneral) {
    phoneGenElement.classList.remove("hidden");
    phoneGenElement.href = `tel:${phoneGeneral.replace(/\D/g, "")}`;
    phoneGenElement.innerHTML = `<i data-lucide="phone" class="icon"></i> Call Office: ${phoneGeneral}`;
  } else {
    phoneGenElement.classList.add("hidden");
  }

  // Actions
  const btnReserve = document.getElementById("btn-reserve");
  
  let targetUrl = park.reservation_url || park.park_url;
  let buttonLabel = "Reserve / Park Info";

  if (park.state !== "AL") {
    // For states other than Alabama, direct search/reservation links often fail with 403/404 session timeouts.
    // Route users to the official state park details page where bookings can be safely initiated.
    targetUrl = park.park_url || park.reservation_url;
  }

  if (targetUrl) {
    btnReserve.classList.remove("hidden");
    btnReserve.href = targetUrl;
    btnReserve.innerHTML = `<i data-lucide="calendar-check"></i> ${buttonLabel}`;
  } else {
    btnReserve.classList.add("hidden");
  }

  const btnMaps = document.getElementById("btn-maps");
  if (park.google_maps_url) {
    btnMaps.classList.remove("hidden");
    btnMaps.href = park.google_maps_url;
  } else {
    btnMaps.classList.add("hidden");
  }

  const btnRoute = document.getElementById("btn-route");
  if (!isNaN(lat) && !isNaN(lon)) {
    btnRoute.classList.remove("hidden");
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
    if (isIOS) {
      btnRoute.href = `maps://maps.apple.com/?daddr=${lat},${lon}&dirflg=d`;
    } else {
      btnRoute.href = `https://www.google.com/maps/dir/?api=1&destination=${lat},${lon}`;
    }
  } else {
    btnRoute.classList.add("hidden");
  }

  // Open the drawer
  document.getElementById("detail-drawer").classList.add("active");
  
  // Re-run Lucide icons render
  lucide.createIcons();
}

function closeDetailDrawer() {
  document.getElementById("detail-drawer").classList.remove("active");
  if (activeMarker) {
    const activePin = document.querySelector(".marker-pin.active");
    if (activePin) activePin.classList.remove("active");
    activeMarker.closePopup();
    activeMarker = null;
  }
  selectedPark = null;
}

/* ==========================================================================
   UI Controls & Event Handlers
   ========================================================================== */
function setupUIEventListeners() {
  // Accessibility Contrast Mode Toggle
  const btnToggleAccess = document.getElementById("btn-toggle-accessibility");
  if (document.body.classList.contains("high-contrast")) {
    btnToggleAccess.classList.add("active");
  }

  btnToggleAccess.addEventListener("click", () => {
    const isHC = document.body.classList.toggle("high-contrast");
    btnToggleAccess.classList.toggle("active", isHC);
    
    // Dynamically swap Leaflet tile layer URL
    const newTileUrl = isHC ? TILE_URL_LIGHT : TILE_URL_DARK;
    if (tileLayerInstance) {
      tileLayerInstance.setUrl(newTileUrl);
    }
    
    // Persist user selection
    localStorage.setItem("accessibilityMode", isHC ? "enabled" : "disabled");
  });

  // Drawer Toggles
  const btnToggleFilter = document.getElementById("btn-toggle-filter");
  const filterPanel = document.getElementById("filter-panel");

  btnToggleFilter.addEventListener("click", () => {
    const isMobile = window.innerWidth < 768;
    if (isMobile) {
      filterPanel.classList.toggle("active");
    } else {
      filterPanel.classList.toggle("hidden");
      btnToggleFilter.classList.toggle("active");
    }
  });

  // Close filter drawer on mobile by clicking header drag bar
  document.querySelector(".filter-panel-header .drag-handle").addEventListener("click", () => {
    filterPanel.classList.remove("active");
  });

  // Close details drawer
  document.getElementById("btn-close-drawer").addEventListener("click", () => {
    closeDetailDrawer();
  });

  // Dual Camping Toggles visual card selection
  const campingCards = document.querySelectorAll(".camp-type-card");
  campingCards.forEach(card => {
    const checkbox = card.querySelector("input");
    
    // Clicking card toggles checkbox
    card.addEventListener("click", (e) => {
      if (e.target !== checkbox) {
        checkbox.checked = !checkbox.checked;
      }
      card.classList.toggle("active", checkbox.checked);
      applyFilters();
    });
    
    // Set initial card highlight state
    card.classList.toggle("active", checkbox.checked);
  });

  // Slider change updates label badge and re-filters
  const sliders = [
    { slider: "min-rv-sites", label: "label-rv-count", suffix: " sites" },
    { slider: "min-tent-sites", label: "label-tent-count", suffix: " sites" },
    { slider: "min-rating", label: "label-rating", prefix: "★ " }
  ];

  sliders.forEach(item => {
    const sliderEl = document.getElementById(item.slider);
    const labelEl = document.getElementById(item.label);
    
    sliderEl.addEventListener("input", () => {
      let val = sliderEl.value;
      if (item.prefix) val = item.prefix + val;
      if (item.suffix) val = val + item.suffix;
      labelEl.textContent = val;
      applyFilters();
    });
  });

  // Checkboxes list selection style
  const chips = document.querySelectorAll(".chip-label");
  chips.forEach(chip => {
    const checkbox = chip.querySelector("input");
    chip.addEventListener("click", () => {
      chip.classList.toggle("active", checkbox.checked);
      applyFilters();
    });
  });

  // Reset Filters
  document.getElementById("btn-reset").addEventListener("click", () => {
    // Reset Checkboxes
    document.querySelectorAll("input[type='checkbox']").forEach(cb => cb.checked = false);
    
    // Reset Sliders
    document.getElementById("min-rv-sites").value = 0;
    document.getElementById("label-rv-count").textContent = "0 sites";
    
    document.getElementById("min-tent-sites").value = 0;
    document.getElementById("label-tent-count").textContent = "0 sites";
    
    document.getElementById("min-rating").value = 0.0;
    document.getElementById("label-rating").textContent = "★ 0.0";

    // Reset visual CSS active states
    document.querySelectorAll(".camp-type-card").forEach(card => card.classList.remove("active"));
    document.querySelectorAll(".chip-label").forEach(chip => chip.classList.remove("active"));

    applyFilters();
  });

  // State Select Dropdown Listener
  const stateSelect = document.getElementById("state-select");
  stateSelect.addEventListener("change", () => {
    activeState = stateSelect.value;
    closeDetailDrawer();
    
    // Smoothly pan and zoom map to the new state
    const config = STATE_CONFIG[activeState];
    map.setView(config.center, config.zoom);
    
    // Apply filters locally on the already loaded master dataset
    applyFilters();
  });

  // Locate Me Button Listener
  const btnLocateMe = document.getElementById("btn-locate-me");
  btnLocateMe.addEventListener("click", () => {
    locateUser();
  });

  // View Switcher Buttons
  document.getElementById("btn-view-map").addEventListener("click", () => {
    switchToView("map");
  });
  document.getElementById("btn-view-list").addEventListener("click", () => {
    switchToView("list");
  });

  // Re-render Lucide icons initially
  lucide.createIcons();
}

/* ==========================================================================
   View Switching & List View Rendering
   ========================================================================== */

function switchToView(viewName) {
  const btnMap = document.getElementById("btn-view-map");
  const btnList = document.getElementById("btn-view-list");
  const mapEl = document.getElementById("map");
  const btnLocate = document.getElementById("btn-locate-me");
  const listEl = document.getElementById("list-view");
  
  if (viewName === "map") {
    btnMap.classList.add("active");
    btnList.classList.remove("active");
    mapEl.classList.remove("hidden");
    btnLocate.classList.remove("hidden");
    listEl.classList.add("hidden");
    
    // Recalculate leaflet map size now that it's visible again
    setTimeout(() => {
      map.invalidateSize();
    }, 100);
  } else {
    btnMap.classList.remove("active");
    btnList.classList.add("active");
    mapEl.classList.add("hidden");
    btnLocate.classList.add("hidden");
    listEl.classList.remove("hidden");
  }
}

function renderListView(parks) {
  const container = document.getElementById("list-view");
  if (!container) return;
  
  container.innerHTML = "";
  
  if (parks.length === 0) {
    container.innerHTML = `
      <div class="no-results-card text-center">
        <i data-lucide="compass" class="icon" style="width: 48px; height: 48px; margin: 0 auto 15px auto; color: var(--text-muted);"></i>
        <h3 style="color: var(--text-primary); font-family: 'Outfit', sans-serif;">No Campsites Found</h3>
        <p style="color: var(--text-muted); font-size: 13px; margin-top: 5px;">Adjust your filters to see more campgrounds.</p>
      </div>
    `;
    lucide.createIcons();
    return;
  }
  
  parks.forEach(park => {
    // Determine distance
    let distanceStr = "";
    const lat = parseFloat(park.latitude);
    const lon = parseFloat(park.longitude);
    if (userCoords && !isNaN(lat) && !isNaN(lon)) {
      const dist = calculateDistance(userCoords[0], userCoords[1], lat, lon);
      distanceStr = `<span class="distance-badge"><i data-lucide="navigation" style="width: 10px; height: 10px;"></i> ${dist.toFixed(1)} mi away</span>`;
    }
    
    // Rating string
    const rating = parseFloat(park.google_rating);
    const reviewCount = parseInt(park.google_review_count);
    let ratingHtml = "";
    if (!isNaN(rating)) {
      ratingHtml = `
        <span class="camp-card-meta-item">
          <i data-lucide="star" class="icon" style="fill: var(--warning); color: var(--warning); width: 14px; height: 14px;"></i>
          <span class="camp-card-rating">${rating.toFixed(1)}</span>
          <span style="color: var(--text-muted);">(${reviewCount.toLocaleString()})</span>
        </span>
      `;
    }
    
    // Accessibility Badges
    let accBadgesHtml = "";
    const accItems = [
      { label: "ADA Campsites", key: "ada_sites" },
      { label: "ADA Restrooms", key: "ada_restrooms" },
      { label: "Paved Trails", key: "ada_trails" },
      { label: "ADA Water Access", key: "ada_water_access" }
    ];
    accItems.forEach(item => {
      if (park[item.key] === true || park[item.key] === "True") {
        accBadgesHtml += `
          <span class="camp-card-acc-badge">
            <i data-lucide="check" style="width: 10px; height: 10px; color: hsl(210, 100%, 65%);"></i>
            ${item.label}
          </span>
        `;
      }
    });
    
    // Site counts
    const rvCount = parseInt(park.rv_sites_count);
    const tentCount = parseInt(park.tent_sites_count);
    const rvText = isNaN(rvCount)
      ? (park.has_rv_camping === true || park.has_rv_camping === "True" ? "Yes" : "None")
      : `${rvCount} RV`;
    const tentText = isNaN(tentCount)
      ? (park.has_tent_camping === true || park.has_tent_camping === "True" ? "Yes" : "None")
      : `${tentCount} Tent`;

    // Determine target URL and button label based on state
    let targetUrl = "";
    let buttonLabel = "Reserve / Info";
    if (park.state === "AL") {
      targetUrl = park.reservation_url || park.park_url;
    } else {
      targetUrl = park.park_url || park.reservation_url;
    }

    // Create the card element
    const card = document.createElement("div");
    card.className = "camp-card";
    
    card.innerHTML = `
      <div class="camp-card-header">
        <div>
          <span class="camp-card-subtitle">${park.state} State Park</span>
          <h4 class="camp-card-title">${park.park_name}</h4>
        </div>
        ${distanceStr}
      </div>
      
      <div class="camp-card-meta">
        ${ratingHtml}
        <span class="camp-card-meta-item">
          <i data-lucide="truck" class="icon"></i>
          <span>${rvText}</span>
        </span>
        <span class="camp-card-meta-item">
          <i data-lucide="tent" class="icon"></i>
          <span>${tentText}</span>
        </span>
      </div>
      
      ${accBadgesHtml ? `<div class="camp-card-acc">${accBadgesHtml}</div>` : ''}
      
      <div class="camp-card-actions">
        ${targetUrl ? `
          <a href="${targetUrl}" target="_blank" class="btn btn-primary stop-propagation">
            <i data-lucide="calendar-check" style="width: 14px; height: 14px;"></i> ${buttonLabel}
          </a>
        ` : ''}
        <button class="btn stop-propagation btn-view-on-map">
          <i data-lucide="map" style="width: 14px; height: 14px;"></i> Map
        </button>
      </div>
    `;
    
    // Add event listeners:
    // 1. Click card to open Details Drawer
    card.addEventListener("click", () => {
      let foundMarker = null;
      markersLayer.eachLayer(m => {
        const latLng = m.getLatLng();
        if (Math.abs(latLng.lat - parseFloat(park.latitude)) < 0.0001 &&
            Math.abs(latLng.lng - parseFloat(park.longitude)) < 0.0001) {
          foundMarker = m;
        }
      });
      selectPark(park, foundMarker);
    });
    
    // Stop propagation on action buttons to prevent opening details drawer twice
    card.querySelectorAll(".stop-propagation").forEach(el => {
      el.addEventListener("click", e => e.stopPropagation());
    });
    
    // 2. View on map button click
    card.querySelector(".btn-view-on-map").addEventListener("click", () => {
      let foundMarker = null;
      markersLayer.eachLayer(m => {
        const latLng = m.getLatLng();
        if (Math.abs(latLng.lat - parseFloat(park.latitude)) < 0.0001 &&
            Math.abs(latLng.lng - parseFloat(park.longitude)) < 0.0001) {
          foundMarker = m;
        }
      });
      
      // Toggle back to Map view
      switchToView("map");
      
      // Select the park and open popup/drawer
      if (foundMarker) {
        selectPark(park, foundMarker);
        foundMarker.openPopup();
      }
    });
    
    container.appendChild(card);
  });
  
  lucide.createIcons();
}
