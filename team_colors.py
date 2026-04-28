# team_colors.py  –  Primary and secondary RGB colors for every NHL team
# Colors are scaled to 0-255. The led_effects module applies BRIGHTNESS scaling.

TEAM_COLORS = {
    # Atlantic Division
    "BOS": ((255, 185,  15), ( 17,  17,  17)),  # Bruins       gold / black
    "BUF": ((252, 181,  20), ( 0,   56, 168)),  # Sabres       gold / blue
    "DET": ((206,  17,  38), (255, 255, 255)),  # Red Wings    red  / white
    "FLA": ((185,  30,  56), ( 4,   30,  66)),  # Panthers     red  / navy
    "MTL": ((175,  30,  45), ( 1,   60, 143)),  # Canadiens    red  / blue
    "OTT": ((200,  16,  46), (255, 184,  28)),  # Senators     red  / gold
    "TBL": ((0,    40, 104), (255, 255, 255)),  # Lightning    blue / white
    "TOR": ((0,    32,  91), (255, 255, 255)),  # Maple Leafs  blue / white

    # Metropolitan Division
    "CAR": ((206,  17,  38), (255, 255, 255)),  # Hurricanes   red  / white
    "CBJ": ((0,    38, 152), (206,  17,  38)),  # Blue Jackets blue / red
    "NJD": ((206,  17,  38), ( 0,    0,   0)),  # Devils       red  / black
    "NYI": ((0,    83, 155), (252, 184,  19)),  # Islanders    blue / orange
    "NYR": ((0,    56, 168), (206,  17,  38)),  # Rangers      blue / red
    "PHI": ((247, 127,  29), (  0,   0,   0)),  # Flyers       orange/ black
    "PIT": ((252, 181,  20), (  0,   0,   0)),  # Penguins     gold / black
    "WSH": ((166,  25,  46), (  4,  30,  66)),  # Capitals     red  / navy

    # Central Division
    "ARI": ((140,  38,  51), ( 30,  15,  55)),  # Coyotes      red  / purple (Utah HC)
    "UTA": ((110, 181, 228), (  0,   0,   0)),  # Utah HC      blue / black
    "CHI": ((207,  10,  44), (255, 103,   0)),  # Blackhawks   red  / orange
    "COL": ((111,  38,  61), ( 35,  97, 146)),  # Avalanche    burgundy/blue
    "DAL": ((  6, 118,  78), (  0,   0,   0)),  # Stars        green/ black
    "MIN": ((  2,  73,  48), (163,   0,   0)),  # Wild         green/ red
    "NSH": ((255, 184,  28), (  4,  30,  66)),  # Predators    gold / navy
    "STL": ((0,   47, 135), (252, 181,  20)),  # Blues        blue / gold
    "WPG": ((  4,  30,  66), ( 49, 81, 140)),  # Jets         navy / blue

    # Pacific Division
    "ANA": ((252, 76,   2), (  0,   0,   0)),  # Ducks        orange/ black
    "CGY": ((210,  15,  26), (250, 175,  25)),  # Flames       red  / yellow
    "EDM": ((  4,  30,  66), (252, 76,    2)),  # Oilers       navy / orange
    "LAK": ((162, 170, 173), (  0,   0,   0)),  # Kings        silver/ black
    "SJS": ((  0, 109, 117), (229, 114,   0)),  # Sharks       teal / orange
    "SEA": (( 53, 115, 128), ( 44,  45,  50)),  # Kraken       teal / dark
    "VAN": ((  0,  32,  91), (  0, 136,  72)),  # Canucks      blue / green
    "VGK": ((180, 151,  90), ( 51,  63,  72)),  # Golden Knts  gold / grey
}

def get_colors(team_abbrev):
    """Return (primary_rgb, secondary_rgb) for a team, defaulting to white/grey."""
    return TEAM_COLORS.get(team_abbrev.upper(), ((255, 255, 255), (80, 80, 80)))
