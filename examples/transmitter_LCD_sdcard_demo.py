'''
_________________________________________________________________________
  NEC PROTOCOL     |       SONY PROTOCOL      |    PHILIPS RC PROTOCOL   |
___________________|__________________________|__________________________|
rx = NEC()         |  rx = SONY_12 ()         |  rx = RC5_IR ()          |    
                   |  rx = SONY_15 ()         |  rx = RC6_M0 ()          |                             
                   |  rx = SONY_20 ()         |                          |                               
___________________|__________________________|__________________________|
'''
from PiBeam import IR_Transmitter,LCD,LED
import vga1_8x16 as font1
import vga1_16x32 as font
import vga1_16x16 as font2
import vga2_8x8   as font3
import time,utime
import st7789

led = LED()
led.off()

tft = LCD().display()

tx = IR_Transmitter

def info():
    tft.init()
    utime.sleep(0.2)
    tft.text(font,"SB BCOMPONENTS", 10,20)
    tft.fill_rect(10, 60, 210,10, st7789.RED)
    tft.text(font,"PiBeam", 10,75,st7789.YELLOW)
    time.sleep(1)
    tft.fill(0) #clear screen
    tft.text(font,"TRANSMIT DATA", 10,10,st7789.WHITE)
    tft.fill_rect(10, 40, 210,10, st7789.RED)
    
info()    

tx = tx.SONY_12()

data    = 02
address = 0004

while True:
    tx.transmit(address,data)  # address == 0004, data == 02
    tft.text(font,'Data {:02x}'.format(data), 10,55,st7789.YELLOW)
    tft.text(font,'Addr {:04x}'.format(address), 10,90,st7789.YELLOW)
    led.on()
    time.sleep(0.2) # delay 80ms
    led.off()
    time.sleep(0.2)
    

