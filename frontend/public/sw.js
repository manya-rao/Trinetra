// Service Worker for Trinetra PWA
const CACHE_NAME = 'trinetra-v1';
const ASSETS_TO_CACHE = [
  '/',
  '/index.html',
  '/manifest.json'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS_TO_CACHE))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      )
    )
  );
  self.clients.claim();
});

// Intercept Share Target (POST multipart/form-data)
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  if (event.request.method === 'POST' && url.pathname === '/share-target') {
    event.respondWith(
      (async () => {
        const formData = await event.request.formData();
        const file = formData.get('image');
        
        // Cache the shared file in CacheStorage or broadcast to client
        if (file) {
          const cache = await caches.open('trinetra-shared');
          await cache.put('/shared-image', new Response(file));
        }
        
        // Redirect client to home with ?shared=1 flag
        return Response.redirect('/?shared=1', 303);
      })()
    );
    return;
  }

  // Network first with cache fallback for navigation & static assets
  event.respondWith(
    fetch(event.request).catch(() => caches.match(event.request))
  );
});
