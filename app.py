
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import time

app = Flask(__name__)
CORS(app)  # Permitir solicitudes CORS para el frontend

# Lista de productos de ejemplo
products = [
    {"id": 1, "name": "Producto 1", "image": "https://via.placeholder.com/150", "timeLeft": 3600},
    {"id": 2, "name": "Producto 2", "image": "https://via.placeholder.com/150", "timeLeft": 7200},
    {"id": 3, "name": "Producto 3", "image": "https://via.placeholder.com/150", "timeLeft": 1800},
]

# Carrito de compras (almacenado en memoria para este ejemplo)
cart = []

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

    product = next((p for p in products if p['id'] == product_id), None)
    if not product:
        return jsonify({"error": "Producto no encontrado"}), 404
    if not price or price <= 0:
        return jsonify({"error": "Precio inválido"}), 400
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

if __name__ == '__main__':
    app.run(debug=True)
