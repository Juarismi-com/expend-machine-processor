from flask import Blueprint, jsonify
from env import APP_PLATFORM, MODO_RELES
from services import stock_service

slot_bp = Blueprint('slots', __name__)

if APP_PLATFORM == "raspberry":
    from services.slot_service import activar_espiral_en_low, activar_espilar_en_high


def _activar(fila, columna, segundos):
    if APP_PLATFORM == "raspberry":
        if MODO_RELES == 1:
            activar_espilar_en_high(fila, columna, segundos)
        else:
            activar_espiral_en_low(fila, columna, segundos)


@slot_bp.route('/config', methods=['GET'])
def get_gpio_config():
    """Configuracion GPIO (fila/columna) descargada del admin, con producto y stock"""
    return jsonify([
        {
            "slot_num": s["slot_num"],
            "producto_id": s["producto_id"],
            "stock": s["stock"],
            "fila": s["fila"],
            "columna": s["columna"],
            "fecha_sync": s["fecha_sync"],
        }
        for s in stock_service.list_slots()
    ])


@slot_bp.route('/<int:slot_num>', methods=['GET'])
def get_slot_by_slot_id(slot_num):
    """Prueba de despacho de un slot con su configuracion GPIO local"""
    slot = stock_service.get_slot(slot_num)
    if slot is None:
        return jsonify({"error": "Slot no sincronizado todavia"}), 404
    if slot['fila'] is None or slot['columna'] is None:
        return jsonify({"error": "Slot sin fila/columna configurada"}), 409

    try:
        _activar(slot['fila'], slot['columna'], 5)
    except Exception as e:
        return jsonify({"error": "Error al activar el slot", "details": str(e)}), 500

    return jsonify({
        "status": "ok",
        "slot_num": slot_num,
        "fila": slot['fila'],
        "columna": slot['columna']
    })


@slot_bp.route('/<int:fila>/<int:columna>', methods=['GET'])
def get_slot_by_fila_columna(fila, columna):
    """Prueba directa de un par de pines (para descubrir el cableado)"""
    try:
        _activar(fila, columna, 20)
        return jsonify({
            "status": "ok",
            "fila": fila,
            "columna": columna
        })
    except Exception as e:
        return jsonify({"error": "Error inesperado", "details": str(e)}), 500
