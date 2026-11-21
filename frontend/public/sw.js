// Trinetra Offline Shell & Share Target Service Worker
const CACHE_NAME = 'trinetra-shell-v1';

self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(clients.claim());
});

self.addEventListener('fetch', (event) => {
  // Handle PWA share target POST
  if (event.request.method === 'POST') {
    const url = new URL(event.request.url);
    if (url.pathname === '/') {
      event.respondWith((async () => {
        try {
          const formData = await event.request.formData();
          const imageFile = formData.get('image');
          if (imageFile) {
            // Forward to verify section
            return Response.redirect('/#verify', 303);
          }
        } catch (e) {
          console.warn('Share target processing failed', e);
        }
        return Response.redirect('/#verify', 303);
      })());
      return;
    }
  }

  // Network-first with cache fallback
  event.respondWith(
    fetch(event.request).catch(() => caches.match(event.request))
  );
});
