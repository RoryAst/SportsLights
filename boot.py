import asyncio
import network
import machine

import wifi
import config
from led_effects import LEDEffects
from team_colors import get_colors
import updater


async def boot_sequence():
    leds = LEDEffects()
    primary, _ = get_colors(config.TEAM_ABBREV)

    # 1. Spinning blue while connecting to WiFi
    network.hostname("sportslights")   # advertise as sportslights.local via mDNS
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(wifi.WIFI_SSID, wifi.WIFI_PASSWORD)
    print(f"[Boot] Connecting to '{wifi.WIFI_SSID}'...", end="")
    from utime import ticks_ms, ticks_diff
    start = ticks_ms()
    while not wlan.isconnected():
        if ticks_diff(ticks_ms(), start) > 20_000:
            print(" FAILED")
            await leds.error_flash()
            machine.reset()
        await leds.wifi_connecting_pulse()
    print(f" OK  IP={wlan.ifconfig()[0]}  http://sportslights.local/")

    # 2. Three green flashes on connect
    await leds.wifi_connected_flash()

    # 3. Spinning purple while checking for OTA update
    await leds.ota_checking_pulse()
    updater.check_and_update()  # sync — no other tasks running yet

    # 4. Team colour wipe
    await leds.team_wipe(primary)


asyncio.run(boot_sequence())
