from env import BANCARD_API_URL, APP_PLATFORM, MODO_RELES
import requests
import logging
from services import stock_service, venta_local_service
from services.venta_local_service import VentaError
from services.stock_sync_service import request_sync

# Configuración de logging
logger = logging.getLogger(__name__)

# Constantes
DEFAULT_TIMEOUT = 20
QR_TIMEOUT = 90      # QR requiere que el usuario escanee, necesita más tiempo
TARJETA_TIMEOUT = 60 # tarjeta requiere que el usuario acerque/inserte, necesita más tiempo
ESPIRAL_TIEMPO_SEGUNDOS = 5

if (APP_PLATFORM == "raspberry"):
    from services.slot_service import activar_espiral_en_low, activar_espilar_en_high


# La venta se ejecuta completa en la maquina (sqlite local): no depende de la api.
# El sync en segundo plano la sube a la api (ver stock_sync_service).

def create_pending_vending(slot_num):
    """Registra la venta pendiente localmente. Retorna (body, status)."""
    try:
        return venta_local_service.crear_venta(slot_num), 200
    except VentaError as e:
        return {"message": e.message}, e.status

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

def _despachar(fila, columna, slot_num):
    _activar_rele(fila, columna)
    if not stock_service.descontar_stock(slot_num):
        logger.warning("No se pudo descontar stock local (slot_num=%s)", slot_num)

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

def _error(message, status, **extra):
    # bancard_status: el front lo usa para mostrar el error al cliente
    return {"message": message, "bancard_status": status, **extra}

def confirm_vending_card(vending_id, metodo_pago="TARJETA"):
    """Cobra con el POS, despacha y confirma la venta local."""
    try:
        venta_local_service.tomar_venta(vending_id)
    except VentaError as e:
        return _error(e.message, e.status)

    venta = venta_local_service.get_venta(vending_id)
    slot = stock_service.get_slot(venta['slot_num'])
    if slot is None or slot['fila'] is None or slot['columna'] is None:
        venta_local_service.finalizar_venta(vending_id, "R", metodo_pago, "Slot sin fila/columna")
        return _error("Configuración de fila o columna no válida", 500)

    monto = int(float(venta['precio_venta']))

    try:
        if metodo_pago == "qr":
            error = _cobrar_qr(vending_id, monto)
        else:
            error = _cobrar_tarjeta(vending_id, monto)
    except requests.exceptions.Timeout:
        logger.error("Timeout en request a Bancard (vending_id=%s)", vending_id)
        error = _error("Timeout contra servidor de Bancard", 504)
    except Exception as e:
        logger.exception("Error inesperado en confirm_vending_card (vending_id=%s): %s", vending_id, str(e))
        error = _error(str(e), 500)

    if error:
        venta_local_service.finalizar_venta(vending_id, "R", metodo_pago, error["message"])
        request_sync()
        return error

    _despachar(slot['fila'], slot['columna'], venta['slot_num'])
    venta = venta_local_service.finalizar_venta(vending_id, "A", metodo_pago)
    request_sync()
    return venta

def _cobrar_qr(vending_id, monto):
    """Retorna None si el pago fue aprobado, o el error."""
    payload = {
        "facturaNro": int(vending_id),
        "monto": monto,
        "montoVuelto": 0
    }
    res = _bancard_post(BANCARD_API_URL + "/pos/venta-qr", payload, timeout=QR_TIMEOUT)

    if res.status_code == 200:
        return None

    logger.warning("Pago QR no satisfactorio (vending_id=%s status=%s): %s",
                   vending_id, res.status_code, res.text)
    return _error("No se pudo confirmar la venta", res.status_code, bancard_response=res.text)

def _cobrar_tarjeta(vending_id, monto):
    """Retorna None si el pago fue aprobado, o el error."""
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
        return _error("No se pudo iniciar la venta con tarjeta", res_paso1.status_code,
                      bancard_response=res_paso1.text)

    try:
        paso1_json = res_paso1.json()
    except Exception:
        return _error("Respuesta del paso 1 no es JSON válida", 502, raw=res_paso1.text)

    nsu = paso1_json.get("nsu")
    bin_ = paso1_json.get("bin")
    if nsu is None or bin_ is None:
        logger.warning("Paso 1 tarjeta no retornó nsu/bin (vending_id=%s): %s", vending_id, paso1_json)
        return _error("Respuesta del paso 1 no contiene nsu o bin", 502, bancard_response=paso1_json)

    # Paso 2: confirmar venta con NSU y BIN
    payload_paso2 = {
        "nsu": nsu,
        "bin": bin_,
        "monto": monto
    }
    res_paso2 = _bancard_post(BANCARD_API_URL + "/pos/descuento", payload_paso2)

    if res_paso2.status_code == 200:
        return None

    logger.warning("Paso 2 tarjeta fallido (vending_id=%s status=%s): %s",
                   vending_id, res_paso2.status_code, res_paso2.text)
    return _error("No se pudo confirmar la venta con tarjeta", res_paso2.status_code,
                  bancard_response=res_paso2.text)
