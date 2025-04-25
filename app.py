from flask import Flask, jsonify, abort
from core.slot_app import active_slot
from flask_cors import CORS

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

    