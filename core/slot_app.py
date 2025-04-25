from libs.slots import Slots
from db import obtener_productos
# Crear instancia

def initialize_slot():
    try:
        slots = Slots()

        # Habilitar salidas
        slots.enable_outputs(True)
        
        # Activar un slot (ejemplo: slot 25 por 1 segundo)
        slots.activate_slot(9, 3.0)
        
        # Deshabilitar salidas
        slots.enable_outputs(False)

    except Exception as e:
        print(e)
    except KeyboardInterrupt:
        print("Programa interrumpido")
    finally:
        slots.cleanup()



def active_slot(key):

    #slots = Slots()
    #slots.enable_outputs(True)
    #slots.activate_slot(key, 3.0)
    producto = obtener_productos(key)
    return producto
