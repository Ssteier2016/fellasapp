// Nombre de la caché para la versión actual de la interfaz
const CACHE_NAME = 'showroom-roma-cache-v3';

// Recursos esenciales para la carga offline
const urlsToCache = [
    '/',
    '/manifest.json',
    '/sw.js',
    '/offline',
    
    // Recursos CSS/JS si los tienes localmente
    // '/static/css/styles.css',
    // '/static/js/app.js',
    
    // Imágenes de ejemplo (ajusta según tus necesidades)
    'https://raw.githubusercontent.com/Ssteier2016/fellasapp/main/imagen/logo2.png',
    'https://via.placeholder.com/192x192/667eea/ffffff?text=+Roma',
    'https://via.placeholder.com/512x512/667eea/ffffff?text=Showroom+Roma',
];

// 1. Evento de Instalación: Cachea los archivos esenciales
self.addEventListener('install', (event) => {
    console.log('[Service Worker] Instalando...');
    
    // Forzar la activación inmediata
    self.skipWaiting();
    
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('[Service Worker] Cacheando recursos esenciales...');
                return cache.addAll(urlsToCache)
                    .then(() => {
                        console.log('[Service Worker] Todos los recursos cacheados exitosamente');
                    })
                    .catch((error) => {
                        console.error('[Service Worker] Error al cachear recursos:', error);
                        // Continuar incluso si algunos recursos fallan
                    });
            })
    );
});

// 2. Evento de Activación: Limpia cachés antiguas
self.addEventListener('activate', (event) => {
    console.log('[Service Worker] Activando...');
    
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('[Service Worker] Eliminando caché antigua:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => {
            // Tomar control inmediato de todas las pestañas
            console.log('[Service Worker] Tomando control de los clientes...');
            return self.clients.claim();
        })
    );
});

// 3. Evento de Fetch: Estrategia Cache-First con fallback a red
self.addEventListener('fetch', (event) => {
    // Ignorar solicitudes a APIs y recursos externos
    const url = new URL(event.request.url);
    
    // No cachear solicitudes a la API
    if (url.pathname.startsWith('/api/')) {
        return;
    }
    
    // No cachear solicitudes a Firebase o servicios externos
    if (url.href.includes('firebase') || 
        url.href.includes('googleapis') || 
        url.href.includes('gstatic')) {
        return;
    }
    
    // Para navegación (HTML), intentar red primero
    if (event.request.mode === 'navigate') {
        event.respondWith(
            fetch(event.request)
                .then((response) => {
                    // Cachear la página cargada
                    const responseClone = response.clone();
                    caches.open(CACHE_NAME)
                        .then((cache) => {
                            cache.put(event.request, responseClone);
                        });
                    return response;
                })
                .catch(() => {
                    // Si falla, intentar servir desde caché
                    return caches.match(event.request)
                        .then((cachedResponse) => {
                            if (cachedResponse) {
                                return cachedResponse;
                            }
                            // Si no hay en caché, servir página offline
                            return caches.match('/offline');
                        });
                })
        );
        return;
    }
    
    // Para otros recursos (CSS, JS, imágenes), estrategia Cache-First
    event.respondWith(
        caches.match(event.request)
            .then((cachedResponse) => {
                if (cachedResponse) {
                    console.log(`[Service Worker] Sirviendo desde caché: ${event.request.url}`);
                    return cachedResponse;
                }
                
                // Si no está en caché, ir a la red
                console.log(`[Service Worker] Obteniendo de la red: ${event.request.url}`);
                return fetch(event.request)
                    .then((response) => {
                        // Verificar que la respuesta sea válida
                        if (!response || response.status !== 200 || response.type !== 'basic') {
                            return response;
                        }
                        
                        // Clonar y cachear la respuesta
                        const responseToCache = response.clone();
                        caches.open(CACHE_NAME)
                            .then((cache) => {
                                cache.put(event.request, responseToCache);
                            });
                        
                        return response;
                    })
                    .catch((error) => {
                        console.error('[Service Worker] Error de red:', error);
                        
                        // Para imágenes, devolver un placeholder
                        if (event.request.destination === 'image') {
                            return new Response(
                                `<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300" viewBox="0 0 400 300">
                                    <rect width="400" height="300" fill="#667eea"/>
                                    <text x="50%" y="50%" font-family="Arial" font-size="20" fill="white" text-anchor="middle" dy=".3em">
                                        Imagen no disponible offline
                                    </text>
                                </svg>`,
                                {
                                    headers: {
                                        'Content-Type': 'image/svg+xml'
                                    }
                                }
                            );
                        }
                        
                        // Para otros recursos, devolver error
                        return new Response('Recurso no disponible offline', {
                            status: 503,
                            statusText: 'Service Unavailable',
                            headers: new Headers({
                                'Content-Type': 'text/plain'
                            })
                        });
                    });
            })
    );
});

