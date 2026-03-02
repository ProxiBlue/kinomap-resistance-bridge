"""Orchestrates the FTMS → resistance level → button press pipeline.

Receives decoded FTMS commands, maps them to target resistance levels,
calculates the delta from current level, and queues button presses.
"""

import logging
import time
from typing import Any

from ..ftms import characteristics as chars
from ..gpio.button_simulator import ButtonSimulator
from ..gpio.speed_sensor import SpeedSensor
from .resistance_mapper import ResistanceMapper

logger = logging.getLogger(__name__)


class CommandHandler:
    """Handles FTMS control point commands and drives the button simulator."""

    def __init__(
        self,
        config: dict[str, Any],
        button_sim: ButtonSimulator,
        speed_sensor: SpeedSensor | None = None,
    ):
        self._config = config
        self._mapper = ResistanceMapper(config)
        self._button_sim = button_sim
        self._speed_sensor = speed_sensor
        self._max_presses = config["bridge"]["max_presses_per_command"]
        self._control_granted = False
        self._session_active = False
        self._start_time: float | None = None

        # Telemetry config (used as fallback when no speed sensor)
        tel = config["telemetry"]
        self._base_speed = tel["base_speed_kmh"]
        self._speed_factor = tel["speed_resistance_factor"]
        self._cadence = tel["cadence_rpm"]
        self._power_base = tel["power_base_watts"]
        self._power_per_level = tel["power_per_level_watts"]

        # Power estimation from speed sensor
        self._power_from_sensor = False
        if speed_sensor and config.get("speed_sensor", {}).get("power_estimation", {}).get("enabled"):
            pe = config["speed_sensor"]["power_estimation"]
            self._power_from_sensor = True
            self._base_watts_per_kmh = pe["base_watts_per_kmh"]
            self._watts_per_level = pe["watts_per_level"]

    def handle_control_point(self, opcode: int, data: bytes) -> int:
        """Process an FTMS control point write.

        Args:
            opcode: The FTMS opcode (first byte of the write).
            data: The full raw data including the opcode byte.

        Returns:
            FTMS result code (success, not supported, etc.)
        """
        if opcode == chars.OP_REQUEST_CONTROL:
            self._control_granted = True
            logger.info("Control granted to connected app")
            return chars.RESULT_SUCCESS

        if not self._control_granted and opcode != chars.OP_RESET:
            logger.warning("Command 0x%02x rejected: control not granted", opcode)
            return chars.RESULT_CONTROL_NOT_PERMITTED

        if opcode == chars.OP_RESET:
            self._control_granted = False
            self._session_active = False
            self._start_time = None
            logger.info("Reset received")
            return chars.RESULT_SUCCESS

        if opcode == chars.OP_START_RESUME:
            self._session_active = True
            self._start_time = time.time()
            logger.info("Session started")
            return chars.RESULT_SUCCESS

        if opcode == chars.OP_STOP_PAUSE:
            self._session_active = False
            action = "stopped" if len(data) > 1 and data[1] == 1 else "paused"
            logger.info("Session %s", action)
            return chars.RESULT_SUCCESS

        if opcode == chars.OP_SET_TARGET_INCLINATION:
            grade = chars.decode_set_target_inclination(data)
            target_level = self._mapper.from_inclination(grade)
            logger.info("Set Target Inclination: %.1f%% → level %d", grade, target_level)
            self._move_to_level(target_level)
            return chars.RESULT_SUCCESS

        if opcode == chars.OP_SET_TARGET_RESISTANCE:
            resistance_pct = chars.decode_set_target_resistance(data)
            target_level = self._mapper.from_resistance_percent(resistance_pct)
            logger.info("Set Target Resistance: %.1f%% → level %d", resistance_pct, target_level)
            self._move_to_level(target_level)
            return chars.RESULT_SUCCESS

        if opcode == chars.OP_SET_INDOOR_BIKE_SIMULATION:
            sim = chars.decode_indoor_bike_simulation(data)
            target_level = self._mapper.from_inclination(sim["grade_percent"])
            logger.info(
                "Indoor Bike Simulation: grade=%.2f%%, wind=%.3f m/s → level %d",
                sim["grade_percent"], sim["wind_speed_ms"], target_level,
            )
            self._move_to_level(target_level)
            return chars.RESULT_SUCCESS

        logger.warning("Unsupported opcode: 0x%02x", opcode)
        return chars.RESULT_NOT_SUPPORTED

    def _move_to_level(self, target: int) -> None:
        """Calculate and queue the button presses needed to reach the target level."""
        current = self._button_sim.current_level
        delta = target - current

        if delta == 0:
            logger.debug("Already at level %d", current)
            return

        # Apply safety limit
        clamped_delta = max(-self._max_presses, min(self._max_presses, delta))
        if clamped_delta != delta:
            logger.warning(
                "Clamped delta from %d to %d (max_presses_per_command=%d)",
                delta, clamped_delta, self._max_presses,
            )

        if clamped_delta > 0:
            logger.info("Moving UP %d levels: %d → %d", clamped_delta, current, current + clamped_delta)
            self._button_sim.press_up(clamped_delta)
        else:
            logger.info("Moving DOWN %d levels: %d → %d", -clamped_delta, current, current + clamped_delta)
            self._button_sim.press_down(-clamped_delta)

    def get_telemetry(self) -> dict:
        """Generate telemetry data for FTMS notifications.

        Uses real speed sensor data when available, falls back to simulated values.
        Returns a dict suitable for passing to FTMSService.send_bike_data().
        """
        level = self._button_sim.current_level
        elapsed = int(time.time() - self._start_time) if self._start_time else 0

        if self._speed_sensor:
            # Real data from Hall effect / reed switch sensor
            speed = self._speed_sensor.speed_kmh
            cadence = self._speed_sensor.cadence_rpm
            distance = self._speed_sensor.total_distance_m

            if self._power_from_sensor and speed > 0:
                # Estimate power from speed and resistance level
                watts_per_kmh = self._base_watts_per_kmh + (level - 1) * self._watts_per_level
                power = int(speed * watts_per_kmh)
            else:
                power = self._power_base + (level - 1) * self._power_per_level
        else:
            # Simulated fallback
            speed = max(0.0, self._base_speed - (level - 1) * self._speed_factor)
            cadence = self._cadence
            power = self._power_base + (level - 1) * self._power_per_level
            distance = speed / 3.6 * elapsed  # rough estimate: speed(m/s) * time

        return {
            "speed_kmh": speed,
            "cadence_rpm": cadence,
            "resistance_level": level,
            "power_watts": power,
            "elapsed_seconds": elapsed,
            "total_distance_m": distance,
        }
