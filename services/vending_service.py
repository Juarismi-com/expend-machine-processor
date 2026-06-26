from env import API_URL, MACHINE_ID, BANCARD_API_URL, APP_PLATFORM, MODO_RELES
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
    from services.slot_service import activar_espiral_en_low, activar_espilar_en_high

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
        # 1. traer venta
        response_vendind_pending = get_vending_by_id(vending_id)

        if 'error' in response_vendind_pending:
            return {"message": response_vendind_pending['error']}

        fila = response_vendind_pending.get('config', {}).get('fila')
        columna = response_vendind_pending.get('config', {}).get('columna')

        if fila is None or columna is None:
            return {"message": "Configuración de fila o columna no válida"}

        # 2. payload bancard (IMPORTANTE: id real)
        payload_bancard = {
            "facturaNro": int(vending_id),
            "monto": int(float(response_vendind_pending.get('precio_venta', 0))),
            "montoVuelto": 0
        }

        # 3. URL según método
        url = (
            BANCARD_API_URL + "/pos/venta-qr"
            if metodo_pago == "qr"
            else BANCARD_API_URL + "/pos/venta-ux"
        )

        # 4. headers (ESTO era lo que faltaba)
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "PostmanRuntime/7.36.0"
        }

        # 5. request bancard (mejor sin session para evitar estado raro)
        res_bancard = requests.post(
            url,
            json=payload_bancard,
            headers=headers,
            timeout=DEFAULT_TIMEOUT
        )

        # 6. debug fuerte (solo útil en desarrollo)
        print("\n========== BANCARD DEBUG ==========")
        print("URL:", url)
        print("PAYLOAD:", payload_bancard)
        print("STATUS:", res_bancard.status_code)
        print("HEADERS:", dict(res_bancard.headers))
        print("RAW TEXT:", res_bancard.text)

        bancard_json = None
        try:
            bancard_json = res_bancard.json()
            print("JSON:", bancard_json)
        except Exception as e:
            print("JSON ERROR:", str(e))
        print("===================================\n")

        # 7. error bancard
        if res_bancard.status_code != 200:
            return {
                "message": "No se pudo confirmar la venta",
                "bancard_status": res_bancard.status_code,
                "bancard_response": res_bancard.text,
                "bancard_json": bancard_json
            }

        # 8. hardware raspberry
        if APP_PLATFORM == "raspberry":
            if MODO_RELES == 1:
                activar_espilar_en_high(fila, columna, ESPIRAL_TIEMPO_SEGUNDOS)
            else:
                activar_espiral_en_low(fila, columna, ESPIRAL_TIEMPO_SEGUNDOS)

        # 9. actualizar venta
        payload_success = {
            "metodo_pago": metodo_pago,
            "estado": "A"
        }

        res_update_vending = session.put(
            API_URL + "/ventas/" + vending_id,
            json=payload_success,
            timeout=DEFAULT_TIMEOUT
        )

        try:
            return res_update_vending.json()
        except Exception:
            return {
                "message": "Venta actualizada pero respuesta no es JSON",
                "raw": res_update_vending.text
            }

    except requests.exceptions.Timeout:
        return {"message": "Timeout contra servidor de Bancard"}

    except Exception as e:
        return {"message": str(e)}