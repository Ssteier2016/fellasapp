// Nombre de la caché para la versión actual de la interfaz
// Se recomienda cambiar el número de versión (v1 -> v2) al actualizar los recursos para forzar la limpieza de cachés anteriores.
const CACHE_NAME = 'showroom-roma-cache-v2';

// Recursos esenciales para la carga offline de la interfaz
// Ahora incluye los nuevos archivos de imagen en la raíz del proyecto.
const urlsToCache = [
    '/', // Raíz del sitio (asumimos que carga templates/index.html o index.html)
    'index.html', // Añadido por si la raíz no resuelve el archivo por sí misma
    'manifest.json', 
    
    // Incluir los nuevos íconos y favicon en la raíz
    'icon.png', 
    'logo.png',
    'favicon.png',

    // Puedes añadir aquí otros archivos estáticos críticos (CSS, JS)
    // 'styles.css',
    // 'app.js',
];

// 1. Evento de Instalación: Cachea los archivos esenciales
self.addEventListener('install', (event) => {
    // Forzar la activación inmediata del nuevo Service Worker
    self.skipWaiting(); 
    
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('[Service Worker] Cacheando archivos esenciales para modo offline...');
                // Intentar cachear todos los archivos; si alguno falla, la promesa se rechaza
                return cache.addAll(urlsToCache).catch((error) => {
                    console.error('[Service Worker] Error al cachear un recurso:', error);
                    // Esto puede ocurrir si el servidor no devuelve 200 para algún recurso (e.g., '/')
                });
            })
    );
});

// 2. Evento de Activación: Limpia cachés antiguas y toma el control
self.addEventListener('activate', (event) => {
    const cacheWhitelist = [CACHE_NAME];
    
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    // Si el nombre de la caché no está en la lista blanca, la elimina
                    if (cacheWhitelist.indexOf(cacheName) === -1) {
                        console.log('[Service Worker] Eliminando caché antigua:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => {
            // Reclamar el control de todas las páginas sin recargar
            return self.clients.claim();
        })
    );
});

// 3. Evento de Fetch: Estrategia Cache-First para la interfaz y Network-Falling-Back-to-Cache para nuevas peticiones
self.addEventListener('fetch', (event) => {
    // Excluir peticiones a APIs externas (para evitar errores de CORS)
    if (event.request.url.includes('api.tutienda.com') || event.request.url.includes('googleapis.com') || event.request.url.includes('firebasestorage.googleapis.com')) {
        // Para estas URLs, simplemente dejamos que la red maneje la solicitud
        return; 
    }

    event.respondWith(
        caches.match(event.request)
            .then((response) => {
                // Estrategia Cache-First: Si el recurso está en caché, lo devuelve inmediatamente (soporte offline)
                if (response) {
                    console.log(`[Service Worker] Sirviendo desde caché: ${event.request.url}`);
                    return response;
                }
                
                // Si no está, va a la red
                console.log(`[Service Worker] Petición a la red: ${event.request.url}`);
                return fetch(event.request).then(
                    function(response) {
                        // Verifica que la respuesta sea válida antes de cachearla (no errores, no CORS)
                        if(!response || response.status !== 200 || response.type !== 'basic') {
                            return response;
                        }

                        // Clonar la respuesta porque el cuerpo (body) de la respuesta de red solo se puede leer una vez
                        var responseToCache = response.clone();
                        
                        // Abrir la caché y guardar la nueva respuesta
                        caches.open(CACHE_NAME)
                            .then(function(cache) {
                                cache.put(event.request, responseToCache);
                            });

                        return response;
                    }
                ).catch((error) => {
                    // Esta rama se activa en caso de falla de red (e.g., cuando el usuario está offline)
                    console.error('[Service Worker] Fallo de red. Recurso no encontrado en caché ni en red:', event.request.url, error);
                    // Opcional: Podrías devolver una página offline genérica aquí, e.g., caches.match('/offline.html');
                });
            })
    );
});


// 4. Lógica de Notificaciones Push
self.addEventListener('push', event => {
  const data = event.data.json();
  self.registration.showNotification(data.title, {
    body: data.body,
    // Usar el nuevo ícono de la raíz para la notificación
    icon: 'icon.png', 
    data: { url: data.url }
  });
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  event.waitUntil(
    clients.openWindow(event.notification.data.url)
  );
});
