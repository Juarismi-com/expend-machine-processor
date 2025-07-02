from flask import Flask, jsonify, abort, g
from flask_cors import CORS
#from database.conn import get_db, close_db, init_db
from routes.vending_route import bp as vending_bp
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
app.register_blueprint(vending_bp, url_prefix="/vending")
@app.route("/")
def hello_world():
    return "api v1"




if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=APP_DEBUG, port=5001)