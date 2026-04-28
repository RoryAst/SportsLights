# nhl_poller.py  –  Queries the NHL live scores API and tracks goal changes
#
# API used: https://api-web.nhle.com/v1/score/now
# Returns today's games with live scores, game state, and team abbreviations.

import urequests
import utime

SCORE_URL = "https://api-web.nhle.com/v1/score/now"

# Game states reported by the NHL API
LIVE_STATES  = {"LIVE", "CRIT"}       # actively in progress
END_STATES   = {"FINAL", "OFF"}       # game over
PRE_STATES   = {"FUT", "PRE"}         # not started yet


class GameState:
    """Snapshot of the team's current game."""
    def __init__(self):
        self.game_id    = None
        self.state      = "NONE"       # FUT / PRE / LIVE / CRIT / FINAL / OFF / NONE
        self.our_score  = 0
        self.opp_score  = 0
        self.opp_abbrev = "???"
        self.period     = 0
        self.is_home    = False


class NHLPoller:
    def __init__(self, team_abbrev):
        self.team = team_abbrev.upper()
        self.current = GameState()
        self._last_score = -1          # sentinel: never seen a score yet
        self._last_opp_score = -1
        self._last_period = -1

    # ------------------------------------------------------------------

    def fetch(self):
        """
        Poll the NHL API.  Returns one of:
          "GOAL"         – our team just scored (score increased)
          "OPP_GOAL"     – opponent scored
          "PERIOD_START" – a new period just began
          "LIVE"         – game is live, no new goal
          "IDLE"         – no live game right now
          "ERROR"        – network / parse failure
        """
        try:
            resp = urequests.get(SCORE_URL, timeout=10)
            if resp.status_code != 200:
                resp.close()
                return "ERROR"
            data = resp.json()
            resp.close()
        except Exception as e:
            print("NHL API error:", e)
            return "ERROR"

        return self._parse(data)

    # ------------------------------------------------------------------

    def _parse(self, data):
        games = data.get("games", [])

        for game in games:
            away = game.get("awayTeam", {})
            home = game.get("homeTeam", {})

            our_side  = None
            opp_side  = None
            is_home   = False

            if away.get("abbrev", "").upper() == self.team:
                our_side, opp_side, is_home = away, home, False
            elif home.get("abbrev", "").upper() == self.team:
                our_side, opp_side, is_home = home, away, True

            if our_side is None:
                continue  # not our team's game

            # Found our game – update state
            state = game.get("gameState", "NONE").upper()
            our_score = our_side.get("score", 0)
            opp_score = opp_side.get("score", 0)
            period    = game.get("period", 0)

            self.current.game_id    = game.get("id")
            self.current.state      = state
            self.current.our_score  = our_score
            self.current.opp_score  = opp_score
            self.current.opp_abbrev = opp_side.get("abbrev", "???").upper()
            self.current.period     = period
            self.current.is_home    = is_home

            if state not in LIVE_STATES:
                if state in END_STATES:
                    self._last_score = -1
                    self._last_opp_score = -1
                    self._last_period = -1
                return "IDLE"

            # Live game – check for new goal
            if self._last_score == -1:
                # First time seeing this game live
                self._last_score = our_score
                self._last_opp_score = opp_score
                self._last_period = period
                print(f"[NHL] Game found: {self.team} vs {self.current.opp_abbrev} | "
                      f"Score {our_score}–{opp_score} | Period {period}")
                return "LIVE"

            if period > self._last_period:
                print(f"[NHL] Period {period} started")
                self._last_period = period
                self._last_score = max(self._last_score, our_score)
                self._last_opp_score = max(self._last_opp_score, opp_score)
                return "PERIOD_START"

            if our_score > self._last_score:
                print(f"[NHL] GOAL! {self.team} scores! {our_score}–{opp_score}")
                self._last_score = our_score
                self._last_opp_score = max(self._last_opp_score, opp_score)
                return "GOAL"

            if opp_score > self._last_opp_score:
                print(f"[NHL] OPP GOAL! {self.current.opp_abbrev} scores! {our_score}–{opp_score}")
                self._last_opp_score = opp_score
                self._last_score = max(self._last_score, our_score)
                return "OPP_GOAL"

            self._last_score = max(self._last_score, our_score)
            self._last_opp_score = max(self._last_opp_score, opp_score)
            return "LIVE"

        # Team not found in today's schedule
        self._last_score = -1
        self._last_opp_score = -1
        self._last_period = -1
        self.current.state = "NONE"
        return "IDLE"

    # ------------------------------------------------------------------

    def summary(self):
        """Human-readable one-liner for serial output."""
        g = self.current
        if g.state == "NONE":
            return f"{self.team}: no game today"
        loc = "vs" if g.is_home else "@"
        return (f"{self.team} {loc} {g.opp_abbrev} | "
                f"{g.our_score}–{g.opp_score} | "
                f"P{g.period} [{g.state}]")
