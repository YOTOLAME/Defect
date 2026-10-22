var CACHE_NAME = 'defect-capture-v8';
var FILES = ['./', './index.html'].concat([
  '../inspections/INSPECTARE-500M-ASSET-MOBILE.html',
  '../inspections/INSPECTARE-500M-MOBILE.html',
  '../inspections/INSPECTARE-AHTS-MOBILE.html',
  '../inspections/INSPECTARE-CREWBOAT-MOBILE.html',
  '../inspections/INSPECTARE-PSV-MOBILE.html',
  '../inspections/INSPECTARE-TUG-MOBILE.html',
  '../inspections/OVID-AHTS-TUG-OPERATIONS-MOBILE.html',
  '../inspections/OVID-BARGE-OPERATIONS-MOBILE.html',
  '../inspections/OVID-COMMON-PART1-MOBILE.html',
  '../inspections/OVID-COMMON-PART2-MOBILE.html',
  '../inspections/OVID-COMMON-PART3-MOBILE.html',
  '../inspections/OVID-COMMON-PART4-MOBILE.html',
  '../inspections/OVID-CREWBOAT-PART1-MOBILE.html',
  '../inspections/OVID-CREWBOAT-PART2-MOBILE.html',
  '../inspections/OVID-DP-OPERATIONS-MOBILE.html',
  '../inspections/OVID-MPSV-OPERATIONS-MOBILE.html',
  '../inspections/OVID-PSV-OPERATIONS-MOBILE.html'
]);

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
