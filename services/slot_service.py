import RPi.GPIO as GPIO
import time

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