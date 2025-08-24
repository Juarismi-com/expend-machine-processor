import RPi.GPIO as GPIO
import time
import logging

# Configuración del logger
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Bandera para no repetir inicialización
GPIO_initialized = False

def init_gpio():
    global GPIO_initialized
    if not GPIO_initialized:
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(True)
            GPIO_initialized = True
            logger.info("GPIO inicializado en modo BCM")
        except RuntimeError as e:
            logger.error("Fallo al inicializar GPIO: %s", e)
    else:
        logger.debug("GPIO ya estaba inicializado")


def activate_rele(pin, seconds):
    """Activa cada relé uno por uno durante 5 segundos, luego lo apaga."""
    try:
        init_gpio()

        GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)
        logger.info(f"Activando relés en pines {pin}")
        
        GPIO.output(pin, GPIO.LOW)
        time.sleep(seconds)
        

    except (RuntimeError, KeyboardInterrupt) as e:
        logger.error("Error durante activate_rele: %s", e)

    finally:
        logger.info("Limpiando GPIO (activate_rele)")
        GPIO.cleanup()

