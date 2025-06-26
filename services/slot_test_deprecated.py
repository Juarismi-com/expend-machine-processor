# -*- coding: utf-8 -*-

import RPi.GPIO as GPIO
import time

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
        for _ in range(tiempo_espera * 100):  # 10 ciclos por segundo
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


def activar_todos_los_reles_2(tiempo_encendido=1):
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


# Ejecutar si se llama directamente
if __name__ == "__main__":
    try:
        activar_reles_secuencialmente(tiempo_encendido=1)
    except KeyboardInterrupt:
        print("\nInterrumpido por el usuario.")
    finally:
        GPIO.cleanup()
