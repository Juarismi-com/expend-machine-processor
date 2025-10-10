from flask import Blueprint, request, jsonify
from services.dispenser_service import select_option, submit_bancard

bp = Blueprint('dispensers', __name__)

@bp.route('/', methods=['POST'])
def request_option_withouy_pay():
    if request.method == "POST":
        data = request.get_json()
        option = data.get('option')

        select_option(option)
        return data


@bp.route('/submit-bancard', methods=['POST'])
def submit_bancard_pay():
    if request.method == "POST":
        data = request.get_json()
        metodo_pago = data.get('metodo_pago')
        precio = data.get('precio')

        return submit_bancard(precio, metodo_pago)


