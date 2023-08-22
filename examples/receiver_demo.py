'''
Demo code to testing receive funciton of PiBeam
Below provided various protocol options we have, for demo will use one of them
____________________________________________________________________________________________________________
  NEC PROTOCOL         |       SONY PROTOCOL      |    PHILIPS RC PROTOCOL   | Microsoft Vista MCE PROTOCOL  |
_______________________|__________________________|__________________________|_______________________________|
rx = NEC_8 (callback)  |  rx = SONY_12 (callback) |  rx = RC5_IR (callback)  |   rx = MCE (callback)         |
rx = NEC_16(callback)  |  rx = SONY_15 (callback) |  rx = RC6_M0 (callback)  |                               | 
rx = SAMSUNG(callback) |  rx = SONY_20 (callback) |                          |                               |
_______________________|__________________________|__________________________|_______________________________|
'''
from PiBeam import IR_Receiver,LED
import time,utime


rx = IR_Receiver

led = LED()

def callback(data, addr, ctrl):
    led.on()
    print('Addr {:04x}'.format(addr),'Data {:02x}'.format(data))
    utime.sleep(0.2)#wait 200ms
    led.off()
    
rx = rx.NEC_16(callback)

while True:
    time.sleep_ms(200)
