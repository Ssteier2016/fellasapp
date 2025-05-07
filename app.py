from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit
from hashlib import sha256
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret_key_1234567890')
socketio = SocketIO(app, cors_allowed_origins="*")

# Base de datos en memoria (simplificada)
users_db = {}  # {username: hashed_password}
connected_users = {}  # {sid: username}

@app.route('/')
def index():
    return render_template('index.html')

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

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
