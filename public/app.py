from flask import Flask, render_template, jsonify, request, session
from flask_cors import CORS
from datetime import datetime, timedelta
import json
import uuid
import threading
import time

app = Flask(__name__)
CORS(app)
app.secret_key = 'showroom_roma_secret_key_2024'

# Almacenar usuarios conectados
connected_users = {}
user_lock = threading.Lock()

# Tiempo de expiración de sesión (5 minutos)
SESSION_TIMEOUT = 300  # 5 minutos en segundos

# Lista de productos con dos prendas (URLs de ejemplo, reemplaza con las tuyas)
products = [
    {"id": 1, "name": "Remera Underarmour XXL", "image": "https://i.imgur.com/0lX8j5O.jpg", "timeLeft": 3600},
    {"id": 2, "name": "Short Underarmour S", "image": "https://i.imgur.com/5Y7Qz9I.jpg", "timeLeft": 7200},
]

cart = []

def cleanup_old_sessions():
    """Limpia sesiones antiguas periódicamente"""
    while True:
        time.sleep(60)  # Ejecutar cada minuto
        current_time = datetime.now()
        with user_lock:
            to_remove = []
            for user_id, user_data in connected_users.items():
                last_seen = user_data.get('last_seen')
                if last_seen and (current_time - last_seen).total_seconds() > SESSION_TIMEOUT:
                    to_remove.append(user_id)
            
            for user_id in to_remove:
                del connected_users[user_id]
                print(f"[INFO] Sesión expirada eliminada: {user_id}")

# Iniciar hilo de limpieza
cleanup_thread = threading.Thread(target=cleanup_old_sessions, daemon=True)
cleanup_thread.start()

@app.before_request
def track_user_session():
    """Rastrea la sesión del usuario antes de cada solicitud"""
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
        session['created_at'] = datetime.now().isoformat()
    
    user_id = session['user_id']
    user_ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', 'Desconocido')
    
    with user_lock:
        connected_users[user_id] = {
            'ip': user_ip,
            'user_agent': user_agent,
            'last_seen': datetime.now(),
            'created_at': session['created_at'],
            'current_page': request.path
        }
    
    # Actualizar última actividad en sesión
    session['last_activity'] = datetime.now().isoformat()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/products', methods=['GET'])
def get_products():
    return jsonify(products)

@app.route('/api/cart', methods=['GET'])
def get_cart():
    return jsonify(cart)

