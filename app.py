from flask import Flask, jsonify, abort, g, request, make_response
from flask_cors import CORS
#from database.conn import get_db, close_db, init_db
from routes.vending_route import bp as vending_bp
from routes.slot_route import slot_bp
from database.conn import get_db
from env import APP_DEBUG

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

# Muestra el listado de rutas configuradas 
with app.app_context():
    for rule in app.url_map.iter_rules():
        print(f"{rule} -> {rule.methods}")

@app.route("/")
def hello_world():
    return "api v1"


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=APP_DEBUG)