/*  FinCrime — service worker
    Cache-first strategy for the shell (HTML/JS/CSS/icons), network-first for /v1/* API.
*/
const SW_VERSION = "fincrime-sw-v1";
const SHELL = [
  "/",
  "/static/app.js",
  "/static/manifest.json",
  "/static/icon-192.svg",
  "/static/icon-512.svg",
];

self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open(SW_VERSION).then((cache) => cache.addAll(SHELL).catch(() => {}))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== SW_VERSION).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  // API + WS: always go to network (no caching)
  if (url.pathname.startsWith("/v1/") || url.pathname.startsWith("/ws/") || url.pathname === "/metrics") {
    return;
  }
  // Static shell: cache-first
  e.respondWith(
    caches.match(e.request).then((cached) => {
      if (cached) return cached;
      return fetch(e.request).then((resp) => {
        if (resp && resp.status === 200 && e.request.method === "GET") {
          const copy = resp.clone();
          caches.open(SW_VERSION).then((c) => c.put(e.request, copy)).catch(() => {});
        }
        return resp;
      }).catch(() => caches.match("/"));
    })
  );
});
