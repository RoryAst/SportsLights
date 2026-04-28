# updater.py  –  OTA update check, runs from boot.py before main.py
#
# Fetches version.json from GitHub. If remote version > local, downloads
# each listed file and resets. On any error, returns silently so boot continues.

import network
import utime
import urequests
import ujson
import machine

import wifi
import config


def _connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if wlan.isconnected():
        return wlan
    wlan.connect(wifi.WIFI_SSID, wifi.WIFI_PASSWORD)
    deadline = utime.ticks_add(utime.ticks_ms(), 20_000)
    while not wlan.isconnected():
        if utime.ticks_diff(deadline, utime.ticks_ms()) <= 0:
            return None
        utime.sleep_ms(200)
    return wlan


def _local_version():
    try:
        with open("version.json") as f:
            return ujson.loads(f.read()).get("version", 0)
    except Exception:
        return 0


def check_and_update():
    if not getattr(config, "OTA_ENABLED", False):
        return

    repo = getattr(config, "OTA_REPO_URL", "").rstrip("/")
    if not repo or "YOUR_USERNAME" in repo:
        print("[OTA] OTA_REPO_URL not configured — skipping")
        return

    print("[OTA] Connecting WiFi for update check…")
    wlan = _connect_wifi()
    if not wlan:
        print("[OTA] WiFi failed — skipping update check")
        return

    try:
        resp = urequests.get(repo + "/version.json", timeout=10)
        if resp.status_code != 200:
            resp.close()
            print(f"[OTA] version.json fetch failed ({resp.status_code})")
            return
        remote = ujson.loads(resp.text)
        resp.close()
    except Exception as e:
        print("[OTA] version.json fetch error:", e)
        return

    remote_ver = remote.get("version", 0)
    local_ver  = _local_version()
    print(f"[OTA] local={local_ver}  remote={remote_ver}")

    if remote_ver <= local_ver:
        print("[OTA] Up to date")
        return

    files = remote.get("files", [])
    print(f"[OTA] Updating to v{remote_ver} — downloading {len(files)} file(s)…")

    for fname in files:
        try:
            resp = urequests.get(repo + "/" + fname, timeout=15)
            if resp.status_code != 200:
                resp.close()
                print(f"[OTA] Failed to fetch {fname} ({resp.status_code}) — aborting")
                return
            content = resp.content
            resp.close()
            with open(fname, "wb") as f:
                f.write(content)
            print(f"[OTA]   {fname} OK")
        except Exception as e:
            print(f"[OTA] Error downloading {fname}: {e} — aborting")
            return

    # Write version.json last — if we get here all files succeeded
    try:
        with open("version.json", "w") as f:
            f.write(ujson.dumps(remote))
        print(f"[OTA] Update to v{remote_ver} complete — rebooting")
        utime.sleep_ms(500)
        machine.reset()
    except Exception as e:
        print("[OTA] Failed to write version.json:", e)
