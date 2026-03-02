"""Low-level GPIO relay control.

Handles direct interaction with relay module pins. Supports both real GPIO
(on Raspberry Pi) and mock mode for development/testing on other platforms.
"""

import logging
import time
from typing import Any

logger = logging.getLogger(__name__)

try:
    import RPi.GPIO as GPIO
    _HAS_GPIO = True
except ImportError:
    _HAS_GPIO = False
    logger.info("RPi.GPIO not available — relay controller will use mock mode")


class RelayController:
    """Controls individual relay channels via GPIO pins."""

    def __init__(self, config: dict[str, Any]):
        gpio_cfg = config["gpio"]
        self._pin_up: int = gpio_cfg["pin_up"]
        self._pin_down: int = gpio_cfg["pin_down"]
        self._active_low: bool = gpio_cfg["relay_active_low"]
        self._hold_ms: int = gpio_cfg["button_hold_ms"]
        self._inter_press_ms: int = gpio_cfg["inter_press_delay_ms"]
        self._mock: bool = gpio_cfg.get("mock", False) or not _HAS_GPIO

        if self._mock:
            logger.info("Relay controller running in MOCK mode (no GPIO)")
        else:
            self._setup_gpio()

    def _setup_gpio(self) -> None:
        """Initialize GPIO pins for relay control."""
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        off_state = GPIO.HIGH if self._active_low else GPIO.LOW

        GPIO.setup(self._pin_up, GPIO.OUT, initial=off_state)
        GPIO.setup(self._pin_down, GPIO.OUT, initial=off_state)

        logger.info(
            "GPIO initialized: UP=GPIO%d, DOWN=GPIO%d, active_low=%s",
            self._pin_up, self._pin_down, self._active_low,
        )

    def _activate_pin(self, pin: int) -> None:
        """Set a GPIO pin to the active state (relay ON)."""
        if self._mock:
            return
        state = GPIO.LOW if self._active_low else GPIO.HIGH
        GPIO.output(pin, state)

    def _deactivate_pin(self, pin: int) -> None:
        """Set a GPIO pin to the inactive state (relay OFF)."""
        if self._mock:
            return
        state = GPIO.HIGH if self._active_low else GPIO.LOW
        GPIO.output(pin, state)

    def press(self, pin: int, hold_ms: int | None = None) -> None:
        """Simulate a single button press by briefly activating a relay.

        Args:
            pin: GPIO pin number (BCM).
            hold_ms: Override hold duration. Uses config default if None.
        """
        hold = hold_ms if hold_ms is not None else self._hold_ms
        pin_name = "UP" if pin == self._pin_up else "DOWN" if pin == self._pin_down else f"GPIO{pin}"

        logger.debug("Pressing %s (GPIO%d) for %dms", pin_name, pin, hold)

        self._activate_pin(pin)
        time.sleep(hold / 1000.0)
        self._deactivate_pin(pin)

    def press_up(self) -> None:
        """Simulate pressing the resistance UP button."""
        self.press(self._pin_up)

    def press_down(self) -> None:
        """Simulate pressing the resistance DOWN button."""
        self.press(self._pin_down)

    @property
    def inter_press_delay(self) -> float:
        """Delay between consecutive presses, in seconds."""
        return self._inter_press_ms / 1000.0

    @property
    def pin_up(self) -> int:
        return self._pin_up

    @property
    def pin_down(self) -> int:
        return self._pin_down

    def cleanup(self) -> None:
        """Release GPIO resources."""
        if not self._mock:
            self._deactivate_pin(self._pin_up)
            self._deactivate_pin(self._pin_down)
            GPIO.cleanup([self._pin_up, self._pin_down])
            logger.info("GPIO cleaned up")
