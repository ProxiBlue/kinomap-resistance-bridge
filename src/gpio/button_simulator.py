"""Button press sequencing and queued execution.

Runs in a separate thread to avoid blocking the BLE event loop.
Accepts press commands via a thread-safe queue.
"""

import logging
import queue
import threading
import time
from dataclasses import dataclass
from typing import Any

from .relay_controller import RelayController

logger = logging.getLogger(__name__)


@dataclass
class PressCommand:
    """A command to press a button N times."""
    direction: str  # "up" or "down"
    count: int


class ButtonSimulator:
    """Queued button press executor running in a background thread."""

    def __init__(self, config: dict[str, Any]):
        self._relay = RelayController(config)
        self._queue: queue.Queue[PressCommand | None] = queue.Queue()
        self._thread = threading.Thread(target=self._worker, daemon=True, name="button-sim")
        self._running = False
        self._current_level: int = config["bridge"]["initial_level"]
        self._min_level: int = config["bridge"]["min_level"]
        self._max_level: int = config["bridge"]["max_level"]

    def start(self) -> None:
        """Start the background worker thread."""
        self._running = True
        self._thread.start()
        logger.info("Button simulator started")

    def stop(self) -> None:
        """Signal the worker to stop and wait for it to finish."""
        self._running = False
        self._queue.put(None)  # Sentinel to unblock the worker
        self._thread.join(timeout=5.0)
        self._relay.cleanup()
        logger.info("Button simulator stopped")

    def press_up(self, count: int = 1) -> None:
        """Queue resistance UP presses."""
        if count > 0:
            self._queue.put(PressCommand("up", count))

    def press_down(self, count: int = 1) -> None:
        """Queue resistance DOWN presses."""
        if count > 0:
            self._queue.put(PressCommand("down", count))

    def home(self, presses: int, delay_ms: int) -> None:
        """Execute homing sequence: press DOWN enough times to reach minimum.

        This runs synchronously (blocks until complete) and should be called
        before the main loop starts.
        """
        logger.info("Homing: pressing DOWN %d times to find level %d", presses, self._min_level)
        for i in range(presses):
            self._relay.press_down()
            time.sleep(delay_ms / 1000.0)
        self._current_level = self._min_level
        logger.info("Homing complete, current level = %d", self._current_level)

    @property
    def current_level(self) -> int:
        return self._current_level

    def _worker(self) -> None:
        """Background thread: process press commands from the queue."""
        logger.debug("Button simulator worker started")
        while self._running:
            try:
                cmd = self._queue.get(timeout=1.0)
            except queue.Empty:
                continue

            if cmd is None:
                break

            self._execute(cmd)

        logger.debug("Button simulator worker exited")

    def _execute(self, cmd: PressCommand) -> None:
        """Execute a press command, updating tracked level."""
        for i in range(cmd.count):
            if cmd.direction == "up":
                if self._current_level >= self._max_level:
                    logger.debug("Already at max level %d, skipping UP press", self._max_level)
                    break
                self._relay.press_up()
                self._current_level += 1
            else:
                if self._current_level <= self._min_level:
                    logger.debug("Already at min level %d, skipping DOWN press", self._min_level)
                    break
                self._relay.press_down()
                self._current_level -= 1

            logger.info(
                "Pressed %s (%d/%d), level now %d",
                cmd.direction.upper(), i + 1, cmd.count, self._current_level,
            )

            if i < cmd.count - 1:
                time.sleep(self._relay.inter_press_delay)
