from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from hashlib import sha256
import webpush
from py_vapid import Vapid
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'secret!')
socketio = SocketIO(app, cors_allowed_origins="*")

# Base de datos en memoria (simplificada)
users_db = {}  # {username: hashed_password}
connected_users = {}  # {sid: username}
subscriptions = {}  # {username: subscription}

# Configuración de VAPID para notificaciones push
VAPID_PRIVATE_KEY = os.getenv('VAPID_PRIVATE_KEY', 'YOUR_VAPID_PRIVATE_KEY')
VAPID_PUBLIC_KEY = os.getenv('VAPID_PUBLIC_KEY', 'YOUR_VAPID_PUBLIC_KEY')
VAPID_CLAIMS = {"sub": "mailto:your-email@example.com"}

def hash_password(password):
    return sha256(password.encode('utf-8')).hexdigest()

def check_password(password, hashed):
    return hash_password(password) == hashed

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if username in users_db:
        hashed = users_db[username]
        if check_password(password, hashed):
            return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Usuario o contraseña incorrectos'})

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if username in users_db:
        return jsonify({'success': False, 'message': 'El usuario ya existe'})
    hashed = hash_password(password)
    users_db[username] = hashed
    return jsonify({'success': True})

@app.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json()
    username = data.get('username')
    new_password = data.get('newPassword')
    if username not in users_db:
        return jsonify({'success': False, 'message': 'Usuario no encontrado'})
    hashed = hash_password(new_password)
    users_db[username] = hashed
    return jsonify({'success': True})

@app.route('/subscribe', methods=['POST'])
def subscribe():
    data = request.get_json()
    username = data['username']
    subscription = data['subscription']
    subscriptions[username] = subscription
    return jsonify({'success': True})

@socketio.on('connect')
def handle_connect():
    print('Cliente conectado')

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    if sid in connected_users:
        username = connected_users[sid]
        del connected_users[sid]
        emit('users', list(connected_users.values()), broadcast=True)

@socketio.on('join')
def handle_join(data):
    username = data['username']
    connected_users[request.sid] = username
    emit('users', list(connected_users.values()), broadcast=True)

@socketio.on('message')
def handle_message(data):
    emit('message', {'username': connected_users[request.sid], 'message': data['message']}, broadcast=True)

@socketio.on('audio')
def handle_audio(data):
    username = connected_users[request.sid]
    emit('audio', {'username': username, 'audio': data['audio']}, broadcast=True)
    # Enviar notificación push a los usuarios suscritos
    for sub_username, subscription in subscriptions.items():
        if sub_username != username:  # No enviar notificación al emisor
            try:
                webpush.send(
                    subscription,
                    json.dumps({
                        'title': f'Nuevo audio de {username}',
                        'body': 'Toca para escuchar',
                        'url': 'https://fellasapp.onrender.com'
                    }),
                    VAPID_PRIVATE_KEY,
                    VAPID_CLAIMS
                )
            except Exception as e:
                print(f'Error al enviar notificación a {sub_username}: {e}')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
