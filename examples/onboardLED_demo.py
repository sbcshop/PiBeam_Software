'''Demo code to test onboard programmable Status LED of PiBeam'''

from PiBeam import LED #libray module import for LED 
import time

led = LED()	#create object for LED 

while True:
    led.on()	#turn ON Status LED
    time.sleep(0.5) #wait for half second
    led.off() 	#turn OFF Status LED
    time.sleep(0.5)    



