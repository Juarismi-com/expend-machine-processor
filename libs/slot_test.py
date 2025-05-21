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


# Configuración inicial de los pines
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

for gpio_pin in relays.values():
   GPIO.setup(gpio_pin, GPIO.OUT, initial=GPIO.LOW)
#   GPIO.output(gpio_pin, GPIO.HIGH)  # HIGH para desactivar (si el relé es activo en LOW)

def activar_reles_secuencialmente(tiempo_encendido=1):
   """Activa cada relé uno por uno durante X segundos, luego lo apaga."""
   #GPIO.setup(pin, GPIO.OUT)
   for nombre, pin in relays.items():
      
      print(GPIO.LOW)
      GPIO.output(pin, GPIO.LOW)
      print(f"{nombre} (GPIO {pin}) inicializado en LOW (relé apagado)")
      time.sleep(5)
      print(f"{nombre} (GPIO {pin}) inicializado en HIGH (relé apagado)")
      GPIO.output(pin, GPIO.HIGH)
      time.sleep(5)

# Ejecutar si se llama directamente
if __name__ == "__main__":
   try:
      activar_reles_secuencialmente(tiempo_encendido=1)
   except KeyboardInterrupt:
      print("\nInterrumpido por el usuario.")
   finally:
      GPIO.cleanup()
