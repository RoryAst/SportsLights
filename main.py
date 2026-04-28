# main.py  –  NHL Goal Light  |  MicroPython on Raspberry Pi Pico W
# Boot sequence (WiFi, OTA, team wipe) is handled by boot.py.
# Three concurrent async tasks: poll_task, led_task, run_server.

import asyncio
import network
import ujson

import wifi
import config
from led_effects import LEDEffects
from nhl_poller  import NHLPoller
from team_colors import get_colors
from server      import run_server

_ACTIONABLE = {"GOAL", "OPP_GOAL", "PERIOD_START", "ERROR"}


# ---------------------------------------------------------------------------
# Persistent user config (overrides config.py on boot)
# ---------------------------------------------------------------------------

def _apply_user_config():
    try:
        with open("user_config.json") as f:
            for k, v in ujson.loads(f.read()).items():
                setattr(config, k, v)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Shared state (written by poll_task / server, read by led_task)
# ---------------------------------------------------------------------------

class AppState:
    event      = None    # "GOAL" | "OPP_GOAL" | "PERIOD_START" | "ERROR" | None
    game_state = "IDLE"
    opp_abbrev = "???"
    primary    = (255, 255, 255)
    secondary  = (80,  80,  80)
    poller     = None    # NHLPoller — replaced live on team change


# ---------------------------------------------------------------------------
# WiFi helper
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Poll task
# ---------------------------------------------------------------------------

async def poll_task(state, wlan, leds):
    interval = 0  # poll immediately on first iteration
    while True:
        await asyncio.sleep(interval)

        if not await ensure_wifi(wlan, leds):
            interval = config.POLL_INTERVAL_IDLE
            continue

        result = state.poller.fetch()  # synchronous HTTP — blocks briefly

        state.game_state = state.poller.current.state
        state.opp_abbrev = state.poller.current.opp_abbrev
        print(f"[Poll] {result:12s}  {state.poller.summary()}")

        # Only queue actionable events; LIVE/IDLE are status, not events.
        # Don't clobber a pending actionable event that led_task hasn't handled yet.
        if result in _ACTIONABLE and state.event not in _ACTIONABLE:
            state.event = result

        interval = (config.POLL_INTERVAL_LIVE
                    if state.game_state in {"LIVE", "CRIT"}
                    else config.POLL_INTERVAL_IDLE)


# ---------------------------------------------------------------------------
# LED task
# ---------------------------------------------------------------------------

async def led_task(state, leds):
    while True:
        ev = state.event

        if ev == "GOAL":
            state.event = None
            await leds.goal_celebration(state.primary, state.secondary,
                                        config.GOAL_FLASH_DURATION)
        elif ev == "OPP_GOAL":
            state.event = None
            opp_primary, opp_secondary = get_colors(state.opp_abbrev)
            await leds.goal_celebration(opp_primary, opp_secondary,
                                        config.GOAL_FLASH_DURATION)
        elif ev == "PERIOD_START":
            state.event = None
            await leds.period_start_flash(state.secondary)
        elif ev == "ERROR":
            state.event = None
            await leds.error_flash()
        else:
            leds.standby_dim(state.primary)
            await asyncio.sleep_ms(50)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    _apply_user_config()

    leds  = LEDEffects()
    state = AppState()
    state.primary, state.secondary = get_colors(config.TEAM_ABBREV)
    state.poller = NHLPoller(config.TEAM_ABBREV)

    print(f"Team: {config.TEAM_ABBREV}  |  Primary {state.primary}  |  Secondary {state.secondary}")

    wlan = network.WLAN(network.STA_IF)  # already active and connected from boot.py

    print("Entering main loop…")
    asyncio.create_task(poll_task(state, wlan, leds))
    asyncio.create_task(run_server(state, wlan))
    await led_task(state, leds)


asyncio.run(main())
