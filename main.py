# main.py  –  NHL Goal Light  |  MicroPython on Raspberry Pi Pico W
# Boot sequence (WiFi, OTA, team wipe) is handled by boot.py.
# This file owns the polling loop only.

import network
import utime

import wifi
import config
from led_effects  import LEDEffects
from nhl_poller   import NHLPoller
from team_colors  import get_colors


def ensure_wifi(wlan, leds):
    """Re-connect if WiFi dropped."""
    if not wlan.isconnected():
        print("[WiFi] Reconnecting…")
        wlan.connect(wifi.WIFI_SSID, wifi.WIFI_PASSWORD)
        for _ in range(40):
            if wlan.isconnected():
                print("[WiFi] Reconnected")
                return True
            leds.wifi_connecting_pulse()
        print("[WiFi] Reconnect failed")
        return False
    return True


def main():
    leds = LEDEffects()
    primary, secondary = get_colors(config.TEAM_ABBREV)

    wlan = network.WLAN(network.STA_IF)  # already active and connected from boot.py

    poller    = NHLPoller(config.TEAM_ABBREV)
    last_poll = utime.ticks_ms() - config.POLL_INTERVAL_LIVE * 1000  # poll immediately

    print("Entering main loop…")

    while True:
        now = utime.ticks_ms()

        interval = (config.POLL_INTERVAL_LIVE
                    if poller.current.state in {"LIVE", "CRIT"}
                    else config.POLL_INTERVAL_IDLE)

        if utime.ticks_diff(now, last_poll) >= interval * 1000:
            if ensure_wifi(wlan, leds):
                result = poller.fetch()
                last_poll = utime.ticks_ms()
                print(f"[Poll] {result:8s}  {poller.summary()}")

                if result == "GOAL":
                    leds.goal_celebration(primary, secondary,
                                          config.GOAL_FLASH_DURATION)
                elif result == "OPP_GOAL":
                    opp_primary, opp_secondary = get_colors(poller.current.opp_abbrev)
                    leds.goal_celebration(opp_primary, opp_secondary,
                                          config.GOAL_FLASH_DURATION)
                elif result == "ERROR":
                    leds.error_flash()

        leds.standby_dim(primary)
        utime.sleep_ms(50)


main()
