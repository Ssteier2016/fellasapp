// Nombre de la caché para la versión actual de la interfaz
const CACHE_NAME = 'showroom-roma-cache-v1';

// Recursos esenciales para la carga offline de la interfaz (Ajusta si tienes más archivos)
const urlsToCache = [
    '/', // Raíz del sitio (asumimos que carga templates/index.html)
    // El manifiesto debe estar en la raíz para ser detectado
    'manifest.json', 
    // Incluir los íconos referenciados por el manifest
    '/static/icon3.png', 
    '/static/icon-maskable.png'
];

// 1. Evento de Instalación: Cachea los archivos esenciales
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('[Service Worker] Cacheando archivos estáticos...');
                return cache.addAll(urlsToCache);
            })
    );
});

// 2. Evento de Activación: Limpia cachés antiguas
self.addEventListener('activate', (event) => {
    const cacheWhitelist = [CACHE_NAME];
    
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheWhitelist.indexOf(cacheName) === -1) {
                        console.log('[Service Worker] Eliminando caché antigua:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});

// 3. Evento de Fetch: Estrategia Cache-First para la interfaz
self.addEventListener('fetch', (event) => {
    // Excluir peticiones a APIs externas (para evitar errores de CORS)
    if (event.request.url.includes('api.tutienda.com') || event.request.url.includes('googleapis.com')) {
        return; 
    }

    event.respondWith(
        caches.match(event.request)
            .then((response) => {
                // Si el recurso está en caché, lo devuelve
                if (response) {
                    return response;
                }
                
                // Si no está, va a la red y luego lo añade al caché
                return fetch(event.request).then(
                    function(response) {
                        if(!response || response.status !== 200 || response.type !== 'basic') {
                            return response;
                        }

                        var responseToCache = response.clone();
                        caches.open(CACHE_NAME)
                            .then(function(cache) {
                                cache.put(event.request, responseToCache);
                            });

                        return response;
                    }
                );
            })
    );
});


// 4. Lógica de Notificaciones Push (manteniendo tu código original)
self.addEventListener('push', event => {
  const data = event.data.json();
  self.registration.showNotification(data.title, {
    body: data.body,
    icon: '/static/icon3.png', // Usar la ruta estática correcta
    data: { url: data.url }
  });
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  event.waitUntil(
    clients.openWindow(event.notification.data.url)
  );
});

