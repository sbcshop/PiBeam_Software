'''
Demo code to test IR trasmission application of PiBeam
Below provided various protocol options we have, for demo will use one of them
_________________________________________________________________________
  NEC PROTOCOL     |       SONY PROTOCOL      |    PHILIPS RC PROTOCOL   |
___________________|__________________________|__________________________|
tx = NEC()         |  tx = SONY_12 ()         |  tx = RC5_IR ()          |    
                   |  tx = SONY_15 ()         |  tx = RC6_M0 ()          |                             
                   |  tx = SONY_20 ()         |                          |                               
___________________|__________________________|__________________________|
'''

from PiBeam import IR_Transmitter,LED
import time,utime

led = LED()
led.off()

#create instance for IR Transmitter 
tx = IR_Transmitter
tx = tx.NEC() #selecting NEC transmission protocol 

data    = 02
address = 0004

while True:
    tx.transmit(address,data)  # address == 0004, data == 02, change value as per requirement
    print('Addr {:04x}'.format(address),'Data {:02x}'.format(data))
    led.on()
    time.sleep(0.08) # delay 80ms
    led.off()
    time.sleep(0.08)
    

