from flask import Blueprint, request, jsonify
from services.dispenser_service import select_option

bp = Blueprint('dispensers', __name__)

@bp.route('/', methods=['POST'])
def request_option_withouy_pay():
    if request.method == "POST":
        data = request.get_json()
        option = data.get('option')

        select_option(option)
        return data

