"""Kinomap Resistance Bridge — main entry point.

Starts the FTMS BLE service, performs homing, and runs the main event loop
that bridges Kinomap commands to physical button presses.

Usage:
    python -m src.main [--config PATH] [--log-level LEVEL] [--no-home]
"""

import argparse
import asyncio
import logging
import signal
import sys

from .bridge.command_handler import CommandHandler
from .config import load_config, setup_logging
from .ftms.ftms_service import FTMSService
from .gpio.button_simulator import ButtonSimulator
from .gpio.speed_sensor import SpeedSensor

logger = logging.getLogger(__name__)


class Bridge:
    """Main application: ties together FTMS, command handling, and GPIO."""

    def __init__(self, config: dict):
        self._config = config
        self._button_sim = ButtonSimulator(config)

        # Speed sensor (optional — uses simulated telemetry if disabled)
        self._speed_sensor: SpeedSensor | None = None
        if config.get("speed_sensor", {}).get("enabled", False):
            self._speed_sensor = SpeedSensor(config)
            logger.info("Speed sensor enabled on GPIO%d", config["speed_sensor"]["pin"])
        else:
            logger.info("Speed sensor disabled — using simulated telemetry")

        self._handler = CommandHandler(config, self._button_sim, self._speed_sensor)
        self._ftms = FTMSService(config, self._handler.handle_control_point)
        self._running = False
        self._telemetry_interval = config["telemetry"]["notification_interval_ms"] / 1000.0

    async def run(self, skip_home: bool = False) -> None:
        """Start all components and run the main loop."""
        self._running = True

        # Start button simulator thread
        self._button_sim.start()

        # Homing sequence
        if not skip_home and self._config["bridge"]["home_on_startup"]:
            home_cfg = self._config["bridge"]
            self._button_sim.home(home_cfg["home_presses"], home_cfg["home_press_delay_ms"])

        # Start FTMS BLE service
        await self._ftms.start()
        logger.info("Bridge is running. Waiting for Kinomap to connect...")

        # Main telemetry loop
        try:
            while self._running:
                telemetry = self._handler.get_telemetry()
                await self._ftms.send_bike_data(**telemetry)
                await asyncio.sleep(self._telemetry_interval)
        except asyncio.CancelledError:
            logger.info("Main loop cancelled")

        await self.shutdown()

    async def shutdown(self) -> None:
        """Clean up all resources."""
        self._running = False
        await self._ftms.stop()
        self._button_sim.stop()
        if self._speed_sensor:
            self._speed_sensor.cleanup()
        logger.info("Bridge shut down")

    def request_home(self) -> None:
        """Trigger a re-homing sequence (e.g., from a signal handler)."""
        home_cfg = self._config["bridge"]
        logger.info("Re-homing requested")
        self._button_sim.home(home_cfg["home_presses"], home_cfg["home_press_delay_ms"])


def main():
    parser = argparse.ArgumentParser(description="Kinomap Resistance Bridge")
    parser.add_argument("--config", type=str, help="Path to config YAML file")
    parser.add_argument("--log-level", type=str, help="Override log level (DEBUG, INFO, WARNING, ERROR)")
    parser.add_argument("--no-home", action="store_true", help="Skip homing on startup")
    args = parser.parse_args()

    config = load_config(args.config)
    if args.log_level:
        config.setdefault("logging", {})["level"] = args.log_level
    setup_logging(config)

    logger.info("Kinomap Resistance Bridge starting")
    logger.info("Config: %s", "local.yaml" if args.config is None else args.config)

    bridge = Bridge(config)

    # Handle graceful shutdown
    loop = asyncio.new_event_loop()

    def handle_shutdown(sig):
        logger.info("Received signal %s, shutting down...", sig.name)
        loop.create_task(bridge.shutdown())

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, handle_shutdown, sig)

    # Handle SIGUSR1 for re-homing
    loop.add_signal_handler(signal.SIGUSR1, bridge.request_home)

    try:
        loop.run_until_complete(bridge.run(skip_home=args.no_home))
    finally:
        loop.close()

    logger.info("Goodbye!")


if __name__ == "__main__":
    main()
