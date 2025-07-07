from flask import Blueprint, request, jsonify
from services.vending_service import create_pending_vending, confirm_vending_card
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



@bp.route("/<int:vending_id>/<string:metodo_pago>", methods=['PATCH'])
def update_vending_card(vending_id, metodo_pago):
    """Actualiza una venta si se concreto, rechazo o se cancelo
    
    Keyword arguments:
    argument -- description
    Return: Retorna un json confirmado o rechanzado la venta
    """
    
    if request.method != 'PATCH':
        return "pass"

    return confirm_vending_card(vending_id, metodo_pago)


