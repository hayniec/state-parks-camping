// Register Service Worker for PWA Offline support
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker
      .register("./sw.js")
      .then((reg) => console.log("Service Worker registered successfully!"))
      .catch((err) => console.warn("Service Worker registration failed:", err));
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

// CartoDB Dark Matter Tile Layer
const TILE_URL = "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png";
const TILE_ATTR =
  '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>';

// State configurations: Centers, default zoom levels, and CSV filenames
const STATE_CONFIG = {
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
  }
};
let activeState = "AL";

/* ==========================================================================
   Map & Application Initialization
   ========================================================================== */
document.addEventListener("DOMContentLoaded", () => {
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

  // Add Dark Map Tile Layer
  L.tileLayer(TILE_URL, {
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
  const config = STATE_CONFIG[activeState];
  Papa.parse(config.csv, {
    download: true,
    header: true,
    dynamicTyping: true,
    skipEmptyLines: true,
    complete: function (results) {
      allParks = results.data;
      console.log(`Loaded ${allParks.length} parks from ${config.csv}.`);
      applyFilters(); // Initial render
    },
    error: function (error) {
      console.error(`Error reading ${config.csv}:`, error);
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
      <div class="popup-subtitle">Alabama State Park</div>
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
  };

  // 3. Activity Toggles
  const activities = {
    hiking: document.getElementById("activity-hiking").checked,
    fishing: document.getElementById("activity-fishing").checked,
    swimming: document.getElementById("activity-swimming").checked,
    boat_ramp: document.getElementById("activity-boat").checked,
    golf: document.getElementById("activity-golf").checked,
  };

  // Filter list
  const filtered = allParks.filter((park) => {
    // Camping Toggles
    if (filterRv && park.has_rv_camping !== true && park.has_rv_camping !== "True") return false;
    if (filterTent && park.has_tent_camping !== true && park.has_tent_camping !== "True") return false;

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

    return true;
  });

  renderMarkers(filtered);
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
  document.getElementById("drawer-slug").textContent = park.park_slug.replace(/-/g, " ");

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

  const hours = extractHours(rawDesc);
  if (hours) {
    // Format hours subheaders (e.g. Winter Hours, Summer Hours) onto separate lines with bullets
    const formattedHours = hours.replace(/(winter|summer|store|office|gate|campground)\s+hours/gi, "<br>• $&");
    quickInfoContainer.innerHTML += `
      <div class="quick-info-item">
        <i data-lucide="clock" class="icon"></i>
        <span><span class="label">Hours:</span> ${formattedHours}</span>
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
  if (park.reservation_url) {
    btnReserve.classList.remove("hidden");
    btnReserve.href = park.reservation_url;
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
    
    // Fetch and load the selected state's campgrounds CSV
    loadParkData();
  });

  // Re-render Lucide icons initially
  lucide.createIcons();
}
