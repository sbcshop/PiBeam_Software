'''Demo code to test programmable buttons of PiBeam'''

# Importing the BUTTON and LED modules from the PiBeam library
from PiBeam import BUTTON, LED
import time

# Creating an instance of the LED class
led = LED()

# Creating instances of the BUTTON class for three different buttons
bt1 = BUTTON(1)
bt2 = BUTTON(2)
bt3 = BUTTON(3)

while True:
    # Checking if any of the buttons are pressed
    if bt1.read() == 0 or bt2.read() == 0 or bt3.read() == 0:
        print("BUTTON PRESS")
        time.sleep(0.1)  # Introducing a 100ms delay
        led.on()
        time.sleep(0.1)
        led.off()


