from env import APP_PLATFORM, BANCARD_API_URL
import random
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


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
        if (option == 1):
            activate_rele(17, 0.5)
            
        if (option == 2):
            activate_rele(18, 0.5)

    return option



## UX es lo mismo que tarjeta o contact less
def submit_bancard(precio, metodo_pago="ux", option=1, payment_url=""):
    try:
        
        # enviamos a bancard
        # seleccionamos tipo de venta a generaar
        payload_bancard = {
            'facturaNro': random.randint(1, 10000),
            'monto': precio,
            'montoVuelto': 0
        }

        if (metodo_pago == "qr"):
            res_bancard = session.post(payment_url + "/pos/venta-qr", json=payload_bancard, timeout=DEFAULT_TIMEOUT)
        else:
            res_bancard = session.post(payment_url + "/pos/venta-ux", json=payload_bancard, timeout=DEFAULT_TIMEOUT)

        # si no se pudo procesar el pago
        if res_bancard.status_code != 200:
            return {
                "message": "En proceso"
            }
        

        select_option(option)
        
        return res_bancard.json()
    except requests.exceptions.Timeout:
        return {
            "message": "No se pudo conectar con el servidor de bancard"
        }
    except Exception as e:
        return {
            "message": str(e)
        }