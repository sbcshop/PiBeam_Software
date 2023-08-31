To try above listed codes which gives ability to use PiBeam as HID device, you have to follow below instructions,

### Step 1: Boot Firmware installation
   - Change PiBeam default micropython firmware with CircuitPython based boot fimware. Download Firmware from here or you can also install via Thonny IDE.
   - Push and hold the BOOT button and plug your PiBeam into the USB port of your computer. Release the BOOT button after your PiBeam is connected to USB port.
   - It will mount as a Mass Storage Device called RPI-RP2.
   - Drag and drop the Firmware UF2 - [PiBeam_HID_firmware](https://github.com/sbcshop/PiBeam_Software/blob/main/examples/HID_example_circuitpython/PiBeam_HID_firmware.uf2) file provided here onto the RPI-RP2 volume. Your PiBeam will reboot. You are now running CircuitPython on PiBeam.

### Step 2: Libraries Setup
  - Once fimware step done, proceed to add complete [lib](https://github.com/sbcshop/PiBeam_Software/tree/main/examples/HID_example_circuitpython) folder having various libraries inside PiBeam.
  - Either copy and paste complete lib directly inside PiBeam or transfer file as shown in [step 3](https://github.com/sbcshop/PiBeam_Software/blob/main/README.md#3-how-to-move-your-script-on-pibeam) of getting started section

### Step 3: Testing Codes
  - Open code which you want to try into Thonny IDE, then click on Green Run button on top left corner.
  - To test any code you just have to save it as code.py into PiBeam's pico for standalone execution.