// 4. Manejo de mensajes desde la página principal
self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
});

// 5. Lógica de Notificaciones Push (opcional)
self.addEventListener('push', (event) => {
    console.log('[Service Worker] Push recibido');
    
    let data = {};
    if (event.data) {
        try {
            data = event.data.json();
        } catch (e) {
            data = {
                title: 'Showroom +Roma',
                body: event.data.text() || 'Nueva notificación',
                icon: 'https://raw.githubusercontent.com/Ssteier2016/fellasapp/main/imagen/logo2.png',
                badge: 'https://raw.githubusercontent.com/Ssteier2016/fellasapp/main/imagen/logo2.png'
            };
        }
    }
    
    const options = {
        body: data.body || '¡Nueva oferta disponible!',
        icon: data.icon || 'https://raw.githubusercontent.com/Ssteier2016/fellasapp/main/imagen/logo2.png',
        badge: data.badge || 'https://raw.githubusercontent.com/Ssteier2016/fellasapp/main/imagen/logo2.png',
        vibrate: [100, 50, 100],
        data: {
            url: data.url || '/',
            dateOfArrival: Date.now()
        },
        actions: [
            {
                action: 'explore',
                title: 'Ver oferta',
                icon: 'https://raw.githubusercontent.com/Ssteier2016/fellasapp/main/imagen/logo2.png'
            },
            {
                action: 'close',
                title: 'Cerrar',
                icon: 'https://raw.githubusercontent.com/Ssteier2016/fellasapp/main/imagen/logo2.png'
            }
        ]
    };
    
    event.waitUntil(
        self.registration.showNotification(data.title || 'Showroom +Roma', options)
    );
});

self.addEventListener('notificationclick', (event) => {
    console.log('[Service Worker] Notificación clickeada');
    
    event.notification.close();
    
    if (event.action === 'close') {
        return;
    }
    
    // Abrir la página correspondiente
    event.waitUntil(
        clients.matchAll({
            type: 'window',
            includeUncontrolled: true
        }).then((clientList) => {
            // Si ya hay una ventana abierta, enfocarla
            for (const client of clientList) {
                if (client.url === event.notification.data.url && 'focus' in client) {
                    return client.focus();
                }
            }
            
            // Si no hay ventana abierta, abrir una nueva
            if (clients.openWindow) {
                return clients.openWindow(event.notification.data.url || '/');
            }
        })
    );
});

// 6. Sincronización en segundo plano
self.addEventListener('sync', (event) => {
    console.log('[Service Worker] Sincronización:', event.tag);
    
    if (event.tag === 'sync-cart') {
        event.waitUntil(
            syncCartData()
        );
    }
});

async function syncCartData() {
    console.log('[Service Worker] Sincronizando carrito...');
    // Aquí iría la lógica para sincronizar datos offline
    // Por ejemplo, enviar pedidos pendientes al servidor
}

// 7. Manejo de actualizaciones periódicas
async function checkForUpdates() {
    console.log('[Service Worker] Verificando actualizaciones...');
    
    try {
        const response = await fetch('/?check-update=true');
        if (response.status === 200) {
            // Podrías verificar aquí si hay una nueva versión
            const cache = await caches.open(CACHE_NAME);
            const cachedResponse = await cache.match('/');
            
            if (!cachedResponse) {
                // Recachear si es necesario
                console.log('[Service Worker] Actualizando caché...');
                // Aquí iría la lógica de actualización
            }
        }
    } catch (error) {
        console.error('[Service Worker] Error verificando actualizaciones:', error);
    }
}

// Ejecutar verificación periódica
setInterval(checkForUpdates, 3600000); // Cada hora

console.log('[Service Worker] Cargado y listo');
