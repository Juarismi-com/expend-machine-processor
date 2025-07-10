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
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(True)
        GPIO_initialized = True
        logger.info("GPIO inicializado en modo BCM")


def active_slot(pin1, pin2):
    """Activa cada relé uno por uno durante 5 segundos, luego lo apaga."""
    try:
        init_gpio()

        GPIO.setup(pin1, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(pin2, GPIO.OUT, initial=GPIO.LOW)

        logger.info(f"Activando relés en pines {pin1} y {pin2}")
        GPIO.output(pin1, GPIO.LOW)
        GPIO.output(pin2, GPIO.LOW)

        time.sleep(5)

    except (RuntimeError, KeyboardInterrupt) as e:
        logger.error("Error durante active_slot: %s", e)

    finally:
        logger.info("Limpiando GPIO (active_slot)")
        GPIO.cleanup()


def activar_espiral_con_sensor_y_tiempo(pin_fila, pin_columna, tiempo_maximo=5):
    """
    Activa dos relés para expendio y monitoriza sensor en pin 25.
    Si el sensor infrarrojo detecta presencia, se interrumpe el proceso.
    """
    pin_sensor = 25  # Sensor infrarrojo

    try:
        init_gpio()

        GPIO.setup(pin_fila, GPIO.OUT, initial=GPIO.HIGH)
        GPIO.setup(pin_columna, GPIO.OUT, initial=GPIO.HIGH)
        GPIO.setup(pin_sensor, GPIO.IN)

        GPIO.output(pin_fila, GPIO.LOW)
        GPIO.output(pin_columna, GPIO.LOW)

        logger.info(f"Expedición en proceso (tiempo máximo: {tiempo_maximo}s)")

        tiempo_inicio = time.time()

        while True:
            sensor_estado = GPIO.input(pin_sensor)
            logger.debug(f"Sensor pin {pin_sensor} estado: {sensor_estado}")

            if sensor_estado == GPIO.HIGH:
                logger.info("Movimiento detectado. Interrumpiendo expendio.")
                break

            if time.time() - tiempo_inicio >= tiempo_maximo:
                logger.info("Tiempo máximo alcanzado. Terminando expendio.")
                break

            time.sleep(0.01)

    except (RuntimeError, KeyboardInterrupt) as e:
        logger.error("Error durante activar_espiral: %s", e)

    finally:
        GPIO.output(pin_fila, GPIO.HIGH)
        GPIO.output(pin_columna, GPIO.HIGH)
        logger.info("Proceso finalizado, relés desactivados.")
        GPIO.cleanup()
