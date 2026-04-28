# =============================================================
#  config.py  –  Edit this file before uploading to your Pico
# =============================================================

# --- OTA updates (set OTA_REPO_URL to your GitHub raw content URL) ---
OTA_ENABLED  = True
OTA_REPO_URL = "https://raw.githubusercontent.com/RoryAst/SportsLights/main"

# --- Your NHL team (3-letter abbreviation) ---
# Examples: TOR BOS NYR MTL EDM COL LAK VGK SEA NYI
TEAM_ABBREV = "UTA"

# --- NeoPixel hardware ---
NEOPIXEL_PIN   = 18   # GPIO pin the NeoPixel data line is connected to
NEOPIXEL_COUNT = 150 # Number of LEDs in your strip / ring

# --- Behaviour ---
POLL_INTERVAL_LIVE   = 5    # seconds between polls during a live game
POLL_INTERVAL_IDLE   = 15   # seconds between polls when no live game
GOAL_FLASH_DURATION  = 8    # seconds to run the goal celebration
BRIGHTNESS           = 1    # 0.0 – 1.0  (keep ≤ 0.5 on USB power)
IDLE_BRIGHTNESS      = 0.25 # 0.0 – 1.0  dim glow when no game / game is live