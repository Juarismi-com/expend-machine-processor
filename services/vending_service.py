from env import API_URL, MACHINE_ID, BANCARD_API_URL
from flask import jsonify
import requests
#from slot_service import activar_espiral_con_sensor_y_tiempo
from services.slot import activar_espiral_con_sensor_y_tiempo

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



def confirm_vending_card(vending_id):
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

    res_bancard = requests.post(BANCARD_API_URL + "/pos/venta-ux", json=payload_bancard)
    res_update_vending = requests.put(API_URL + "/ventas/" + vending_id, json=payload_success)
    
    activar_espiral_con_sensor_y_tiempo(fila, columna, 5)
    if res_bancard == 200:
        print(res_bancard.json())

        payload_success = {
            "metodo_pago": "visa mastercard",
            "estado": "A"
        }
        
        return res_bancard.json()
    else:
        return {
            "message": "No se pudo actualizar la venta"
        }


def get_vending_by_id(vending_id):
    response = requests.get(f"{API_URL}/ventas/{vending_id}")


    # Checking the status code
    if response.status_code == 200:
        return response.json()
    else:
        print(f'Request failed with status code {response.status_code}')
        