import RPi.GPIO as GPIO
import time
import logging
from env import PIN_INTRARROJO

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


def activar_espilar_en_high(pin_fila, pin_columna, tiempo_maximo=5):
    pin_sensor = PIN_INTRARROJO     # Sensor infrarrojo de movimiento

    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(True)

        # Configurar relés y sensor con pull-down
        GPIO.setup(pin_fila, GPIO.OUT, initial=GPIO.HIGH)
        GPIO.setup(pin_columna, GPIO.OUT, initial=GPIO.HIGH)
        GPIO.setup(pin_sensor, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

        # Leer estado inicial del sensor antes de activar relés
        print(f"Estado inicial del sensor (pin {pin_sensor}): {GPIO.input(pin_sensor)}")
        time.sleep(0.1)  # Breve espera para estabilizar

        # Activar relés (LOW activa en la mayoría de módulos)
        GPIO.output(pin_fila, GPIO.LOW)
        GPIO.output(pin_columna, GPIO.LOW)

        print(f"Expedición en proceso, monitoreando sensor en pin {pin_sensor} por {tiempo_maximo} segundos...")

        tiempo_inicio = time.time()
        lecturas_consecutivas = 0
        umbral_confirmacion = 5

        while True:
            if GPIO.input(pin_sensor):
                lecturas_consecutivas += 1
            else:
                lecturas_consecutivas = 0

            if lecturas_consecutivas >= umbral_confirmacion:
                print("Sensor activado (movimiento detectado). Cancelando proceso.")
                break

            if time.time() - tiempo_inicio >= tiempo_maximo:
                print(f"Tiempo máximo de {tiempo_maximo} segundos alcanzado. Terminando expendio.")
                break

            time.sleep(0.01)

    except RuntimeError as e:
        print("\nError en el proceso.")
        print(e)

    finally:
        # Desactivar relés (HIGH = desactivado en la mayoría)
        GPIO.output(pin_fila, GPIO.HIGH)
        GPIO.output(pin_columna, GPIO.HIGH)

        print("Proceso finalizado, relés desactivados.")
        GPIO.cleanup()


def activar_espiral_en_low(pin_fila, pin_columna, tiempo_maximo=5):
    """
    Activa dos relés para expendio y monitoriza sensor en pin definido.
    Si el sensor infrarrojo detecta presencia, se interrumpe el proceso.
    """
    pin_sensor = PIN_INTRARROJO

    try:
        init_gpio()

        # Configurar pines
        GPIO.setup(pin_fila, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(pin_columna, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(pin_sensor, GPIO.IN)

        # Activar relés (o preparar señal)
        GPIO.output(pin_fila, GPIO.LOW)
        GPIO.output(pin_columna, GPIO.LOW)

        logger.info(f"Expedición en proceso (máximo {tiempo_maximo} segundos)")

        tiempo_inicio = time.time()

        while True:
            sensor_estado = GPIO.input(pin_sensor)
            logger.debug(f"Sensor (pin {pin_sensor}) estado: {sensor_estado}")

            if sensor_estado == GPIO.HIGH:
                logger.info("Movimiento detectado por el sensor. Interrumpiendo expendio.")
                break

            if time.time() - tiempo_inicio >= tiempo_maximo:
                logger.info("Tiempo máximo alcanzado. Finalizando expendio.")
                break

            time.sleep(0.01)

    except (RuntimeError, KeyboardInterrupt) as e:
        logger.error("Error durante activar_espiral: %s", e)

    finally:
        # Desactivar relés o señales
        GPIO.output(pin_fila, GPIO.HIGH)
        GPIO.output(pin_columna, GPIO.HIGH)
        logger.info("Proceso finalizado. Relés desactivados.")
        GPIO.cleanup()  # Limpieza segura
        global GPIO_initialized
        GPIO_initialized = False  # Marcar como no inicializado para futuras llamadas


def probar_sensor_infrarrojo():
    """
    Monitorea continuamente el sensor en el pin 25 e imprime el estado.
    Usa Ctrl + C para detener.
    """

    pin_sensor = PIN_INTRARROJO  # Número de pin para el sensor

    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(True)
        GPIO.setup(pin_sensor, GPIO.IN)

        print("Leyendo el sensor infrarrojo en pin 25. Presiona Ctrl + C para salir.")

        while True:
            estado = GPIO.input(pin_sensor)
            logger.info("Movimiento detectado. Interrumpiendo expendio.")
            
            if estado == GPIO.HIGH:
                print("➡ Movimiento detectado.")
            else:
                print("⏸ Sin movimiento.")

            time.sleep(0.5)  # Lectura cada medio segundo

    except KeyboardInterrupt:
        print("\nLectura interrumpida por el usuario.")

    finally:
        GPIO.cleanup()
        print("GPIO limpio. Finalizado.")