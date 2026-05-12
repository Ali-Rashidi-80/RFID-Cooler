# boot.py
try:
    import usocket as socket
except:
    import socket

import network
import machine
import time

# SSID and Password (REPLACE WITH YOUR CREDENTIALS)
SSID = "ICT"
PASSWORD = "@Mohsen1370"

def do_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('connecting to network...')
        wlan.connect(SSID, PASSWORD)
        # Wait for connection with timeout
        max_wait = 20
        while max_wait > 0:
            if wlan.status() < 0 or wlan.status() >= 3:
                break
            max_wait -= 1
            print('waiting for connection...')
            time.sleep(1)

    if wlan.isconnected():
        print('network config:', wlan.ifconfig())
    else:
        print('wifi connection failed')

do_connect()
