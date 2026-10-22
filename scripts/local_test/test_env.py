# Configuracion del processor para pruebas locales (reemplaza a env.py).
# Los valores se pueden sobreescribir con variables de entorno.
import os

_HERE = os.path.dirname(os.path.abspath(__file__))

API_URL = os.environ.get("TEST_API_URL", "http://localhost:5099")
MACHINE_ID = os.environ.get("TEST_MACHINE_ID", "maquina-test")
BANCARD_API_URL = os.environ.get("TEST_POS_URL", "http://localhost:5098")
APP_PLATFORM = "default"  # nunca toca GPIO
APP_DEBUG = False
MODO_RELES = 0
AUTH_TOKEN = "test"
DATABASE_PATH = os.environ.get("TEST_DATABASE_PATH", os.path.join(_HERE, ".data", "processor.db"))
STOCK_SYNC_INTERVAL = int(os.environ.get("TEST_STOCK_SYNC_INTERVAL", "5"))
