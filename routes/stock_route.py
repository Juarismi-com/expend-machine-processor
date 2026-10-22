from flask import Blueprint, jsonify
import requests
from services import stock_service
from services.stock_sync_service import sync_stock

bp = Blueprint('stock', __name__)


@bp.route('/', methods=['GET'])
def list_stock():
    """Stock local de todos los slots"""
    return jsonify(stock_service.list_slots())


@bp.route('/<int:slot_num>', methods=['GET'])
def get_stock(slot_num):
    slot = stock_service.get_slot(slot_num)
    if slot is None:
        return jsonify({"error": "Slot no sincronizado"}), 404
    return jsonify(slot)


@bp.route('/sync', methods=['POST'])
def force_sync():
    """Fuerza un ciclo de sincronizacion (ej. luego de cargar una reposicion)"""
    try:
        return jsonify(sync_stock())
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "No se pudo sincronizar con la api", "details": str(e)}), 502
