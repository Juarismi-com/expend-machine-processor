from flask import Blueprint, request
from services import product_service
bp = Blueprint('products', __name__)

@bp.route('/', methods=['GET', 'POST'])
def get_product():
    if request.method == "POST":
        return "pass"
    
    return product_service.get_product()


def update_product():
    return "CREATE PATH"


def delete_product():
    return "DELETE PRODUCT"