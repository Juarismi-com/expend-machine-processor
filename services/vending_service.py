from env import API_URL, MACHINE_ID, BANCARD_API_URL
from flask import jsonify
import requests


def create_pending_vending(slot_num):
    payload = {
       'slot_num': slot_num,
       'maquina_id': MACHINE_ID
    }

    try:
        res = requests.post(API_URL + '/ventas', json=payload)
        if res.ok:
            return jsonify(res.json())
        else:
            return jsonify(res.json()), 500
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500
    

def confirm_vending(vending_id):
    return jsonify(vending_id)
    # Invocar a bancard

    # si bancard da satisfactorio
        # enviar a remoto
        # activar maquina con el valor del config
    # sino 
        # mensaje
        

    # @todo de momento queda 
    # guardar en local


    payload = {
       'metodo_pago': slot_num,
       'maquina_id': MACHINE_ID
    }

    try:
        res = requests.patch(API_URL + '/ventas' + vending_id, json=payload)
        if res.ok:
            return jsonify(res.json())
        else:
            return jsonify(res.json()), 500
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500