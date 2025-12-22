import network
import time
from secrets import WIFI_SSID, WIFI_PASSWORD


def connect(timeout=15):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if wlan.isconnected():
        return wlan

    print("Connecting to Wi-Fi...")
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)

    start = time.time()
    while not wlan.isconnected():
        if time.time() - start > timeout:
            raise RuntimeError("Wi-Fi connection failed")
        time.sleep(0.5)

    print("Wi-Fi connected:", wlan.ifconfig())
    return wlan