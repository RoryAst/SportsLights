# led_effects.py  –  NeoPixel animation helpers for MicroPython
import asyncio
import neopixel
from machine import Pin
import config


def _scale(color, brightness):
    return tuple(int(c * brightness) for c in color)


class LEDEffects:
    def __init__(self):
        pin = Pin(config.NEOPIXEL_PIN, Pin.OUT)
        self.np = neopixel.NeoPixel(pin, config.NEOPIXEL_COUNT)
        self.n = config.NEOPIXEL_COUNT
        self.brightness = config.BRIGHTNESS
        self._chase_pos = 0
        self.clear()

    # ------------------------------------------------------------------
    # Low-level helpers (sync — no sleeping)
    # ------------------------------------------------------------------

    def clear(self):
        for i in range(self.n):
            self.np[i] = (0, 0, 0)
        self.np.write()

    def fill(self, color):
        c = _scale(color, self.brightness)
        for i in range(self.n):
            self.np[i] = c
        self.np.write()

    def _set_pixel(self, i, color):
        self.np[i] = _scale(color, self.brightness)

    def standby_dim(self, primary):
        c = _scale(primary, config.BRIGHTNESS * config.IDLE_BRIGHTNESS)
        for i in range(self.n):
            self.np[i] = c
        self.np.write()

    # ------------------------------------------------------------------
    # Boot / status animations (async)
    # ------------------------------------------------------------------

    async def startup_sweep(self, color=(0, 120, 255)):
        self.clear()
        for i in range(self.n):
            self._set_pixel(i, color)
            self.np.write()
            await asyncio.sleep_ms(10)
        for i in range(self.n):
            self.np[i] = (0, 0, 0)
            self.np.write()
            await asyncio.sleep_ms(10)

    async def wifi_connecting_pulse(self):
        """One spinning-chase frame – await repeatedly while connecting."""
        self.clear()
        spacing = self.n // 3
        for j in range(3):
            self._set_pixel((self._chase_pos + j * spacing) % self.n, (0, 0, 200))
        self.np.write()
        await asyncio.sleep_ms(30)
        self._chase_pos = (self._chase_pos + 1) % self.n

    async def wifi_connected_flash(self):
        for _ in range(3):
            self.fill((0, 200, 0))
            await asyncio.sleep_ms(120)
            self.clear()
            await asyncio.sleep_ms(80)

    async def ota_checking_pulse(self, duration_ms=2000):
        """Blocking purple spinning chase shown while OTA check runs."""
        end = duration_ms  # count down in ms steps
        pos = 0
        spacing = self.n // 3
        while end > 0:
            self.clear()
            for j in range(3):
                self._set_pixel((pos + j * spacing) % self.n, (128, 0, 255))
            self.np.write()
            await asyncio.sleep_ms(30)
            pos = (pos + 1) % self.n
            end -= 30
        self.clear()

    async def team_wipe(self, color):
        """Sweep team color from pixel 0 to end, then hold briefly."""
        self.clear()
        for i in range(self.n):
            self._set_pixel(i, color)
            self.np.write()
            await asyncio.sleep_ms(8)
        await asyncio.sleep_ms(400)

    async def period_start_flash(self, color):
        """Three flashes in the given color — shown at period start."""
        for _ in range(3):
            self.fill(color)
            await asyncio.sleep_ms(150)
            self.clear()
            await asyncio.sleep_ms(100)

    async def error_flash(self):
        for _ in range(3):
            self.fill((200, 0, 0))
            await asyncio.sleep_ms(150)
            self.clear()
            await asyncio.sleep_ms(100)

    # ------------------------------------------------------------------
    # GOAL celebration  (async, yields every frame)
    # ------------------------------------------------------------------

    async def goal_celebration(self, primary, secondary, duration_s=None):
        """
        Three-stage goal celebration. Fully async — yields every 40-60 ms
        so poll_task can run mid-celebration without dropping HTTP calls.
        """
        if duration_s is None:
            duration_s = config.GOAL_FLASH_DURATION

        remaining_ms = duration_s * 1000

        # Stage 1: rapid strobe alternating team colors (2 seconds)
        strobe_ms = min(2000, remaining_ms)
        remaining_ms -= strobe_ms
        toggle = True
        while strobe_ms > 0:
            self.fill(primary if toggle else secondary)
            await asyncio.sleep_ms(60)
            toggle = not toggle
            strobe_ms -= 60

        # Stage 2: spinning chase in primary until 1.5 s before end
        chase_ms = max(0, remaining_ms - 1500)
        remaining_ms -= chase_ms
        pos = 0
        while chase_ms > 0:
            self.clear()
            for j in range(3):
                idx = (pos + j * (self.n // 3)) % self.n
                self._set_pixel(idx, primary)
            for j in range(3):
                idx = (pos + j * (self.n // 3) - 1) % self.n
                self._set_pixel(idx, secondary)
            self.np.write()
            pos = (pos + 1) % self.n
            await asyncio.sleep_ms(40)
            chase_ms -= 40

        # Stage 3: fade out (remaining_ms ≈ 1500)
        steps = 20
        step_ms = max(1, remaining_ms // steps)
        for step in range(steps, 0, -1):
            faded = _scale(primary, self.brightness * step / steps)
            for i in range(self.n):
                self.np[i] = faded
            self.np.write()
            await asyncio.sleep_ms(step_ms)

        self.clear()
