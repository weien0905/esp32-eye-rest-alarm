try:
  import usocket as socket
except:
  import socket

import network

import esp
esp.osdebug(None)

import gc
gc.collect()

# Replace your ssid and password here
ssid = "REPLACE_WITH_YOUR_SSID"
password = "REPLACE_WITH_YOUR_PASSWORD"

station = network.WLAN(network.STA_IF)
station.active(True)
station.connect(ssid, password)

while not station.isconnected():
  pass

print("Connection successful")
print(station.ifconfig())
