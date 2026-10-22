from flask import Blueprint, request, jsonify
from services.vending_service import create_pending_vending, confirm_vending_card
from services import venta_local_service
bp = Blueprint('vending', __name__)


@bp.route("/", methods=['GET', 'POST', 'OPTIONS'])
def create_vending():
    """POST: registra una venta pendiente en la maquina. GET: ultimas ventas locales."""

    if request.method == 'GET':
        return jsonify(venta_local_service.list_ventas())

    if request.method != 'POST':
        return 'pass'

    data = request.get_json()
    slot_num = data.get('slot_num')

    if slot_num is None:
        return jsonify({"error":"slot_num is undefined"}), 400

    body, status = create_pending_vending(int(slot_num))
    return jsonify(body), status



@bp.route("/<int:vending_id>/<string:metodo_pago>", methods=['PATCH','OPTIONS'])
def update_vending_card(vending_id, metodo_pago):
    """Cobra la venta local con el POS (qr o tarjeta) y despacha el producto

    Return: la venta aceptada, o un json con message y bancard_status si no se concreto
    """

    if request.method != 'PATCH':
        return "pass"

    return jsonify(confirm_vending_card(vending_id, metodo_pago))
