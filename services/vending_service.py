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
QR_TIMEOUT = 90      # QR requiere que el usuario escanee, necesita más tiempo
TARJETA_TIMEOUT = 60 # tarjeta requiere que el usuario acerque/inserte, necesita más tiempo
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

def _activar_rele(fila, columna):
    logger.info("_activar_rele llamado: fila=%s columna=%s platform=%s", fila, columna, APP_PLATFORM)
    if APP_PLATFORM == "raspberry":
        logger.info("Activando relé: fila=%s columna=%s modo=%s", fila, columna, MODO_RELES)
        try:
            if MODO_RELES == 1:
                activar_espilar_en_high(fila, columna, ESPIRAL_TIEMPO_SEGUNDOS)
            else:
                activar_espiral_en_low(fila, columna, ESPIRAL_TIEMPO_SEGUNDOS)
            logger.info("Relé activado correctamente: fila=%s columna=%s", fila, columna)
        except Exception as e:
            logger.error("Error al activar relé (fila=%s columna=%s): %s", fila, columna, str(e))
    else:
        logger.warning("Relé NO activado: APP_PLATFORM='%s' (debe ser 'raspberry')", APP_PLATFORM)

def _confirmar_venta(vending_id, metodo_pago):
    payload_success = {"metodo_pago": metodo_pago, "estado": "A"}
    res = session.put(
        API_URL + "/ventas/" + str(vending_id),
        json=payload_success,
        timeout=DEFAULT_TIMEOUT
    )
    try:
        return res.json()
    except Exception:
        return {"message": "Venta actualizada pero respuesta no es JSON", "raw": res.text}

def _bancard_post(url, payload, timeout=DEFAULT_TIMEOUT):
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "PostmanRuntime/7.36.0"
    }
    logger.info("Enviando request a Bancard: url=%s payload=%s", url, payload)
    res = requests.post(url, json=payload, headers=headers, timeout=timeout)
    logger.info("Respuesta Bancard: status=%s body=%s", res.status_code, res.text)
    return res

def confirm_vending_card(vending_id, metodo_pago="TARJETA"):
    try:
        venta = get_vending_by_id(vending_id)
        if 'error' in venta:
            return {"message": venta['error']}

        fila = venta.get('config', {}).get('fila')
        columna = venta.get('config', {}).get('columna')
        if fila is None or columna is None:
            return {"message": "Configuración de fila o columna no válida"}

        monto = int(float(venta.get('precio_venta', 0)))

        if metodo_pago == "qr":
            return _confirm_vending_qr(vending_id, fila, columna, monto, metodo_pago)
        else:
            return _confirm_vending_tarjeta(vending_id, fila, columna, monto, metodo_pago)

    except requests.exceptions.Timeout:
        logger.error("Timeout en request a Bancard (vending_id=%s)", vending_id)
        return {"message": "Timeout contra servidor de Bancard"}
    except Exception as e:
        logger.exception("Error inesperado en confirm_vending_card (vending_id=%s): %s", vending_id, str(e))
        return {"message": str(e)}

def _confirm_vending_qr(vending_id, fila, columna, monto, metodo_pago):
    payload = {
        "facturaNro": int(vending_id),
        "monto": monto,
        "montoVuelto": 0
    }
    res = _bancard_post(BANCARD_API_URL + "/pos/venta-qr", payload, timeout=QR_TIMEOUT)

    if res.status_code == 200:
        _activar_rele(fila, columna)
        return _confirmar_venta(vending_id, metodo_pago)

    logger.warning("Pago QR no satisfactorio (vending_id=%s status=%s): %s",
                   vending_id, res.status_code, res.text)
    return {
        "message": "No se pudo confirmar la venta",
        "bancard_status": res.status_code,
        "bancard_response": res.text
    }

def _confirm_vending_tarjeta(vending_id, fila, columna, monto, metodo_pago):
    # Paso 1: solicitar venta UX → obtiene NSU y BIN
    payload_paso1 = {
        "facturaNro": int(vending_id),
        "monto": monto,
        "montoVuelto": 0
    }
    res_paso1 = _bancard_post(BANCARD_API_URL + "/pos/venta-ux", payload_paso1, timeout=TARJETA_TIMEOUT)

    if res_paso1.status_code != 200:
        logger.warning("Paso 1 tarjeta fallido (vending_id=%s status=%s): %s",
                       vending_id, res_paso1.status_code, res_paso1.text)
        return {
            "message": "No se pudo iniciar la venta con tarjeta",
            "bancard_status": res_paso1.status_code,
            "bancard_response": res_paso1.text
        }

    try:
        paso1_json = res_paso1.json()
    except Exception:
        return {"message": "Respuesta del paso 1 no es JSON válida", "raw": res_paso1.text}

    nsu = paso1_json.get("nsu")
    bin_ = paso1_json.get("bin")
    if nsu is None or bin_ is None:
        logger.warning("Paso 1 tarjeta no retornó nsu/bin (vending_id=%s): %s", vending_id, paso1_json)
        return {"message": "Respuesta del paso 1 no contiene nsu o bin", "bancard_response": paso1_json}

    # Paso 2: confirmar venta con NSU y BIN
    payload_paso2 = {
        "nsu": nsu,
        "bin": bin_,
        "monto": monto
    }
    res_paso2 = _bancard_post(BANCARD_API_URL + "/pos/descuento", payload_paso2)

    if res_paso2.status_code == 200:
        _activar_rele(fila, columna)
        return _confirmar_venta(vending_id, metodo_pago)

    logger.warning("Paso 2 tarjeta fallido (vending_id=%s status=%s): %s",
                   vending_id, res_paso2.status_code, res_paso2.text)
    return {
        "message": "No se pudo confirmar la venta con tarjeta",
        "bancard_status": res_paso2.status_code,
        "bancard_response": res_paso2.text
    }