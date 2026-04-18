# ESP32 Captive Portal

Connects to ESP32 WiFi hotspot and plays a sound via browser.

## Requirements

- ESP32 with MicroPython flashed
- Python 3.x
- mpremote

## Setup

Install mpremote:
pip install mpremote

Upload files to ESP32:
mpremote connect /dev/ttyUSB0 cp main.py :/main.py
mpremote connect /dev/ttyUSB0 cp sound.mp3 :/sound.mp3

Restart the device:
mpremote connect /dev/ttyUSB0 reset

## Usage

1. Connect to WiFi network **FreeWiFi** (no password)
2. Open browser and go to `http://192.168.4.1`
3. Press **Connect** button to play sound
