from env import API_URL, MACHINE_ID, BANCARD_API_URL, APP_PLATFORM
from flask import jsonify
import requests

if (APP_PLATFORM == "raspberry"):
    from services.slot_service import activar_espiral_con_sensor_y_tiempo

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
    

def get_vending(vending_id):
    try:
        res = requests.patch(API_URL + '/ventas/' + vending_id)
        if res.ok:
            return jsonify(res.json())
        else:
            return jsonify(res.json()), 500
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500



def confirm_vending_card(vending_id, metodo_pago="TARJETA"):

    try:
        # traemos info de la venta remota
        response_vendind_pending = get_vending_by_id(vending_id)

        fila = response_vendind_pending['config']['fila']
        columna = response_vendind_pending['config']['columna']

        # enviamos a bancard
        payload_bancard = {
            'facturaNro': response_vendind_pending['id'],
            'monto': int(float(response_vendind_pending['precio_venta'])),
            'montoVuelto': 0
        }

        if (metodo_pago == "QR"):
            res_bancard = requests.post(BANCARD_API_URL + "/pos/venta-qr", json=payload_bancard, timeout=20)
        else:
            res_bancard = requests.post(BANCARD_API_URL + "/pos/venta-ux", json=payload_bancard, timeout=20)
        
        # si no se pudo procesar el pago
        if res_bancard.status_code != 200:
            return {
                "message": "No se pudo actualizar la venta"
            }
        
        # si estamos en raspberry y se proceso el pago
        if (APP_PLATFORM == "raspberry"):
            activar_espiral_con_sensor_y_tiempo(fila, columna, 5)

        payload_success = {
            "metodo_pago": metodo_pago,
            "estado": "A"
        }

        res_update_vending = requests.put(API_URL + "/ventas/" + vending_id, json=payload_success)
        
        return res_update_vending.json()
    except requests.exceptions.Timeout:
        return {
                "message": "No se pudo conectar con el servidor de bancard"
            }
    except Exception as e:
        return {
            "message": e.__doc__
        }
        


def get_vending_by_id(vending_id):
    response = requests.get(f"{API_URL}/ventas/{vending_id}")

    # Checking the status code
    return response.json()
        
        