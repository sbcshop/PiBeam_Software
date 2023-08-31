# Basic Program to start camera of device and ongoing operations displayed on TFT
# This code tested for Windows based PC/Laptop but can be modified for Other OS
import time
import os
import usb_hid
import digitalio
import board
import busio
import terminalio
import displayio
import pulseio
import adafruit_irremote
from adafruit_display_text import label
from adafruit_hid.keyboard import Keyboard, Keycode
from keyboard_layout_win_uk import KeyboardLayout
from adafruit_st7789 import ST7789

class LCD:
    def __init__(self,BG_COLOR):
        
        displayio.release_displays()
        self.BG_COLOR = BG_COLOR

        self.tft_clk = board.GP10 # must be a SPI CLK
        self.tft_mosi= board.GP11 # must be a SPI TX
        self.tft_rst = board.GP12
        self.tft_dc  = board.GP8
        self.tft_cs  = board.GP9
        self.spi = busio.SPI(clock=self.tft_clk, MOSI=self.tft_mosi)

        self.display_bus = displayio.FourWire(self.spi, command=self.tft_dc, chip_select=self.tft_cs, reset=self.tft_rst)
        self.display = ST7789(self.display_bus, rotation=270, width=240, height=135, rowstart=40, colstart=53)

        # Make the display context
        self.splash = displayio.Group()
        self.display.show(self.splash)

        color_bitmap = displayio.Bitmap(self.display.width, self.display.height, 1)
        color_palette = displayio.Palette(1)
        color_palette[0] = BG_COLOR

        bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
        self.splash.append(bg_sprite)
    
    def bl(self,val = True):
        self.tft_bl  = board.GP13
        self.led = digitalio.DigitalInOut(self.tft_bl)
        self.led.direction = digitalio.Direction.OUTPUT
        
        if val == True:
            self.led.value=True

        elif val == False:
            self.led.value=False
            
    def clear(self,color):
        color_bitmap = displayio.Bitmap(self.display.width, self.display.height, 1)
        color_palette = displayio.Palette(1)
        color_palette[0] = color

        bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
        self.splash.append(bg_sprite)
        
    # This function creates colorful rectangular box 
    def inner_rectangle(self,BORDER,frame_color):
        # Draw a smaller inner rectangle
        inner_bitmap = displayio.Bitmap(self.display.width - BORDER * 2, self.display.height - BORDER * 2, 1)
        inner_palette = displayio.Palette(1)
        inner_palette[0] = frame_color
        inner_sprite = displayio.TileGrid(inner_bitmap, pixel_shader=inner_palette, x=BORDER, y=BORDER)
        self.splash.append(inner_sprite)
        
    #Function to print data on TFT
    def printf(self,text,FONTSCALE,TEXT_COLOR,x_pos, y_pos): 
        text_area = label.Label(terminalio.FONT, text=text, color=TEXT_COLOR)
        text_group = displayio.Group(scale=FONTSCALE,x=x_pos,y=y_pos,)
        text_group.append(text_area)  # Subgroup for text scaling
        self.splash.append(text_group)

class IR:
    def __init__(self):
        self.pin = board.GP1
        self.pulsein = pulseio.PulseIn(self.pin, maxlen=120, idle_state=True)
        self.decoder = adafruit_irremote.NonblockingGenericDecode(self.pulsein)

    def Read(self):
        for message in self.decoder.read():
            if isinstance(message, adafruit_irremote.IRMessage):
                return message.code 
                #print("Decoded:", message.code)
class LED:
    def __init__(self):
        self.tft_bl = board.GP25
        self.led = digitalio.DigitalInOut(self.tft_bl)
        self.led.direction = digitalio.Direction.OUTPUT
        
    def on(self):
        self.led.value=True

    def off(self):
        self.led.value=False
        