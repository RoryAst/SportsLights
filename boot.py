import network
import utime
import machine

import wifi
import config
from led_effects import LEDEffects
from team_colors import get_colors
import updater

leds = LEDEffects()
primary, _ = get_colors(config.TEAM_ABBREV)

# 1. Spinning blue while connecting to WiFi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(wifi.WIFI_SSID, wifi.WIFI_PASSWORD)
print(f"[Boot] Connecting to '{wifi.WIFI_SSID}'...", end="")
start = utime.ticks_ms()
while not wlan.isconnected():
    if utime.ticks_diff(utime.ticks_ms(), start) > 20_000:
        print(" FAILED")
        leds.error_flash()
        machine.reset()
    leds.wifi_connecting_pulse()
print(f" OK  IP={wlan.ifconfig()[0]}")

# 2. Three green flashes on connect
leds.wifi_connected_flash()

# 3. Spinning purple while checking for OTA update
leds.ota_checking_pulse()
updater.check_and_update()

# 4. Team colour wipe
leds.team_wipe(primary)

# boot.py exits → main.py starts
