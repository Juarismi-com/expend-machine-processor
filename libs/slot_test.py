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

#for gpio_pin in relays.values():
   
#   GPIO.output(gpio_pin, GPIO.HIGH)  # HIGH para desactivar (si el relé es activo en LOW)

def activar_reles_secuencialmente(tiempo_encendido=1):
   """Activa cada relé uno por uno durante X segundos, luego lo apaga."""
   #GPIO.setup(pin, GPIO.OUT)


   for nombre, pin in relays.items():
      for nombre2, pin2 in relays.items():
         try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(True)

            GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)
            GPIO.setup(pin2, GPIO.OUT, initial=GPIO.LOW)
            GPIO.output(pin, GPIO.LOW)
            GPIO.output(pin2, GPIO.LOW)
            #print(f"{nombre} (GPIO {pin}) inicializado en LOW (relé prendido)")
            time.sleep(1)

         #print(f"{nombre} (GPIO {pin}) inicializado en high (relé prendido)")
         #GPIO.cleanup()
         except RuntimeError as e:
            print("\nInterrumpido por el usuario.")
            print(e)
         finally:
            print("finaly")
            GPIO.cleanup()
      
      
      
   """GPIO.setup(17, GPIO.OUT)
   GPIO.output(pin, GPIO.LOW)
   estados = [GPIO.LOW, GPIO.HIGH, GPIO.HIGH, GPIO.HIGH, GPIO.HIGH, GPIO.HIGH, GPIO.LOW, GPIO.HIGH, GPIO.HIGH, GPIO.HIGH, GPIO.HIGH, GPIO.HIGH, GPIO.HIGH, GPIO.HIGH, GPIO.HIGH, GPIO.HIGH]
   
   for i, estado in enumerate(estados):
      GPIO.output(17, estado)"""
   

# Ejecutar si se llama directamente
if __name__ == "__main__":
   try:
      activar_reles_secuencialmente(tiempo_encendido=1)
   except KeyboardInterrupt:
      print("\nInterrumpido por el usuario.")
   finally:
      GPIO.cleanup()
