import RPi.GPIO as GPIO
import time
import logging

# Configuración del logger
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
)
logger = logging.getLogger(__name__)


def activate_rele(pin, seconds):
    """Activa cada relé uno por uno durante 5 segundos, luego lo apaga."""
    try:
        GPIO.setmode(GPIO.BCM)
        logger.info("GPIO inicializado en modo BCM")
        GPIO.setwarnings(True)

        GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)
        logger.info(f"Activando relés en pines {pin}")
        
        GPIO.output(pin, GPIO.LOW)
        time.sleep(seconds)
        GPIO.output(pin, GPIO.HIGH)
        

    except (RuntimeError, KeyboardInterrupt) as e:
        logger.error("Error durante activate_rele: %s", e)

    finally:
        logger.info("Limpiando GPIO (activate_rele)")
        GPIO.cleanup()


def deactivce_rele(pin):
    """Desactiva el sistema de rele"""
    try:
        GPIO.setmode(GPIO.BCM)
        logger.info("GPIO inicializado en modo BCM")
        GPIO.setwarnings(True)

        GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)
        logger.info(f"Desactiva relés en pines {pin}")

        GPIO.output(pin, GPIO.HIGH)
        
    except (RuntimeError, KeyboardInterrupt) as e:
        logger.error("Error durante deactivce_rele: %s", e)

    finally:
        logger.info("Limpiando GPIO (deactivce_rele)")
        GPIO.cleanup()
