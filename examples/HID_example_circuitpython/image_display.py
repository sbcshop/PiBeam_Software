'''
Demo code to test display of Images stored in PiBeam
save images folder into PiBeam provided -> https://github.com/sbcshop/PiBeam_Software/tree/main/examples/HID_example_circuitpython/images
'''
#import required modules
import os
import board
import terminalio
import displayio
import digitalio
from adafruit_display_text import label
from adafruit_st7789 import ST7789
import busio
import time


# Release any resources currently in use for the displays
displayio.release_displays()

img_filenames = ( "/images/img1.bmp","/images/img2.bmp","/images/img3.bmp","/images/img4.bmp","/images/img5.bmp","/images/img6.bmp")

board_type = os.uname().machine
if 'Pico' in board_type:
    # Raspberry Pi Pico pinout, one possibility, at "southwest" of board
    tft_clk = board.GP10 # must be a SPI CLK
    tft_mosi= board.GP11 # must be a SPI TX
    tft_rst = board.GP12
    tft_dc  = board.GP8
    tft_cs  = board.GP9
    tft_bl  = board.GP13
    spi = busio.SPI(clock=tft_clk, MOSI=tft_mosi)
else:
    print("ERROR: Unknown board!")

#define and configure display SPI interface
display_bus = displayio.FourWire(spi, command=tft_dc, chip_select=tft_cs, reset=tft_rst)
display = ST7789(display_bus, rotation=270, width=240, height=135, rowstart=40, colstart=53)

# Make the display context
splash = displayio.Group()
display.show(splash)

tft_bl  = board.GP13
led = digitalio.DigitalInOut(tft_bl)
led.direction = digitalio.Direction.OUTPUT
led.value=True

bmpfiles = sorted("/images/" + fn for fn in os.listdir("/images") if fn.lower().endswith("bmp")) 

while True:
    if len(bmpfiles) == 0:
        print("N0, BMP Files")
        break

    for filename in bmpfiles:
        print("showing bmp image", filename)

        bitmap_file = open(filename, "rb")
        bitmap = displayio.OnDiskBitmap(bitmap_file)
        tile_grid = displayio.TileGrid(bitmap,pixel_shader=getattr(bitmap, 'pixel_shader', displayio.ColorConverter()))

        group = displayio.Group()
        group.append(tile_grid) 
        display.show(group)

        time.sleep(6)# Show the image for 2 seconds