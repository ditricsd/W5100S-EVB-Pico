# W5100S-EVB-Pico Home Assistant IO Board

Simple MQTT IO board for Home Assistant via MQTT using the W5100S-EVB-Pico RP2040 board

#### Board: https://docs.wiznet.io/Product/iEthernet/W5100S/w5100s-evb-pico

### Install CircuitPython
CircuitPython Install: https://learn.adafruit.com/welcome-to-circuitpython/installing-circuitpython

Board uf2 file: https://circuitpython.org/board/raspberry_pi_pico/

Modified Wiznet5k library (included in lib folder): https://github.com/Wiznet/RP2040-HAT-CircuitPython


### Files and folders
 * lib/: Adafruit CircuitPython libraries required for the project
 * code.py: main
 * config.py : Configuration file
    * device settings
    * mqtt settings
    * IO settings

## How to use it

* Install Circuit Python
* Set MQTT settings in **config.py / broker**
* Set device settings in **config.py / device**
* Set IO settings in **config.py / IOs**
    * Available options in config.py
* Copy all the files and the lib dir to CIRCUITPY drive
* Program will start automatically



