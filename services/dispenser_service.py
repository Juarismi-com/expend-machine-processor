from env import APP_PLATFORM, BANCARD_API_URL
import random
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging
import aiohttp

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
    logging.info("Ejecutando select_option")

    try:
        if APP_PLATFORM == "raspberry":
            print(option)

            if option == 1:
                activate_rele(17, 0.5)
            elif option == 2:
                activate_rele(18, 0.5)
            else:
                logging.warning(f"Opción no válida: {option}")

    except Exception as e:
        logging.error(f"Error al ejecutar select_option: {e}")

    return option


async def submit_bancard(precio, metodo_pago="ux", option=1, payment_url=""):
    if not payment_url:
        logging.error("URL de pago no proporcionada")
        return {"message": "URL de pago no proporcionada"}

    payment_url = payment_url.rstrip("/")  # Evita // en la URL
    factura_nro = random.randint(1, 10000)

    payload_bancard = {
        'facturaNro': factura_nro,
        'monto': precio,
        'montoVuelto': 0
    }

    try:
        async with aiohttp.ClientSession() as session:
            # --- 1) Método QR ---
            if metodo_pago == "qr":
                async with session.post(
                    f"{payment_url}/pos/venta-qr",
                    json=payload_bancard,
                    timeout=DEFAULT_TIMEOUT
                ) as res_bancard:
                    status = res_bancard.status
                    body_text = await res_bancard.text()

            # --- 2) Método UX ---
            else:
                # POST a /pos/venta-ux
                async with session.post(
                    f"{payment_url}/pos/venta-ux",
                    json=payload_bancard,
                    timeout=DEFAULT_TIMEOUT
                ) as res_venta:
                    if res_venta.status != 200:
                        logging.warning(
                            f"Respuesta no exitosa del pos (venta-ux): "
                            f"Status={res_venta.status}, Body={await res_venta.text()}"
                        )
                        return {
                            "message": "Error en la venta previa",
                            "status": res_venta.status,
                            "detalle": await res_venta.text()
                        }

                    try:
                        data = await res_venta.json()
                    except Exception:
                        text_err = await res_venta.text()
                        logging.error(
                            f"La respuesta del pos (venta-ux) no es JSON: {text_err}"
                        )
                        return {
                            "message": "Respuesta inválida del pos (venta-ux)",
                            "status": res_venta.status,
                            "detalle": text_err
                        }

                # Validar nsu/bin
                nsu = data.get('nsu')
                bin_ = data.get('bin')

                if not nsu or not bin_:
                    logging.error(f"Faltan nsu o bin en la respuesta: {data}")
                    return {
                        "message": "No se pudo obtener nsu/bin para el descuento",
                        "detalle": data
                    }

                # POST a /pos/descuento
                async with session.post(
                    f"{payment_url}/pos/descuento",
                    json={'nsu': nsu, 'bin': bin_, 'monto': precio},
                    timeout=DEFAULT_TIMEOUT
                ) as res_bancard:
                    status = res_bancard.status
                    body_text = await res_bancard.text()

            # --- 3) Verificación final ---
            if status != 200:
                logging.warning(
                    f"Respuesta no exitosa de Bancard: "
                    f"Status={status}, Body={body_text}"
                )
                return {
                    "message": "Error al procesar el pago",
                    "status": status,
                    "detalle": body_text
                }

            try:
                response_json = await res_bancard.json()
            except Exception:
                logging.error(
                    f"La respuesta de Bancard no es JSON: {body_text}"
                )
                return {
                    "message": "Respuesta inválida de Bancard",
                    "status": status,
                    "detalle": body_text
                }

            logging.info("Pago procesado correctamente")
            logging.debug(f"Respuesta JSON de Bancard: {response_json}")

            select_option(option)
            return response_json

    except aiohttp.ClientConnectionError:
        logging.error("Timeout o conexión fallida con Bancard")
        select_option(option)
        return {
            "message": "No se pudo conectar con el servidor de Bancard"
        }

    except Exception as e:
        logging.exception(f"Excepción inesperada en submit_bancard: {e}")
        select_option(option)
        return {
            "message": f"Error inesperado: {str(e)}"
        }
