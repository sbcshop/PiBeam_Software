# PiBeam_Software
<img src="">
Introducing PiBeam, the ultimate USB IR Transceiver that revolutionizes the way you control your devices. PiBeam offers a versatile and cost-effective way to enable wireless communication and control in a variety of embedded electronics applications.

PiBeam is a DIY USB transceiver device that can be programmed to control and manage your computer, gaming console, or multimedia system, PiBeam provides a user-friendly interface with TFT 1.14” Display that ensures a smooth and intuitive experience.

An in-depth setup and working guide for PiBeam is available on this github. 

### Features:
- The device is powered by Raspberry Pi RP2040, which ensures efficient and fast processing.
- The device features a TFT 1.14” display, providing a better user experience.
- IR transceiver device, thereby it can send and receive IR signal data to establish two way communication.
- Onboard Micro-SD card support for Data logging and storage
- Boot button for programming and 3 user programmable buttons to add additional control features for project
- One programmable LED and power status LED
- Compatible with Windows, Mac, and Linux, ensuring broad compatibility across different systems.
- The device is a plug-and-play device and does not require any drivers, making it easy to use.
- Supports all common Remote protocols like NEC protocol, Sony SIRC 12 bit, 15bit, 20bit, Philips RC-5 & RC-6 mode 0, making it versatile for various applications.
- Easy drag-and-drop programming using mass storage over USB.
- Open-source hardware with Python support and compatible to use as a HID device

### Specifications:
- RPi RP2040 microcontroller which is dual-core Arm Cortex-M0+ processor
- 2MB of onboard flash storage, 264kB of RAM
- Board supply voltage is 5V
- Display 1.14” with resolution 240×135 pixels
- 65K RGB Colors Display
- SPI Interface
- ST7789 Display Driver
- Type A USB interface


## Getting Started with PiBeam
### Hardware Overview
#### Pinout
<img src="">


### Interfacing Details
- SD Card interfacing info
  | Pico | Hardware Pin | Function |
  |---|---|---|
  |GP18 | SCLK | Clock pin of SPI interface for microSD card |
  |GP19 | DIN  | MOSI (Master OUT Slave IN) data pin of SPI interface for microSD card|
  |GP16 | DOUT | MISO (Master IN Slave OUT) data pin of SPI interface for microSD card|
  |GP17 | CS   | Chip Select pin of SPI interface for microSD card|

- Display interfacing info
  | Pico | Hardware Pin | Function |
  |---|---|---|
  |GP10 | SCLK | Clock pin of SPI interface for display |
  |GP11 | DIN  | MOSI (Master OUT Slave IN) data pin of SPI interface|
  |GP8 | D/C | Data/command line of SPI interface for display |
  |GP12 | RESET | Display reset pin |
  |GP9 | CS   | Chip Select pin of SPI interface for display| 
  |GP13 | BL | Backlight pin for display |

- Other peripherals
  | Pico | Hardware Pin | Function |
  |---|---|---|
  | |  |  |


### 1. Step to install boot Firmware
   - Every PiBeam board will be provided with boot firmware already installed, so you can skip this step and directly go to step 2.
   - If in case you want to install firmware for your board, Push and hold the BOOTSEL button and plug your Pico W into the USB port of your computer. Release the BOOTSEL button after your Pico is connected.
   <img src="https://github.com/sbcshop/PiBeam_Software/blob/main/images/pico_bootmode.gif">
   
   - It will mount as a Mass Storage Device called RPI-RP2.
   - Drag and drop the MicroPython UF2 - [PiBeam_firmware](https://github.com/sbcshop/PiBeam_Software/blob/main/PiBeam_firmware.uf2) file provided in this github onto the RPI-RP2 volume. Your Pico will reboot. You are now running MicroPython on PiBeam.


### Example Codes
   Save whatever example code file you want to try as **main.py** in **PiBeam** as shown in above [step 3](), also add related lib files with default name.
   In [example]() folder you will find demo example script code to test onboard components of PiBeam like 
   - [Buzzer]() : code to test onboard Buzzer
   - [SD card]() : code to test onboard micro SD card interfacing
   - []() :
   
   
   Using this sample code as a guide, you can modify, build, and share codes!!  
   
## Resources
  * [Schematic]()
  * [Hardware Files]()
  * [Step File]()
  * [MicroPython getting started for RPi Pico/Pico W]()
  * [Pico W Getting Started]()
  * [RP2040 Datasheet]()


## Related Products
   
   
   Shields are compatible with PiBeam, Ardi-32 and Other Arduino Uno Compatible boards.

## Product License

This is ***open source*** product. Kindly check LICENSE.md file for more information.

Please contact support@sb-components.co.uk for technical support.
<p align="center">
  <img width="360" height="100" src="https://cdn.shopify.com/s/files/1/1217/2104/files/Logo_sb_component_3.png?v=1666086771&width=300">
</p>
