# led_effects.py  –  NeoPixel animation helpers for MicroPython
import neopixel
from machine import Pin
import utime
import config


def _scale(color, brightness):
    """Apply brightness (0.0-1.0) to an RGB tuple."""
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
    # Low-level helpers
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

    # ------------------------------------------------------------------
    # Boot / status animations
    # ------------------------------------------------------------------

    def startup_sweep(self, color=(0, 120, 255)):
        self.clear()
        for i in range(self.n):
            self._set_pixel(i, color)
            self.np.write()
            utime.sleep_ms(10)
        for i in range(self.n):
            self.np[i] = (0, 0, 0)
            self.np.write()
            utime.sleep_ms(10)

    def wifi_connecting_pulse(self):
        """One spinning-chase frame – call repeatedly while connecting."""
        self.clear()
        spacing = self.n // 3
        for j in range(3):
            self._set_pixel((self._chase_pos + j * spacing) % self.n, (0, 0, 200))
        self.np.write()
        utime.sleep_ms(30)
        self._chase_pos = (self._chase_pos + 1) % self.n

    def wifi_connected_flash(self):
        """Quick green flash to confirm WiFi is up."""
        for _ in range(3):
            self.fill((0, 200, 0))
            utime.sleep_ms(120)
            self.clear()
            utime.sleep_ms(80)

    def error_flash(self):
        """Red triple-flash on error."""
        for _ in range(3):
            self.fill((200, 0, 0))
            utime.sleep_ms(150)
            self.clear()
            utime.sleep_ms(100)

    # ------------------------------------------------------------------
    # Idle / standby
    # ------------------------------------------------------------------

    def standby_dim(self, primary):
        c = _scale(primary, config.BRIGHTNESS * config.IDLE_BRIGHTNESS)
        for i in range(self.n):
            self.np[i] = c
        self.np.write()

    # ------------------------------------------------------------------
    # GOAL celebration  (blocking for goal_duration seconds)
    # ------------------------------------------------------------------

    def goal_celebration(self, primary, secondary, duration_s=None):
        """
        Multi-stage goal celebration:
          1. Rapid alternating flash  (primary / secondary)
          2. Spinning chase in primary
          3. Slow fade out
        Blocks for ~duration_s seconds total.
        """
        if duration_s is None:
            duration_s = config.GOAL_FLASH_DURATION

        deadline = utime.ticks_ms() + duration_s * 1000

        # Stage 1: rapid strobe alternating team colors (2 seconds)
        strobe_end = utime.ticks_ms() + 2000
        toggle = True
        while utime.ticks_diff(strobe_end, utime.ticks_ms()) > 0:
            self.fill(primary if toggle else secondary)
            utime.sleep_ms(60)
            toggle = not toggle

        # Stage 2: spinning chase in primary until 1.5 s before end
        chase_end = utime.ticks_ms() + max(0, utime.ticks_diff(deadline, utime.ticks_ms()) - 1500)
        pos = 0
        while utime.ticks_diff(chase_end, utime.ticks_ms()) > 0:
            self.clear()
            for j in range(3):
                idx = (pos + j * (self.n // 3)) % self.n
                self._set_pixel(idx, primary)
            # secondary colour trail
            for j in range(3):
                idx = (pos + j * (self.n // 3) - 1) % self.n
                self._set_pixel(idx, secondary)
            self.np.write()
            pos = (pos + 1) % self.n
            utime.sleep_ms(40)

        # Stage 3: fade out
        for step in range(20, 0, -1):
            faded = _scale(primary, self.brightness * step / 20)
            for i in range(self.n):
                self.np[i] = faded
            self.np.write()
            utime.sleep_ms(60)

        self.clear()
