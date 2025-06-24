from flask import Blueprint, request

bp = Blueprint('vending', __name__)


@bp.route("/", methods=['GET', 'POST'])
def create_vending():
    return request.method
    if request.method != 'POST':
        return 'pass'
    
    return "method post"


@bp.route("/<int:slot_num>")
def update_vending(slum_num):
    if request.method != 'PATH':
        return "pass"
    

    return slum_num