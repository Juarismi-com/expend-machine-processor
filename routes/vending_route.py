from flask import Blueprint, request, jsonify
from services.vending_service import create_pending_vending, confirm_vending_qr, confirm_vending_card
bp = Blueprint('vending', __name__)


@bp.route("/", methods=['GET', 'POST'])
def create_vending():
    
    if request.method != 'POST':
        return 'pass'
    
    data = request.get_json()
    slot_num = data.get('slot_num')

    if slot_num is None:
        return jsonify({"error":"slot_num is undefined"}), 400 

    return create_pending_vending(slot_num)


@bp.route("/<int:vending_id>", methods=['PATCH'])
def update_vending_qr(vending_id, fila, columna):
    if request.method != 'PATCH':
        return "pass"

    return confirm_vending_qr(vending_id, fila, columna)


@bp.route("/<int:vending_id>/card", methods=['PATCH'])
def update_vending_card(vending_id):
    if request.method != 'PATCH':
        return "pass"

    return confirm_vending_card(vending_id)