@app.route('/api/cart', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    product_id = data.get('productId')
    price = data.get('price')
    
    if not product_id or price is None:
        return jsonify({"error": "ID del producto o precio no proporcionado"}), 400
    
    try:
        price = float(price)
    except (ValueError, TypeError):
        return jsonify({"error": "El precio debe ser un número válido"}), 400
    
    product = next((p for p in products if p['id'] == product_id), None)
    
    if not product:
        return jsonify({"error": "Producto no encontrado"}), 404
    if price <= 0:
        return jsonify({"error": "El precio debe ser mayor que 0"}), 400
    if product['timeLeft'] <= 0:
        return jsonify({"error": "La subasta ha finalizado"}), 400
        
    cart.append({"id": product_id, "name": product['name'], "price": price})
    return jsonify({"message": "Producto agregado al carrito", "cart": cart})

@app.route('/api/cart/<int:index>', methods=['DELETE'])
def remove_from_cart(index):
    if 0 <= index < len(cart):
        cart.pop(index)
        return jsonify({"message": "Producto eliminado", "cart": cart})
    return jsonify({"error": "Índice inválido"}), 400

@app.route('/api/update_timers', methods=['POST'])
def update_timers():
    for product in products:
        if product['timeLeft'] > 0:
            product['timeLeft'] -= 1
    return jsonify(products)

@app.route('/api/connected_users', methods=['GET'])
def get_connected_users():
    """Devuelve la cantidad de usuarios conectados y sus datos"""
    with user_lock:
        active_users = {}
        current_time = datetime.now()
        
        for user_id, user_data in connected_users.items():
            last_seen = user_data.get('last_seen')
            # Solo incluir usuarios activos (vistos en los últimos 2 minutos)
            if last_seen and (current_time - last_seen).total_seconds() < 120:
                active_users[user_id] = {
                    'ip': user_data.get('ip', 'Desconocido'),
                    'user_agent_short': user_data.get('user_agent', 'Desconocido')[:50],
                    'last_seen': user_data.get('last_seen').isoformat(),
                    'current_page': user_data.get('current_page', '/'),
                    'session_age': (current_time - user_data.get('last_seen')).total_seconds()
                }
    
    return jsonify({
        'total_connected': len(active_users),
        'active_users': active_users,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/connected_count', methods=['GET'])
def get_connected_count():
    """Solo devuelve el conteo de usuarios conectados (más ligero)"""
    with user_lock:
        current_time = datetime.now()
        active_count = 0
        
        for user_data in connected_users.values():
            last_seen = user_data.get('last_seen')
            if last_seen and (current_time - last_seen).total_seconds() < 120:
                active_count += 1
    
    return jsonify({
        'connected_count': active_count,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/user_heartbeat', methods=['POST'])
def user_heartbeat():
    """Los clientes pueden enviar un heartbeat para mantenerse activos"""
    user_id = session.get('user_id')
    if user_id:
        with user_lock:
            if user_id in connected_users:
                connected_users[user_id]['last_seen'] = datetime.now()
                connected_users[user_id]['current_page'] = request.headers.get('Referer', '/')
    
    return jsonify({
        'status': 'ok',
        'user_id': user_id,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/session_info', methods=['GET'])
def session_info():
    """Información de la sesión actual del usuario"""
    return jsonify({
        'user_id': session.get('user_id'),
        'created_at': session.get('created_at'),
        'last_activity': session.get('last_activity'),
        'connected_users_count': len([u for u in connected_users.values() 
                                      if (datetime.now() - u.get('last_seen', datetime.now())).total_seconds() < 120])
    })

@app.route('/api/stats', methods=['GET'])
def stats():
    """Estadísticas detalladas del sistema"""
    with user_lock:
        current_time = datetime.now()
        
        # Calcular diferentes métricas de actividad
        active_users = []
        recent_users = []
        
        for user_id, user_data in connected_users.items():
            last_seen = user_data.get('last_seen', current_time)
            seconds_since = (current_time - last_seen).total_seconds()
            
            if seconds_since < 60:  # Activos en el último minuto
                active_users.append(user_id)
            elif seconds_since < 300:  # Activos en los últimos 5 minutos
                recent_users.append(user_id)
        
        # Agrupar por página
        pages = {}
        for user_data in connected_users.values():
            page = user_data.get('current_page', '/')
            pages[page] = pages.get(page, 0) + 1
        
        # Agrupar por navegador
        browsers = {}
        for user_data in connected_users.values():
            ua = user_data.get('user_agent', 'Desconocido')
            browser = 'Desconocido'
            if 'Chrome' in ua:
                browser = 'Chrome'
            elif 'Firefox' in ua:
                browser = 'Firefox'
            elif 'Safari' in ua and 'Chrome' not in ua:
                browser = 'Safari'
            elif 'Edge' in ua:
                browser = 'Edge'
            
            browsers[browser] = browsers.get(browser, 0) + 1
    
    return jsonify({
        'stats': {
            'total_sessions': len(connected_users),
            'active_last_minute': len(active_users),
            'active_last_5_minutes': len(recent_users),
            'pages_visited': pages,
            'browser_distribution': browsers,
            'cart_items': len(cart),
            'products_count': len(products)
        },
        'timestamp': current_time.isoformat()
    })

@app.route('/api/ping', methods=['GET'])
def ping():
    """Endpoint simple para verificar que el servidor está funcionando"""
    return jsonify({
        'status': 'online',
        'message': 'Showroom +Roma API está funcionando',
        'timestamp': datetime.now().isoformat(),
        'server_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/manifest.json')
def serve_manifest():
    """Sirve el manifest.json desde el sistema de archivos"""
    try:
        with open('public/manifest.json', 'r', encoding='utf-8') as f:
            manifest_data = json.load(f)
        return jsonify(manifest_data)
    except FileNotFoundError:
        # Si no existe, crear uno básico
        return jsonify({
            "name": "Showroom +Roma",
            "short_name": "+Roma",
            "description": "Prendas nuevas, únicas e importadas",
            "start_url": ".",
            "display": "standalone",
            "background_color": "#667eea",
            "theme_color": "#667eea"
        })

@app.route('/sw.js')
def serve_sw():
    """Sirve el service worker"""
    return app.send_static_file('sw.js')

@app.route('/offline')
def offline():
    """Página offline para cuando no hay conexión"""
    return render_template('offline.html')

if __name__ == '__main__':
    print("=" * 50)
    print("Showroom +Roma API Server")
    print(f"Iniciando en: http://localhost:5000")
    print("=" * 50)
    print("\nEndpoints disponibles:")
    print("  GET  /                    - Página principal")
    print("  GET  /api/products        - Lista de productos")
    print("  GET  /api/cart            - Carrito actual")
    print("  POST /api/cart            - Agregar al carrito")
    print("  DELETE /api/cart/{index}  - Eliminar del carrito")
    print("  GET  /api/connected_count - Usuarios conectados")
    print("  GET  /api/stats           - Estadísticas del sistema")
    print("  GET  /api/ping            - Verificar estado del servidor")
    print("  POST /api/user_heartbeat  - Mantener sesión activa")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
