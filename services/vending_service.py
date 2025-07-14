from env import API_URL, MACHINE_ID, BANCARD_API_URL, APP_PLATFORM
from flask import jsonify
import requests
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configuración de logging
logger = logging.getLogger(__name__)

# Constantes
DEFAULT_TIMEOUT = 20
ESPIRAL_TIEMPO_SEGUNDOS = 5

# Creamos una sesión HTTP reutilizable con reintentos automáticos
retry_strategy = Retry(
    total=3,  # cantidad máxima de reintentos
    backoff_factor=1,  # tiempo de espera exponencial entre reintentos (1s, 2s, 4s...)
    status_forcelist=[502, 503, 504],  # códigos de error que activan retry
    allowed_methods=["GET", "POST", "PUT", "PATCH"]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session = requests.Session()
session.mount("http://", adapter)
session.mount("https://", adapter)

if (APP_PLATFORM == "raspberry"):
    from services.slot_service import activar_espiral_con_sensor_y_tiempo

def handle_response(res):
    try:
        return jsonify(res.json()), res.status_code
    except ValueError:
        return jsonify({'error': 'Respuesta no es JSON válida'}), 500

def create_pending_vending(slot_num):
    payload = {
        'slot_num': slot_num,
        'maquina_id': MACHINE_ID
    }

    try:
        res = session.post(API_URL + '/ventas', json=payload, timeout=DEFAULT_TIMEOUT)
        return handle_response(res)
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500

def get_vending(vending_id):
    try:
        res = session.patch(API_URL + '/ventas/' + vending_id, timeout=DEFAULT_TIMEOUT)
        return handle_response(res)
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500

def get_vending_by_id(vending_id):
    try:
        response = session.get(f"{API_URL}/ventas/{vending_id}", timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}

def confirm_vending_card(vending_id, metodo_pago="TARJETA"):
    try:
        # traemos info de la venta remota
        response_vendind_pending = get_vending_by_id(vending_id)

        if 'error' in response_vendind_pending:
            return {"message": response_vendind_pending['error']}

        fila = response_vendind_pending.get('config', {}).get('fila')
        columna = response_vendind_pending.get('config', {}).get('columna')

        if fila is None or columna is None:
            return {"message": "Configuración de fila o columna no válida"}

        # enviamos a bancard
        # seleccionamos tipo de venta a generaar
        payload_bancard = {
            'facturaNro': response_vendind_pending['id'],
            'monto': int(float(response_vendind_pending.get('precio_venta', 0))),
            'montoVuelto': 0
        }

        if (metodo_pago == "qr"):
            res_bancard = session.post(BANCARD_API_URL + "/pos/venta-qr", json=payload_bancard, timeout=DEFAULT_TIMEOUT)
        else:
            res_bancard = session.post(BANCARD_API_URL + "/pos/venta-ux", json=payload_bancard, timeout=DEFAULT_TIMEOUT)

        # si no se pudo procesar el pago
        if res_bancard.status_code != 200:
            return {
                "message": "No se pudo realizar la venta"
            }

        # si estamos en raspberry y se proceso el pago
        if (APP_PLATFORM == "raspberry"):
            activar_espiral_con_sensor_y_tiempo(fila, columna, ESPIRAL_TIEMPO_SEGUNDOS)

        payload_success = {
            "metodo_pago": metodo_pago,
            "estado": "A"
        }

        res_update_vending = session.put(API_URL + "/ventas/" + vending_id, json=payload_success, timeout=DEFAULT_TIMEOUT)

        return res_update_vending.json()
    except requests.exceptions.Timeout:
        return {
            "message": "No se pudo conectar con el servidor de bancard"
        }
    except Exception as e:
        return {
            "message": str(e)
        }
