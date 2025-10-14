from env import APP_PLATFORM, BANCARD_API_URL
import random
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

DEFAULT_TIMEOUT = 300
ESPIRAL_TIEMPO_SEGUNDOS = 5

retry_strategy = Retry(
    total=3,  # cantidad máxima de reintentos
    backoff_factor=1,  # tiempo de espera exponencial entre reintentos (1s, 2s, 4s...)
    status_forcelist=[502, 503, 504],  # códigos de error que activan retry
    allowed_methods=["GET", "POST", "PUT", "PATCH"]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session = requests.Session()
session.mount("http://", adapter)
session.mount("https://", adapter)

if (APP_PLATFORM == "raspberry"):
    from services.gpio_service import activate_rele 

def select_option(option):
    if (APP_PLATFORM == "raspberry"):
        print (option)
        if (option == 1):
            activate_rele(17, 0.5)
            
        if (option == 2):
            activate_rele(18, 0.5)

    return option



## UX es lo mismo que tarjeta o contact less
def submit_bancard(precio, metodo_pago="ux", option=1, payment_url=""):
    if not payment_url:
        logging.error("URL de pago no proporcionada")
        return {"message": "URL de pago no proporcionada"}
    
    try:
        factura_nro = random.randint(1, 10000)
        payload_bancard = {
            'facturaNro': factura_nro,
            'monto': precio,
            'montoVuelto': 0
        }

        endpoint = "/pos/venta-qr" if metodo_pago == "qr" else "/pos/venta-ux"
        url = payment_url + endpoint

        logging.info(f"Enviando solicitud a Bancard: URL={url}, Payload={payload_bancard}")

        res_bancard = session.post(
            url,
            json=payload_bancard,
            timeout=DEFAULT_TIMEOUT
        )

        if res_bancard.status_code != 200:
            logging.warning(
                f"Respuesta no exitosa de Bancard: "
                f"Status={res_bancard.status_code}, Body={res_bancard.text}"
            )
            return {
                "message": "Error al procesar el pago",
                "status": res_bancard.status_code,
                "detalle": res_bancard.text
            }

        logging.info("Pago procesado correctamente, ejecutando select_option")
        select_option(option)

        response_json = res_bancard.json()
        logging.debug(f"Respuesta JSON de Bancard: {response_json}")
        return response_json

    except requests.exceptions.Timeout:
        logging.error("Timeout al conectar con Bancard")
        select_option(option)  # opcional
        return {
            "message": "No se pudo conectar con el servidor de bancard"
        }

    except Exception as e:
        logging.exception(f"Excepción inesperada en submit_bancard: {e}")
        select_option(option)
        return {
            "message": f"Error inesperado: {str(e)}"
        }