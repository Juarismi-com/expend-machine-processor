from env import APP_PLATFORM

if (APP_PLATFORM == "raspberry"):
    from services.gpio_service import activate_rele 

def select_option(option):
    print('prueba')
    if (APP_PLATFORM == "raspberry"):
        if (option == 1):
            activate_rele(17, 8)
            
        if (option == 2):
            activate_rele(26, 5)

    return option
