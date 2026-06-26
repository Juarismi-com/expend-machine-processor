from flask import Blueprint, jsonify
from env import API_URL, APP_PLATFORM, MACHINE_ID, MODO_RELES
import requests

slot_bp = Blueprint('slots', __name__)

if APP_PLATFORM == "raspberry":
    from services.slot_service import activar_espiral_en_low, activar_espilar_en_high

@slot_bp.route('/<int:slot_num>', methods=['GET'])
def get_slot_by_slot_id(slot_num):
    try:
        response = requests.get(
            f"{API_URL}/maquinas/{MACHINE_ID}/slot/{slot_num}",
            timeout=5
        )

        response.raise_for_status()

        # Verificar que el servidor devolvió JSON
        content_type = response.headers.get("Content-Type", "")
        if "application/json" not in content_type.lower():
            return jsonify({
                "error": "El servidor central no devolvió JSON",
                "status_code": response.status_code,
                "content_type": content_type,
                "body": response.text
            }), 502

        # Convertir la respuesta a JSON
        try:
            data = response.json()
        except ValueError:
            return jsonify({
                "error": "Respuesta inválida del servidor central (JSON mal formado)",
                "status_code": response.status_code,
                "content_type": content_type,
                "body": response.text
            }), 502

        config = data.get("config")

        if not config:
            return jsonify({
                "error": "El servidor central no devolvió el objeto 'config'",
                "response": data
            }), 500

        fila = config.get("fila")
        columna = config.get("columna")

        if fila is None or columna is None:
            return jsonify({
                "error": "Datos de slot incompletos",
                "response": data
            }), 500

        # ===========================
        # DEBUG
        # ===========================
        print("========================================")
        print(f"[DEBUG] Slot solicitado : {slot_num}")
        print(f"[DEBUG] Config recibida : {config}")
        print(f"[DEBUG] Fila           : {fila} ({type(fila).__name__})")
        print(f"[DEBUG] Columna        : {columna} ({type(columna).__name__})")
        print(f"[DEBUG] Plataforma     : {APP_PLATFORM}")
        print(f"[DEBUG] Modo relés     : {MODO_RELES}")
        print("========================================")

        if APP_PLATFORM == "raspberry":
            if MODO_RELES == 1:
                activar_espilar_en_high(fila, columna, 5)
            else:
                activar_espiral_en_low(fila, columna, 5)

        return jsonify({
            "status": "ok",
            "fila": fila,
            "columna": columna
        })

    except requests.exceptions.Timeout:
        return jsonify({
            "error": "Timeout al contactar el servidor central"
        }), 504

    except requests.exceptions.ConnectionError:
        return jsonify({
            "error": "No fue posible conectarse al servidor central"
        }), 502

    except requests.exceptions.HTTPError as e:
        error_body = None

        if e.response is not None:
            try:
                error_body = e.response.json()
            except ValueError:
                error_body = e.response.text

        return jsonify({
            "error": "El servidor central respondió con un error HTTP",
            "status_code": e.response.status_code if e.response else None,
            "details": str(e),
            "server_response": error_body
        }), 502

    except requests.exceptions.RequestException as e:
        return jsonify({
            "error": "Error al contactar el servidor central",
            "details": str(e)
        }), 502

    except Exception as e:
        print("========================================")
        print("[ERROR] Excepción inesperada")
        print(str(e))
        print("========================================")

        return jsonify({
            "error": "Error inesperado",
            "details": str(e)
        }), 500

@slot_bp.route('/<int:fila>/<int:columna>', methods=['GET'])
def get_slot_by_fila_columna(fila, columna):
    try:
        if APP_PLATFORM == "raspberry":    
            if MODO_RELES == 1:
                activar_espilar_en_high(fila, columna, 20)
            else:
                activar_espiral_en_low(fila, columna, 20)

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