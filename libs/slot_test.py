# -*- coding: utf-8 -*-

import RPi.GPIO as GPIO
import time

# Diccionario: nombre del relé → número de GPIO
relays = {
   "rele_1": 4,
   "rele_2": 17,
   "rele_3": 27,
   "rele_4": 22,
   "rele_5": 5,
   "rele_6": 6,
   "rele_7": 13,
   "rele_8": 19,
   "rele_9": 26,
   "rele_10": 18,
   "rele_11": 23,
   "rele_12": 24,
   "rele_13": 25,
   "rele_14": 12,
   "rele_15": 16,
   "rele_16": 20,
}

# Configuración inicial de los pines
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

for gpio_pin in relays.values():
   GPIO.setup(gpio_pin, GPIO.OUT)
   GPIO.output(gpio_pin, GPIO.HIGH)  # HIGH para desactivar (si el relé es activo en LOW)

def activar_reles_secuencialmente(tiempo_encendido=1):
   """Activa cada relé uno por uno durante X segundos, luego lo apaga."""
   for nombre, gpio in relays.items():
      print(f"Activando {nombre} (GPIO {gpio})")
      GPIO.output(gpio, GPIO.LOW)  # LOW para activar el relé
      time.sleep(tiempo_encendido)
      GPIO.output(gpio, GPIO.HIGH)  # Apagar el relé
      print(f"{nombre} desactivado\n")
      time.sleep(0.5)

# Ejecutar si se llama directamente
if __name__ == "__main__":
   try:
      activar_reles_secuencialmente(tiempo_encendido=1)
   except KeyboardInterrupt:
      print("\nInterrumpido por el usuario.")
   finally:
      GPIO.cleanup()
