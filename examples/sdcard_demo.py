'''Demo code for read and write on microSD card'''

from PiBeam import LED,SDCard #import required sdcard module
import os

led = LED()
sd = SDCard()
vfs = os.VfsFat(sd)
os.mount(vfs, "/fc")
print("Filesystem check")
print(os.listdir("/fc")) # check the files in sd card

fn = "/fc/File.txt"

print("Single block read/write")

data = "SB COMPONENTS"
#################################################

with open(fn, "a") as f:  # append data to file
    led.on()
    n = f.write(data)
    print(n, "bytes written")
    led.off()
#################################################

#################################################
with open(fn, "r") as f:  # read data from file
    led.on()
    result = f.read()
    print(result)
    print(len(result), "bytes read")
    led.off()
    
os.umount("/fc")
#################################################    


