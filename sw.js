const CACHE_NAME = "stateparked-v16";
const ASSETS = [
  "./",
  "./index.html",
  "./styles.css?v=16",
  "./app.js?v=16",
  "./all_state_parks.csv?v=16",
  "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css",
  "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js",
  "https://cdn.jsdelivr.net/npm/papaparse@5.4.1/papaparse.min.js",
  "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700&display=swap",
  "https://unpkg.com/lucide@latest"
];

// Install Event - cache core assets
self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log("[Service Worker] Caching core app assets");
      return cache.addAll(ASSETS);
    }).then(() => self.skipWaiting())
  );
});

// Activate Event - clear old caches
self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            console.log("[Service Worker] Removing old cache", key);
            return caches.delete(key);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch Event - cache-first with network fallback
self.addEventListener("fetch", (e) => {
  e.respondWith(
    caches.match(e.request).then((cachedResponse) => {
      if (cachedResponse) {
        return cachedResponse;
      }
      
      // Fallback to network
      return fetch(e.request).then((networkResponse) => {
        // Cache newly requested assets if they are from our domain or CDNs
        if (
          e.request.url.startsWith(self.location.origin) ||
          e.request.url.includes("unpkg.com") ||
          e.request.url.includes("jsdelivr.net") ||
          e.request.url.includes("googleapis.com") ||
          e.request.url.includes("gstatic.com")
        ) {
          return caches.open(CACHE_NAME).then((cache) => {
            cache.put(e.request, networkResponse.clone());
            return networkResponse;
          });
        }
        return networkResponse;
      }).catch(() => {
        // Handle failed fetch offline cases
        console.log("[Service Worker] Fetch failed; offline.");
      });
    })
  );
});
