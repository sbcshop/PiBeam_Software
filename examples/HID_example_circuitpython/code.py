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

def camera():
    keyboard = Keyboard(usb_hid.devices)
    keyboard_layout = KeyboardLayout(keyboard)
    time.sleep(1)
    keyboard.send(Keycode.WINDOWS, Keycode.R)
    time.sleep(0.3)
    keyboard_layout.write('cmd.exe')
    keyboard.send(Keycode.ENTER)
    keyboard.send(Keycode.F11)
    time.sleep(1)
    keyboard_layout.write("start microsoft.windows.camera:")
    keyboard.send(Keycode.ENTER)
    tft.clear(tft_bg_color)
    tft.printf("Camera",txt_font,txt_color, 60, 40)
    tft.printf("ON",txt_font,txt_color, 90 ,80)
    keyboard.release_all()

while True:
    val = ir.Read()   # read for IR data incoming from IR remote
    if val is not None:
        led.on()
        print(val)
        #when power button of remote pressed, switch ON camera
        #change operation as per requirement
        if val[0] == 13 and val[1] == 245 and val[2] == 191 and val[3] == 64: #(13, 245, 191, 64) - code received for power button of remote
            print("camera on")
            camera()

    else:
        led.off()


