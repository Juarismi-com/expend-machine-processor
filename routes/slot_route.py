from flask import Blueprint, jsonify
from env import API_URL, APP_PLATFORM, MACHINE_ID
import requests

slot_bp = Blueprint('slots', __name__)

if APP_PLATFORM == "raspberry":
    from services.slot_service import activar_espiral_con_sensor_y_tiempo

@slot_bp.route('/<int:slot_num>', methods=['GET'])
def get_slot_by_slot_id(slot_num):
    try:
        response = requests.get(f"{API_URL}/maquinas/{MACHINE_ID}/slot/{slot_num}", timeout=5)
        response.raise_for_status()
        data = response.json()

        config = data.get('config')
        if not config or 'fila' not in config or 'columna' not in config:
            return jsonify({"error": "Datos de slot incompletos"}), 500

        fila = config['fila']
        columna = config['columna']

        print("prueba")
        if APP_PLATFORM == "raspberry":
            print(APP_PLATFORM)
            activar_espiral_con_sensor_y_tiempo(fila, columna, 5)

        return jsonify({
            "status": "ok",
            "fila": fila,
            "columna": columna
        })

    except requests.exceptions.RequestException as e:
        error_details = ""
        if e.response is not None:
            try:
                error_details = e.response.json()
            except ValueError:
                error_details = e.response.text

        return jsonify({
            "error": "Error al contactar el servidor central",
            "details": str(e),
            "server_response": error_details
        }), 502

    except ValueError:
        return jsonify({"error": "Respuesta inválida del servidor central (no es JSON)"}), 500

    except Exception as e:
        return jsonify({"error": "Error inesperado", "details": str(e)}), 500
