from flask import Flask, jsonify, abort, g, request, make_response
from flask_cors import CORS
from routes.vending_route import bp as vending_bp
from routes.slot_route import slot_bp
from routes.dispenser_route import bp as dispenser_bp
from database.conn import get_db
from env import APP_DEBUG, AUTH_TOKEN
import subprocess
import re
import os

app = Flask(__name__)
app.config['DATABASE'] = 'expend_db.sql'


def init_db():
    db = get_db()
    with app.open_resource('./database/schema.sql') as f:
        db.executescript(f.read().decode('utf8'))
    print("Base de datos inicializada")


@app.cli.command('init-db')
def init_db_command():
    """Inicializa la base de datos."""
    init_db()


# Configuracion de las rutas
CORS(app) 
@app.before_request
def handle_options():
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT,PATCH, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response, 200
app.register_blueprint(vending_bp, url_prefix="/vending")
app.register_blueprint(slot_bp, url_prefix="/slots")
app.register_blueprint(dispenser_bp, url_prefix="/dispensers")

# Muestra el listado de rutas configuradas 
with app.app_context():
    for rule in app.url_map.iter_rules():
        print(f"{rule} -> {rule.methods}")


# configuracion de wifi
@app.route("/update_wifi", methods=["POST"])
def update_wifi():
    # Autenticación
    auth_header = request.headers.get("Authorization")
    if auth_header != f"Bearer {AUTH_TOKEN}":
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    ssid = data.get("ssid")
    psk = data.get("psk")

    if not ssid or not psk:
        return jsonify({"error": "Missing ssid or psk"}), 400

    try:
        subprocess.run(["sudo", "/usr/local/bin/update_wifi_config.sh", ssid, psk], check=True)
        return jsonify({"message": "WiFi configuration updated."}), 200
    except subprocess.CalledProcessError as e:
        return jsonify({"error": str(e)}), 500


@app.route("/")
def hello_world():
    return "api v1"


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=APP_DEBUG)