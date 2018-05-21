const cacheName = 'globaltimes-cache';
let filesToCache = [
    '/static/scripts/menu.js',
    '/static/scripts/snuownd.js',
    '/static/stylesheets/main.css',
    '/static/images/bookmark.svg',
    '/static/images/menu.svg',
    '/static/images/play.svg',
    '/static/images/play-clicked.svg',
    '/static/images/search.svg',
    '/static/images/user.svg',
    '/static/images/x.svg',
];

self.addEventListener('install', function(e) {
  console.log('[ServiceWorker] Install');
  e.waitUntil(
    caches.open(cacheName).then(function(cache) {
      console.log('[ServiceWorker] Caching app shell');
      return cache.addAll(filesToCache);
    })
  );
});

self.addEventListener('activate', function(e) {
    e.waitUntil(
    caches.keys().then(function(keyList) {
      return Promise.all(keyList.map(function(key) {
        if (key !== cacheName) {
          console.log('[ServiceWorker] Removing old cache', key);
          return caches.delete(key);
        }
      }));
    })
  );
  return self.clients.claim();
});

self.addEventListener('fetch', function(e) {
  console.log('[ServiceWorker] Fetch', e.request.url);
  e.respondWith(
    caches.match(e.request).then(function(response) {
      return response || fetch(e.request);
    })
  );
});
