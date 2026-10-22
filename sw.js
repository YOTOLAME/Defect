var CACHE_NAME = 'defect-capture-v3';
var FILES = ['./', './index.html'];

self.addEventListener('install', function(e) {
  e.waitUntil(caches.open(CACHE_NAME).then(function(cache) { return cache.addAll(FILES); }));
  self.skipWaiting();
});

self.addEventListener('activate', function(e) {
  e.waitUntil(caches.keys().then(function(keys) {
    return Promise.all(keys.filter(function(k) { return k.indexOf('defect-capture-') === 0 && k !== CACHE_NAME; })
      .map(function(k) { return caches.delete(k); }));
  }));
  self.clients.claim();
});

self.addEventListener('fetch', function(e) {
  if (e.request.method !== 'GET') { return; }
  e.respondWith(caches.match(e.request, { ignoreSearch: true }).then(function(cached) {
    return cached || fetch(e.request);
  }));
});
