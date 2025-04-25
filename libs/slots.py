
try:    
    import board
    import busio
    from adafruit_pca9685 import PCA9685
    import time
    import RPi.GPIO as GPIO
except (ImportError, RuntimeError) as e:
    print("Hardware-specific libraries not available, running in mock mode.")
    GPIO = None 

NUM_ROWS = 6
NUM_COLS = 10
ROW_PINS = list(range(NUM_ROWS))
COL_PINS = list(range(NUM_ROWS, NUM_ROWS + NUM_COLS))
OE_PIN = 17

class Slots:
    def __init__(self, pca_instance=None):
        if pca_instance is None:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(OE_PIN, GPIO.OUT)
            GPIO.output(OE_PIN, GPIO.HIGH)
            i2c = busio.I2C(board.SCL, board.SDA)
            self.pca = PCA9685(i2c)
            self.pca.frequency = 60
        else:
            self.pca = pca_instance
        self.reset_all_pins()
    
    def reset_all_pins(self):
        for pin in ROW_PINS:
            self.pca.channels[pin].duty_cycle = 0xFFFF
        for pin in COL_PINS:
            self.pca.channels[pin].duty_cycle = 0
    
    def enable_outputs(self, enable=True):
        try:
            GPIO.output(OE_PIN, GPIO.LOW if enable else GPIO.HIGH)
        except Exception as e:
            print(e)
    
    def get_row_col(self, slot_number):
        if not 1 <= slot_number <= (NUM_ROWS * NUM_COLS):
            raise ValueError(f"Slot inválido: {slot_number}")
        zero_based_index = slot_number - 1
        row_index = zero_based_index // NUM_COLS
        column_index = zero_based_index % NUM_COLS
        return row_index, column_index
    
    def activate_slot(self, slot_number, duration=1.0):
        try:
            self.reset_all_pins()
            row_idx, col_idx = self.get_row_col(slot_number)
            row_pin = ROW_PINS[row_idx]
            col_pin = COL_PINS[col_idx]
            
            for pin in ROW_PINS:
                self.pca.channels[pin].duty_cycle = 0xFFFF
            
            self.pca.channels[row_pin].duty_cycle = 0
            self.pca.channels[col_pin].duty_cycle = 0xFFFF
            
            time.sleep(duration)
            self.reset_all_pins()
            
        except Exception as e:
            print(f"Error: {e}")
            self.reset_all_pins()
    
    def cleanup(self):
        self.reset_all_pins()
        GPIO.output(OE_PIN, GPIO.HIGH)
        GPIO.cleanup(OE_PIN)
