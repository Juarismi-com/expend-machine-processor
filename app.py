from flask import Flask, jsonify, abort
from core.slot_app import active_slot
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app) 

@app.route("/")
def hello_world():
    return "api"


@app.route("/signal/<int:key>")
def signal(key):
    producto = active_slot(key)

    if producto:
        return jsonify(producto)
    else:
        abort(404, description=f"Producto con id {key} no encontrado")


@app.route('/payment/bancard/qr')
def get_external_data():
    # Make a GET request to an external API

    payload = {
        'facturaNro': 12345,
        'monto': 10,
        'montoVuelto': 20
    }

    try:
        # Make the POST request
        response = requests.post('https://192.168.100.15:3000/pos/venta-qr', json=payload, timeout=100)

        # Return the response from the external API
        return jsonify({
            'status_code': response.status_code,
            'response': response.json()
        })

    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500