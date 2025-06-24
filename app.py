from flask import Flask, jsonify, abort, g
from flask_cors import CORS
#from database.conn import get_db, close_db, init_db
from routes.vending_route import bp as vending_bp
from database.conn import get_db

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
app.register_blueprint(vending_bp, url_prefix="/vending")
@app.route("/")
def hello_world():
    return "api v1"



"""
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
"""


if __name__ == "__main__":
    app.run(debug=True)