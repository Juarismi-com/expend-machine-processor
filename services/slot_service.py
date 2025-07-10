import RPi.GPIO as GPIO
import time
from env import PIN_INTRARROJO


def active_slot(pin1, pin2):
   """Activa cada relé uno por uno durante X segundos, luego lo apaga."""

   try:

      GPIO.setmode(GPIO.BCM)
      GPIO.setwarnings(True)

      GPIO.setup(pin1, GPIO.OUT, initial=GPIO.LOW)
      GPIO.setup(pin2, GPIO.OUT, initial=GPIO.LOW)

      GPIO.output(pin1, GPIO.LOW)
      GPIO.output(pin2, GPIO.LOW)
      
      time.sleep(5)

   except RuntimeError as e:
      print("\nInterrumpido por el usuario.")
      print(e)
   
   finally:
      print("finaly")
      GPIO.cleanup()

def activar_espiral_con_sensor_y_tiempo(pin_fila, pin_columna, tiempo_maximo=5):
    """
    Activa dos relés para expendio y monitoriza sensor en pin 25 o el que fuere.
    Si el sensor infrarrojo detecta presencia, se interrumpe el proceso.
    """
    pin_sensor = 8    # Sensor infrarrojo de movimiento

    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(True)

        # Configuración de relés y sensor
        GPIO.setup(pin_fila, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(pin_columna, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(pin_sensor, GPIO.IN)

        # Activar relés (simulación de expendio)
        GPIO.output(pin_fila, GPIO.LOW)      # LOW → Relé activado (dependiendo del módulo)
        GPIO.output(pin_columna, GPIO.LOW)

        print(f"Expedición en proceso, monitoreando sensor en pin {pin_sensor} por {tiempo_maximo} segundos...")

        tiempo_inicio = time.time()

        while True:
            """if GPIO.input(pin_sensor) == GPIO.HIGH:
                print("Movimiento detectado. Interrumpiendo expendio.")
                break
            """
            if time.time() - tiempo_inicio >= tiempo_maximo:
                print(f"Tiempo máximo de {tiempo_maximo} segundos alcanzado. Terminando expendio.")
                break
            
            time.sleep(0.01)

    except RuntimeError as e:
        print("\nError en el proceso.")
        print(e)

    finally:
        # Apagar los relés
        GPIO.output(pin_fila, GPIO.HIGH)
        GPIO.output(pin_columna, GPIO.HIGH)

        print("Proceso finalizado, relés desactivados.")
        GPIO.cleanup()


