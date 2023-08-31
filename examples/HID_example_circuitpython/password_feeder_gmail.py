'''
Demo code to insert gmail password on Pressing power button of TV remote
'''
from adafruit_hid.keyboard import Keyboard, Keycode
from keyboard_layout_win_uk import KeyboardLayout
from adafruit_display_text import label
from PiBeam  import LCD,IR,LED
import usb_hid
import time

tft_bg_color  = 0xFFFF00  # Yellow
txt_color = 0x0000ff
txt_font = 3

tft = LCD(tft_bg_color)
tft.bl() #tft.bl(False) - tft backlight off

led = LED()

ir = IR()

tft.printf("SB COMPONENTS",txt_font,txt_color, 5, 40)
tft.printf("PiBeam",txt_font,txt_color, 60, 80)

def passwordFeed():
    keyboard = Keyboard(usb_hid.devices)
    keyboard_layout = KeyboardLayout(keyboard)
    
    ''' Modify password text and/or special characters '''
    time.sleep(1)
    keyboard_layout.write("yourPasswordText") # initial text of password
    time.sleep(0.1)
    keyboard.send(Keycode.SHIFT, Keycode.TWO) #special character typing -> @  
    time.sleep(0.1)
    keyboard.send(Keycode.SHIFT, Keycode.THREE) #special character typing -> # 
    time.sleep(0.1)
    keyboard_layout.write("sbcomponents") # terminal text of password
    time.sleep(0.2)
    keyboard.send(Keycode.TAB)
    time.sleep(0.2)
    keyboard.send(Keycode.TAB)
    time.sleep(0.2)
    keyboard.send(Keycode.ENTER)
    time.sleep(0.3)
    keyboard.release_all()


while True:
    val = ir.Read()   # read for IR data incoming from IR remote
    if val is not None:
        led.on()
        print(val)
        #when power button of remote pressed, switch ON camera
        #change operation as per requirement
        if val[0] == 13 and val[1] == 245 and val[2] == 191 and val[3] == 64: #(13, 245, 191, 64) - code received for power button of remote
            print("Password Enter...")
            tft.clear(tft_bg_color)
            tft.printf("Password..",txt_font,txt_color, 5, 40)
            passwordFeed()
            tft.clear(tft_bg_color)
            tft.printf("Login",txt_font,txt_color, 5, 40)()

    else:
        led.off()
    time.sleep(0.2)
    





