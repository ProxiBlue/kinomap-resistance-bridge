"""Speed sensor using Hall effect sensor or reed switch on the flywheel.

Counts pulses from a magnetic sensor attached to the bike's flywheel.
Each pulse = one flywheel revolution. RPM and speed are derived from
the pulse frequency and a configurable flywheel circumference.

Runs interrupt-driven via GPIO edge detection — no polling, no CPU waste.
"""

import logging
import threading
import time
from typing import Any

logger = logging.getLogger(__name__)

try:
    import RPi.GPIO as GPIO
    _HAS_GPIO = True
except ImportError:
    _HAS_GPIO = False


class SpeedSensor:
    """Reads flywheel RPM from a Hall effect sensor or reed switch on a GPIO pin."""

    def __init__(self, config: dict[str, Any]):
        sensor_cfg = config["speed_sensor"]
        self._pin: int = sensor_cfg["pin"]
        self._flywheel_circumference_m: float = sensor_cfg["flywheel_circumference_m"]
        self._gear_ratio: float = sensor_cfg.get("gear_ratio", 1.0)
        self._pulses_per_rev: int = sensor_cfg.get("pulses_per_revolution", 1)
        self._debounce_ms: int = sensor_cfg.get("debounce_ms", 5)
        self._timeout_s: float = sensor_cfg.get("timeout_s", 3.0)
        self._mock: bool = config["gpio"].get("mock", False) or not _HAS_GPIO
        self._pull_up: bool = sensor_cfg.get("pull_up", True)

        # Pulse tracking
        self._lock = threading.Lock()
        self._last_pulse_time: float = 0.0
        self._pulse_interval: float = 0.0  # seconds between last two pulses
        self._pulse_count: int = 0
        self._total_revolutions: int = 0

        if self._mock:
            logger.info("Speed sensor running in MOCK mode (no GPIO)")
        else:
            self._setup_gpio()

    def _setup_gpio(self) -> None:
        """Configure the sensor GPIO pin with interrupt-driven edge detection."""
        GPIO.setmode(GPIO.BCM)

        pull = GPIO.PUD_UP if self._pull_up else GPIO.PUD_DOWN
        GPIO.setup(self._pin, GPIO.IN, pull_up_down=pull)

        # Detect falling edge (Hall sensor pulls low when magnet passes)
        GPIO.add_event_detect(
            self._pin,
            GPIO.FALLING,
            callback=self._on_pulse,
            bouncetime=self._debounce_ms,
        )

        logger.info(
            "Speed sensor initialized: GPIO%d, circumference=%.3fm, gear_ratio=%.2f, debounce=%dms",
            self._pin, self._flywheel_circumference_m, self._gear_ratio, self._debounce_ms,
        )

    def _on_pulse(self, channel: int) -> None:
        """GPIO interrupt callback — called on each flywheel revolution."""
        now = time.monotonic()
        with self._lock:
            if self._last_pulse_time > 0:
                self._pulse_interval = now - self._last_pulse_time
            self._last_pulse_time = now
            self._pulse_count += 1
            self._total_revolutions += 1

    @property
    def rpm(self) -> float:
        """Current flywheel RPM, or 0 if no recent pulses.

        Accounts for multiple magnets: if pulses_per_revolution > 1,
        each revolution produces multiple pulses, so we divide the
        raw pulse frequency accordingly.
        """
        with self._lock:
            if self._last_pulse_time == 0 or self._pulse_interval <= 0:
                return 0.0
            # Check for timeout (wheel stopped)
            if (time.monotonic() - self._last_pulse_time) > self._timeout_s:
                return 0.0
            pulse_rpm = 60.0 / self._pulse_interval
            return pulse_rpm / self._pulses_per_rev

    @property
    def speed_kmh(self) -> float:
        """Current speed in km/h, derived from flywheel RPM and circumference.

        If gear_ratio > 1, the pedal drives the flywheel faster than 1:1.
        speed = (flywheel_RPM / gear_ratio) * circumference * 60 / 1000
        """
        flywheel_rpm = self.rpm
        if flywheel_rpm <= 0:
            return 0.0
        # Convert flywheel RPM to effective wheel RPM via gear ratio
        effective_rpm = flywheel_rpm / self._gear_ratio
        # RPM * circumference_m * 60min/hr / 1000m/km = km/h
        return effective_rpm * self._flywheel_circumference_m * 60.0 / 1000.0

    @property
    def cadence_rpm(self) -> float:
        """Estimated pedal cadence in RPM.

        On most exercise bikes: cadence = flywheel_RPM / gear_ratio.
        """
        flywheel_rpm = self.rpm
        if flywheel_rpm <= 0:
            return 0.0
        return flywheel_rpm / self._gear_ratio

    @property
    def total_distance_m(self) -> float:
        """Total distance in meters since startup, based on pulse count.

        Divides by pulses_per_revolution to get actual flywheel revolutions,
        then by gear_ratio and multiplied by circumference.
        """
        with self._lock:
            pulses = self._total_revolutions  # raw pulse count
        actual_revs = pulses / self._pulses_per_rev
        return (actual_revs / self._gear_ratio) * self._flywheel_circumference_m

    @property
    def total_revolutions(self) -> int:
        with self._lock:
            return self._total_revolutions

    def reset(self) -> None:
        """Reset counters (e.g., at session start)."""
        with self._lock:
            self._pulse_count = 0
            self._total_revolutions = 0
            self._last_pulse_time = 0.0
            self._pulse_interval = 0.0
        logger.info("Speed sensor counters reset")

    # --- Mock helpers for testing / development ---

    def mock_pulse(self) -> None:
        """Simulate a sensor pulse (mock mode only)."""
        if self._mock:
            self._on_pulse(self._pin)

    def mock_set_rpm(self, rpm: float) -> None:
        """Set a simulated RPM value (mock mode only)."""
        if self._mock and rpm > 0:
            interval = 60.0 / rpm
            now = time.monotonic()
            with self._lock:
                self._pulse_interval = interval
                self._last_pulse_time = now

    def cleanup(self) -> None:
        """Remove GPIO event detection and release pin."""
        if not self._mock:
            GPIO.remove_event_detect(self._pin)
            GPIO.cleanup(self._pin)
            logger.info("Speed sensor GPIO cleaned up")
