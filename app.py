from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit
from hashlib import sha256
import os
import logging

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret_key_1234567890')
socketio = SocketIO(app, cors_allowed_origins="*")

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Base de datos en memoria (simplificada)
users_db = {}  # {username: hashed_password}
connected_users = {}  # {sid: username}

@app.route('/')
def index():
    logger.debug('Serving index.html')
    return render_template('index.html')

def hash_password(password):
    return sha256(password.encode('utf-8')).hexdigest()

def check_password(password, hashed):
    return hash_password(password) == hashed

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        logger.debug(f'Login request: {data}')
        username = data.get('username')
        password = data.get('password')
        if not username or not password:
            return jsonify({'success': False, 'message': 'Faltan datos'}), 400
        if username in users_db:
            hashed = users_db[username]
            if check_password(password, hashed):
                logger.debug(f'Login successful for {username}')
                return jsonify({'success': True})
        logger.debug(f'Login failed for {username}')
        return jsonify({'success': False, 'message': 'Usuario o contraseña incorrectos'})
    except Exception as e:
        logger.error(f'Error in login: {str(e)}')
        return jsonify({'success': False, 'message': 'Error del servidor'}), 500

@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        logger.debug(f'Register request: {data}')
        username = data.get('username')
        password = data.get('password')
        if not username or not password:
            return jsonify({'success': False, 'message': 'Faltan datos'}), 400
        if username in users_db:
            logger.debug(f'Register failed: User {username} already exists')
            return jsonify({'success': False, 'message': 'El usuario ya existe'})
        hashed = hash_password(password)
        users_db[username] = hashed
        logger.debug(f'Register successful for {username}')
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f'Error in register: {str(e)}')
        return jsonify({'success': False, 'message': 'Error del servidor'}), 500

@app.route('/reset-password', methods=['POST'])
def reset_password():
    try:
        data = request.get_json()
        logger.debug(f'Reset password request: {data}')
        username = data.get('username')
        new_password = data.get('newPassword')
        if not username or not new_password:
            return jsonify({'success': False, 'message': 'Faltan datos'}), 400
        if username not in users_db:
            logger.debug(f'Reset password failed: User {username} not found')
            return jsonify({'success': False, 'message': 'Usuario no encontrado'})
        hashed = hash_password(new_password)
        users_db[username] = hashed
        logger.debug(f'Reset password successful for {username}')
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f'Error in reset-password: {str(e)}')
        return jsonify({'success': False, 'message': 'Error del servidor'}), 500

@socketio.on('connect')
def handle_connect():
    logger.debug('Client connected')
    print('Cliente conectado')

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    if sid in connected_users:
        username = connected_users[sid]
        del connected_users[sid]
        logger.debug(f'User {username} disconnected')
        emit('users', list(connected_users.values()), broadcast=True)

@socketio.on('join')
def handle_join(data):
    username = data['username']
    connected_users[request.sid] = username
    logger.debug(f'User {username} joined')
    emit('users', list(connected_users.values()), broadcast=True)

@socketio.on('message')
def handle_message(data):
    logger.debug(f'Message from {connected_users[request.sid]}: {data}')
    emit('message', {'username': connected_users[request.sid], 'message': data['message']}, broadcast=True)

@socketio.on('audio')
def handle_audio(data):
    username = connected_users[request.sid]
    logger.debug(f'Audio from {username}')
    emit('audio', {'username': username, 'audio': data['audio']}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
