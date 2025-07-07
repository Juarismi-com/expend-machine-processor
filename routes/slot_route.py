from flask import Blueprint
from env import API_URL, APP_PLATFORM, MACHINE_ID
import requests;

if (APP_PLATFORM == "raspberry"):
    from services.slot_service import activar_espiral_con_sensor_y_tiempo


bp = Blueprint('slots', __name__)

@bp.route('/<int>:slot_num')
def get_slot_by_slot_id(slot_num):
    response = requests.get(f"{API_URL}/maquinas/{MACHINE_ID}/slot/{slot_num}")
    fila = response['config']['fila']
    columna = response['config']['columna']

    if (APP_PLATFORM == "raspberry"):
        print('entro aca')
        activar_espiral_con_sensor_y_tiempo(fila, columna, 5)


@bp.route('/', methods=['POST'])
def reload_slot():
    return "product CREATE"


@bp.route('/', methods=['POST'])
def reload_slot():
    return "product CREATE"
