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
    

def confirm_vending_qr(vending_id, fila, columna):
    
    # Invocar a bancard

    # si bancard da satisfactorio
        # enviar a remoto
        # activar maquina con el valor del config
    # sino 
        # mensaje
        

    # @todo de momento queda 
    # guardar en local

    """
    
    """

    payload_bancard = {
       'facturaNro': 123,
       'monto': 1,
       'montoVuelto': 0
    }

    res  = requests.post("http://192.168.100.16:3000/pos/venta-qr", json=payload_bancard)
    print('probando ')
    return jsonify(res.json())


def get_vending(vending_id):
    try:
        res = requests.patch(API_URL + '/ventas/' + vending_id)
        if res.ok:
            return jsonify(res.json())
        else:
            return jsonify(res.json()), 500
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500
    



def confirm_vending_card(vending_id):
    
    # Invocar a bancard

    # si bancard da satisfactorio
        # enviar a remoto
        # activar maquina con el valor del config
    # sino 
        # mensaje
        

    # @todo de momento queda 
    # guardar en local
    

    payload_bancard = {
       'facturaNro': 123,
       'monto': 1
    }

    res  = requests.post("http://192.168.100.16:3000/pos/venta-ux", json=payload_bancard)
    print('probando ')
    return jsonify(res.json())


    """try:
        res = requests.patch(API_URL + '/ventas' + vending_id, json=payload)
        if res.ok:
            return jsonify(res.json())
        else:
            return jsonify(res.json()), 500
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500
    """