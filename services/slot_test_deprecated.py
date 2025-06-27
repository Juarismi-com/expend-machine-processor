# -*- coding: utf-8 -*-

import RPi.GPIO as GPIO
import time
import sys

# Diccionario: nombre del relé → número de GPIO
relays = {
    "rele_1": 17,
    "rele_2": 18,
    "rele_3": 27,
    "rele_4": 22,
    "rele_5": 23,
    "rele_6": 24,
    "rele_7": 12,
    "rele_8": 16,
    "rele_9": 4,
    "rele_10": 5,
    "rele_11": 6,
    "rele_12": 13,
    "rele_13": 19,
    "rele_14": 26,
    "rele_15": 20,
    "rele_16": 21
}

relay_pins = [17, 18, 27, 22, 23, 24, 12, 16, 4, 5, 6, 13, 19, 26, 20, 21]

# Configuración inicial de los pines
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(True)


def activar_reles_secuencialmente(tiempo_encendido=1):
    """Activa dos relés, espera y monitoriza un pin de interrupción."""

    try:
        pin = 17
        pin2 = 12
        pin_salida = 25  # Pin para monitorear interrupción

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(True)

        GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(pin2, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(pin_salida, GPIO.IN)

        GPIO.output(pin, GPIO.LOW)
        GPIO.output(pin2, GPIO.LOW)

        time.sleep(5)

        # Espera pero interrumpe si pin 25 cambia
        tiempo_espera = 5
        for _ in range(tiempo_espera * 100):  # 10 ciclos por segundo
            if GPIO.input(pin_salida) == GPIO.HIGH:
                print("Pin 25 en ALTO durante la espera. Terminando proceso.")
                GPIO.output(pin, GPIO.HIGH)
                GPIO.output(pin2, GPIO.HIGH)
                return
            time.sleep(0.01)

    except RuntimeError as e:
        print("\nInterrumpido por el usuario.")
        print(e)

    finally:
        print("finally")
        GPIO.cleanup()


def activar_reles_secuencialmente_2(tiempo_encendido=1):
    """Activa dos relés y monitoriza un pin de interrupción sin apagar relés."""

    try:
        pin = 17
        pin2 = 12
        pin_salida = 25  # Pin para monitorear interrupción

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(True)

        GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(pin2, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(pin_salida, GPIO.IN)

        GPIO.output(pin, GPIO.LOW)
        GPIO.output(pin2, GPIO.LOW)

        # Espera pero interrumpe si pin 25 cambia
        tiempo_espera = 1
        for _ in range(tiempo_espera * 3):  # 10 ciclos por segundo
            
            if GPIO.input(pin_salida) == GPIO.HIGH:
                print("Pin 25 en ALTO durante la espera. Terminando proceso.")
                return
            time.sleep(0.01)

    except RuntimeError as e:
        print("\nInterrumpido por el usuario.")
        print(e)

    finally:
        print("finally")
        GPIO.cleanup()






def activete_all_reles(tiempo_encendido=1):
    """Activa cada combinación de dos relés uno por uno durante X segundos."""

    for nombre, pin in relays.items():
        for nombre2, pin2 in relays.items():
            try:
                GPIO.setmode(GPIO.BCM)
                GPIO.setwarnings(True)

                GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)
                GPIO.setup(pin2, GPIO.OUT, initial=GPIO.LOW)

                GPIO.output(pin, GPIO.LOW)
                GPIO.output(pin2, GPIO.LOW)

                time.sleep(1)

            except RuntimeError as e:
                print("\nInterrumpido por el usuario.")
                print(e)

            finally:
                print("finally")
                GPIO.cleanup()


def activar_espiral_con_sensor_y_tiempo(tiempo_maximo=10):
    """
    Activa dos relés para expendio y monitoriza sensor en pin 25.
    Si el sensor infrarrojo detecta presencia, se interrumpe el proceso.
    """

    pin_fila = 17       # Relé fila
    pin_columna = 12    # Relé columna
    pin_sensor = 25     # Sensor infrarrojo de movimiento

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
            if GPIO.input(pin_sensor) == GPIO.HIGH:
                print("Movimiento detectado. Interrumpiendo expendio.")
                break

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



def probar_sensor_infrarrojo():
    """
    Monitorea continuamente el sensor en el pin 25 e imprime el estado.
    Usa Ctrl + C para detener.
    """

    pin_sensor = 25  # Número de pin para el sensor

    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(True)
        GPIO.setup(pin_sensor, GPIO.IN)

        print("Leyendo el sensor infrarrojo en pin 25. Presiona Ctrl + C para salir.")

        while True:
            estado = GPIO.input(pin_sensor)
            print(estado)
            
            if estado == GPIO.LOW:
                print("➡ Movimiento detectado.")
            else:
                print("⏸ Sin movimiento.")

            time.sleep(0.5)  # Lectura cada medio segundo

    except KeyboardInterrupt:
        print("\nLectura interrumpida por el usuario.")

    finally:
        GPIO.cleanup()
        print("GPIO limpio. Finalizado.")


# Ejecutar si se llama directamente
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Debes indicar la función: 'sensor' o 'expender'")
        sys.exit(1)

    try:
        opcion = sys.argv[1]

        if opcion == "1":
            activar_espiral_con_sensor_y_tiempo(tiempo_maximo=10)
        elif opcion == "2":
            probar_sensor_infrarrojo()
        else:
            print("Opción no válida. Usa 1 (sensor) o 2 (expender).")
           
    except KeyboardInterrupt:
        print("\nInterrumpido por el usuario.")
    finally:
        print("finaly")