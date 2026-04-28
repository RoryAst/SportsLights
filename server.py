# server.py  –  Lightweight async HTTP server for Pico W web UI
#
# Runs as a concurrent task alongside poll_task and led_task.
# GET  /  → HTML page with team select + update button
# POST /  → handle form submission (team change or OTA check)

import asyncio
import ujson
import config
import updater
from team_colors import TEAM_COLORS, get_colors
from nhl_poller  import NHLPoller

TEAM_NAMES = {
    "ANA": "Anaheim Ducks",
    "ARI": "Arizona Coyotes",
    "BOS": "Boston Bruins",
    "BUF": "Buffalo Sabres",
    "CAR": "Carolina Hurricanes",
    "CBJ": "Columbus Blue Jackets",
    "CGY": "Calgary Flames",
    "CHI": "Chicago Blackhawks",
    "COL": "Colorado Avalanche",
    "DAL": "Dallas Stars",
    "DET": "Detroit Red Wings",
    "EDM": "Edmonton Oilers",
    "FLA": "Florida Panthers",
    "LAK": "Los Angeles Kings",
    "MIN": "Minnesota Wild",
    "MTL": "Montreal Canadiens",
    "NJD": "New Jersey Devils",
    "NSH": "Nashville Predators",
    "NYI": "New York Islanders",
    "NYR": "New York Rangers",
    "OTT": "Ottawa Senators",
    "PHI": "Philadelphia Flyers",
    "PIT": "Pittsburgh Penguins",
    "SEA": "Seattle Kraken",
    "SJS": "San Jose Sharks",
    "STL": "St. Louis Blues",
    "TBL": "Tampa Bay Lightning",
    "TOR": "Toronto Maple Leafs",
    "UTA": "Utah Hockey Club",
    "VAN": "Vancouver Canucks",
    "VGK": "Vegas Golden Knights",
    "WPG": "Winnipeg Jets",
    "WSH": "Washington Capitals",
}


# ---------------------------------------------------------------------------
# Persistence helpers
# ---------------------------------------------------------------------------

def _load_user_config():
    try:
        with open("user_config.json") as f:
            return ujson.loads(f.read())
    except Exception:
        return {}

def _save_user_config(data):
    with open("user_config.json", "w") as f:
        f.write(ujson.dumps(data))

def _local_version():
    try:
        with open("version.json") as f:
            return ujson.loads(f.read()).get("version", 0)
    except Exception:
        return 0


# ---------------------------------------------------------------------------
# HTML builder
# ---------------------------------------------------------------------------

def _build_page(state, ip):
    current = config.TEAM_ABBREV
    options = "".join(
        '<option value="{a}"{sel}>{name}</option>'.format(
            a=a,
            sel=' selected' if a == current else '',
            name=TEAM_NAMES.get(a, a),
        )
        for a in sorted(TEAM_COLORS)
    )
    score = state.game_state
    return (
        "<!DOCTYPE html><html><head><title>Sports Lights</title></head><body>"
        "<h1>Sports Lights</h1>"
        "<p>Status: {gs} | v{ver}</p>"
        "<form method='post'>"
        "<label>Team: <select name='team'>{opts}</select></label> "
        "<button name='action' value='save'>Apply</button>"
        "</form><br>"
        "<form method='post'>"
        "<button name='action' value='update'>Check for Updates</button>"
        "</form>"
        "<p><small>http://sportslights.local/ &nbsp;|&nbsp; http://{ip}/</small></p>"
        "</body></html>"
    ).format(gs=score, ver=_local_version(), opts=options, ip=ip)


# ---------------------------------------------------------------------------
# Request handler
# ---------------------------------------------------------------------------

async def _handle(reader, writer, state, wlan):
    try:
        # --- Request line ---
        line = await reader.readline()
        parts = line.decode().split()
        method = parts[0] if parts else "GET"

        # --- Headers ---
        content_length = 0
        while True:
            header = await reader.readline()
            if header in (b"\r\n", b"\n", b""):
                break
            h = header.decode().lower()
            if h.startswith("content-length:"):
                content_length = int(h.split(":", 1)[1].strip())

        # --- Body ---
        body = ""
        if content_length > 0:
            body = (await reader.read(content_length)).decode()

        ip = wlan.ifconfig()[0]

        # --- Route ---
        if method == "POST":
            params = {}
            for pair in body.split("&"):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    params[k.strip()] = v.replace("+", " ").strip()

            action = params.get("action", "")

            if action == "save":
                new_team = params.get("team", config.TEAM_ABBREV).upper()
                # Apply live — no restart needed
                config.TEAM_ABBREV = new_team
                state.primary, state.secondary = get_colors(new_team)
                state.poller = NHLPoller(new_team)
                state.event = None  # discard any in-flight event for old team
                # Persist for next boot
                uc = _load_user_config()
                uc["TEAM_ABBREV"] = new_team
                _save_user_config(uc)
                name = TEAM_NAMES.get(new_team, new_team)
                html = (
                    "<!DOCTYPE html><html><body>"
                    "<p>Team changed to <b>{}</b>. LEDs will update within a moment.</p>"
                    "<a href='/'>Back</a></body></html>"
                ).format(name)

            elif action == "update":
                updater.check_and_update()  # resets device if update found
                html = (
                    "<!DOCTYPE html><html><body>"
                    "<p>Already on v{} &mdash; up to date.</p>"
                    "<a href='/'>Back</a></body></html>"
                ).format(_local_version())

            else:
                html = _build_page(state, ip)

            _send(writer, html)

        else:  # GET
            _send(writer, _build_page(state, ip))

        await writer.drain()

    except Exception as e:
        print("[HTTP] error:", e)
    finally:
        writer.close()


def _send(writer, html):
    writer.write(
        "HTTP/1.0 200 OK\r\nContent-Type: text/html\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{}".format(len(html), html)
    )


# ---------------------------------------------------------------------------
# Server task
# ---------------------------------------------------------------------------

async def run_server(state, wlan):
    ip = wlan.ifconfig()[0]
    print(f"[HTTP] Serving at http://{ip}/")
    await asyncio.start_server(
        lambda r, w: _handle(r, w, state, wlan),
        "0.0.0.0", 80,
    )
    while True:
        await asyncio.sleep(3600)
