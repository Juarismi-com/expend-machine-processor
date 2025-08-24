from env import APP_PLATFORM

if (APP_PLATFORM == "raspberry"):
    from services.gpio_service import activate_rele 

def select_option(option):
    if (APP_PLATFORM == "raspberry"):
        if (option == 1):
            activate_rele(17, 5)
            
        if (option == 2):
            activate_rele(27, 5)

    return option
