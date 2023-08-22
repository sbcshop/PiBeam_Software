'''
Demo code to test receive funciton along with display of PiBeam
____________________________________________________________________________________________________________
  NEC PROTOCOL         |       SONY PROTOCOL      |    PHILIPS RC PROTOCOL   | Microsoft Vista MCE PROTOCOL  |
_______________________|__________________________|__________________________|_______________________________|
rx = NEC_8 (callback)  |  rx = SONY_12 (callback) |  rx = RC5_IR (callback)  |   rx = MCE (callback)         |
rx = NEC_16(callback)  |  rx = SONY_15 (callback) |  rx = RC6_M0 (callback)  |                               | 
rx = SAMSUNG(callback) |  rx = SONY_20 (callback) |                          |                               |
_______________________|__________________________|__________________________|_______________________________|
'''
from PiBeam import IR_Receiver,LCD,LED,SDCard
import vga1_16x16 as font2
import vga1_16x32 as font
import vga1_8x16  as font1
import vga2_8x8   as font3
import time,utime
import st7789
import os

#create display object to use available methods
tft = LCD().display()

led = LED()

rx = IR_Receiver

sd=SDCard()
vfs = os.VfsFat(sd)

def sd_card(data,address):
    os.mount(vfs, "/fc")
    #print("Filesystem check")
    #print(os.listdir("/fc")) # check the files in sd card
    fn = "/fc/File.txt"

    #print("Single block read/write")

    dat = data + " , "+ address

    with open(fn, "a") as f:  # append data to file
        n = f.write(dat+ '\n')
        print(n, "bytes written")

    with open(fn, "r") as f:  # read data from file
        result = f.read()
        #print(result)
        #print(len(result), "bytes read")
    os.umount("/fc")

def info():
    tft.init() #initialize display
    utime.sleep(0.2)
    tft.text(font,"SB COMPONENTS", 10,20,st7789.YELLOW) #display text with provided font, co-ordinates and color on TFT
    tft.fill_rect(10, 60, 210,10, st7789.RED) # param (x, y, rectangle_length, rectangle_breadth, color)
    tft.text(font,"PiBeam", 10,75,st7789.YELLOW)
    time.sleep(1)
    tft.fill(0)
    tft.text(font,"RECEIVE DATA", 10,10,st7789.WHITE)
    tft.fill_rect(10, 40, 210,10, st7789.RED)
    
info() 

def callback(data, addr, ctrl):
    led.on()
    tft.text(font,'Data {:02x}'.format(data), 10,55,st7789.YELLOW)
    tft.text(font,'Addr {:04x}'.format(addr), 10,90,st7789.YELLOW)
    print('Addr {:04x}'.format(addr),'Data {:02x}'.format(data))
    
    dat = 'Data = {:02x}'.format(data)
    add = 'Addr  = {:04x}'.format(addr)
    
    sd_card(dat,add)# save data to sd card
    
    utime.sleep(0.1)
    
    tft.text(font,'Data {:02x}'.format(data), 10,55,st7789.BLACK)
    tft.text(font,'Addr {:04x}'.format(addr), 10,90,st7789.BLACK)
    time.sleep(0.1)
    led.off()
    
rx = rx.NEC_16(callback)

while True:
    time.sleep(0.2)
