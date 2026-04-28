# main.py  –  NHL Goal Light  |  MicroPython on Raspberry Pi Pico W
# Flashes NeoPixels in team colors whenever your NHL team scores.
#
# Upload all .py files in this project to the Pico root, then reset.

import network
import utime
from machine import Pin

import config
import wifi
from led_effects  import LEDEffects
from nhl_poller   import NHLPoller
from team_colors  import get_colors

# ---------------------------------------------------------------------------
# WiFi
# ---------------------------------------------------------------------------

def connect_wifi(leds):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(wifi.WIFI_SSID, wifi.WIFI_PASSWORD)

    print(f"Connecting to '{wifi.WIFI_SSID}' ", end="")
    timeout = 20          # seconds
    start   = utime.ticks_ms()

    while not wlan.isconnected():
        if utime.ticks_diff(utime.ticks_ms(), start) > timeout * 1000:
            print(" FAILED")
            leds.error_flash()
            return False
        leds.wifi_connecting_pulse()
        print(".", end="")

    print(f" OK  IP={wlan.ifconfig()[0]}")
    leds.wifi_connected_flash()
    return True


def ensure_wifi(wlan, leds):
    """Re-connect if WiFi dropped."""
    if not wlan.isconnected():
        print("[WiFi] Reconnecting…")
        wlan.connect(wifi.WIFI_SSID, wifi.WIFI_PASSWORD)
        for _ in range(20):
            if wlan.isconnected():
                print("[WiFi] Reconnected")
                return True
            leds.wifi_connecting_pulse()
        print("[WiFi] Reconnect failed")
        return False
    return True

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    leds   = LEDEffects()
    leds.startup_sweep()

    primary, secondary = get_colors(config.TEAM_ABBREV)
    print(f"Team: {config.TEAM_ABBREV}  |  "
          f"Primary RGB {primary}  |  Secondary RGB {secondary}")

    # Connect to WiFi
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not connect_wifi(leds):
        # Can't connect – blink error and halt so watchdog can reset
        while True:
            leds.error_flash()
            utime.sleep(2)

    poller   = NHLPoller(config.TEAM_ABBREV)
    last_poll = utime.ticks_ms() - config.POLL_INTERVAL_LIVE * 1000  # poll immediately



    print("Entering main loop…")

    while True:
        now = utime.ticks_ms()

        # ---- Determine poll interval based on game state ----
        interval = (config.POLL_INTERVAL_LIVE
                    if poller.current.state in {"LIVE", "CRIT"}
                    else config.POLL_INTERVAL_IDLE)

        # ---- Poll when due ----
        if utime.ticks_diff(now, last_poll) >= interval * 1000:
            if ensure_wifi(wlan, leds):
                result = poller.fetch()
                last_poll = utime.ticks_ms()
                print(f"[Poll] {result:6s}  {poller.summary()}")

                if result == "GOAL":
                    leds.goal_celebration(primary, secondary,
                                          config.GOAL_FLASH_DURATION)
                elif result == "OPP_GOAL":
                    opp_primary, opp_secondary = get_colors(poller.current.opp_abbrev)
                    leds.goal_celebration(opp_primary, opp_secondary,
                                          config.GOAL_FLASH_DURATION)
                elif result == "ERROR":
                    leds.error_flash()

        # ---- Idle LED animation between polls ----
        leds.standby_dim(primary)

        utime.sleep_ms(50)


# ---------------------------------------------------------------------------
main()
