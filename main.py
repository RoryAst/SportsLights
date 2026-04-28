# main.py  –  NHL Goal Light  |  MicroPython on Raspberry Pi Pico W
# Boot sequence (WiFi, OTA, team wipe) is handled by boot.py.
# This file owns two concurrent async tasks: poll_task and led_task.

import asyncio
import network

import wifi
import config
from led_effects import LEDEffects
from nhl_poller  import NHLPoller
from team_colors import get_colors


class AppState:
    """Shared state written by poll_task, consumed by led_task."""
    event      = None   # "GOAL" | "OPP_GOAL" | "PERIOD_START" | "ERROR" | None
    game_state = "IDLE" # drives poll interval
    opp_abbrev = "???"  # opponent team for OPP_GOAL color lookup


async def ensure_wifi(wlan, leds):
    if wlan.isconnected():
        return True
    print("[WiFi] Reconnecting…")
    wlan.connect(wifi.WIFI_SSID, wifi.WIFI_PASSWORD)
    for _ in range(40):
        if wlan.isconnected():
            print("[WiFi] Reconnected")
            return True
        await leds.wifi_connecting_pulse()
    print("[WiFi] Reconnect failed")
    return False


async def poll_task(state, poller, wlan, leds):
    interval = 0  # poll immediately on first iteration
    while True:
        await asyncio.sleep(interval)

        if not await ensure_wifi(wlan, leds):
            interval = config.POLL_INTERVAL_IDLE
            continue

        result = poller.fetch()  # synchronous HTTP call — blocks briefly

        # Only set event if led_task has finished handling the previous one
        if state.event is None:
            state.event = result
            state.opp_abbrev = poller.current.opp_abbrev

        state.game_state = poller.current.state
        print(f"[Poll] {result:12s}  {poller.summary()}")

        interval = (config.POLL_INTERVAL_LIVE
                    if state.game_state in {"LIVE", "CRIT"}
                    else config.POLL_INTERVAL_IDLE)


async def led_task(state, leds, primary, secondary):
    while True:
        ev = state.event

        if ev == "GOAL":
            state.event = None
            await leds.goal_celebration(primary, secondary, config.GOAL_FLASH_DURATION)
        elif ev == "OPP_GOAL":
            state.event = None
            opp_primary, opp_secondary = get_colors(state.opp_abbrev)
            await leds.goal_celebration(opp_primary, opp_secondary, config.GOAL_FLASH_DURATION)
        elif ev == "PERIOD_START":
            state.event = None
            await leds.period_start_flash(secondary)
        elif ev == "ERROR":
            state.event = None
            await leds.error_flash()
        else:
            leds.standby_dim(primary)
            await asyncio.sleep_ms(50)


async def main():
    leds   = LEDEffects()
    primary, secondary = get_colors(config.TEAM_ABBREV)
    print(f"Team: {config.TEAM_ABBREV}  |  Primary {primary}  |  Secondary {secondary}")

    wlan   = network.WLAN(network.STA_IF)  # already active and connected from boot.py
    poller = NHLPoller(config.TEAM_ABBREV)
    state  = AppState()

    print("Entering main loop…")
    asyncio.create_task(poll_task(state, poller, wlan, leds))
    await led_task(state, leds, primary, secondary)


asyncio.run(main())
