from flask import Blueprint

bp = Blueprint('slots', __name__)

@bp.route('/:uuid')
def get_slot_by_uuid():
    return "product list"


@bp.route('/', methods=['POST'])
def reload_slot():
    return "product CREATE"


@bp.route('/', methods=['POST'])
def reload_slot():
    return "product CREATE"
