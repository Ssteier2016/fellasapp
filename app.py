from flask import Flask, render_template, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Lista de productos con URLs de Imgur (reemplaza con tus URLs reales)
products = [
    {"id": 1, "name": "Camisa Gucci Edición Limitada", "image": "https://i.imgur.com/0lX8j5O.jpg", "timeLeft": 3600},
    {"id": 2, "name": "Vestido Dior Vintage", "image": "https://i.imgur.com/5Y7Qz9I.jpg", "timeLeft": 7200},
    {"id": 3, "name": "Chaqueta Levi's Única", "image": "https://i.imgur.com/3Z2r4kL.jpg", "timeLeft": 1800},
]

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
        return jsonify({"error": "La subasta ha finalizada"}), 400
        
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
