"""Tests for the bridge layer: resistance mapping and command handling."""

import struct
import time
import pytest

from src.bridge.resistance_mapper import ResistanceMapper
from src.bridge.command_handler import CommandHandler
from src.ftms.characteristics import (
    OP_REQUEST_CONTROL,
    OP_SET_INDOOR_BIKE_SIMULATION,
    OP_SET_TARGET_INCLINATION,
    OP_SET_TARGET_RESISTANCE,
    OP_START_RESUME,
    OP_STOP_PAUSE,
    RESULT_CONTROL_NOT_PERMITTED,
    RESULT_SUCCESS,
)
from src.gpio.button_simulator import ButtonSimulator


def _test_config():
    return {
        "gpio": {
            "pin_up": 17,
            "pin_down": 27,
            "relay_active_low": False,
            "button_hold_ms": 5,
            "inter_press_delay_ms": 5,
            "mock": True,
        },
        "bridge": {
            "total_levels": 16,
            "initial_level": 5,
            "min_level": 1,
            "max_level": 16,
            "home_on_startup": False,
            "home_presses": 20,
            "home_press_delay_ms": 5,
            "max_presses_per_command": 5,
            "inclination_map": {
                -10.0: 1,
                -5.0: 2,
                0.0: 5,
                5.0: 9,
                10.0: 14,
                15.0: 16,
            },
            "resistance_pct_map": {
                0: 1,
                50: 8,
                100: 16,
            },
        },
        "telemetry": {
            "notification_interval_ms": 1000,
            "base_speed_kmh": 20.0,
            "speed_resistance_factor": 0.8,
            "cadence_rpm": 70,
            "power_base_watts": 50,
            "power_per_level_watts": 15,
        },
    }


class TestResistanceMapper:
    def setup_method(self):
        self.mapper = ResistanceMapper(_test_config())

    def test_flat_terrain(self):
        assert self.mapper.from_inclination(0.0) == 5

    def test_steep_uphill(self):
        assert self.mapper.from_inclination(15.0) == 16

    def test_steep_downhill(self):
        assert self.mapper.from_inclination(-10.0) == 1

    def test_interpolation_midpoint(self):
        # Between 0.0→5 and 5.0→9, at 2.5 should be ~7
        level = self.mapper.from_inclination(2.5)
        assert level == 7

    def test_beyond_max_clamps(self):
        assert self.mapper.from_inclination(20.0) == 16

    def test_beyond_min_clamps(self):
        assert self.mapper.from_inclination(-15.0) == 1

    def test_resistance_percent_zero(self):
        assert self.mapper.from_resistance_percent(0) == 1

    def test_resistance_percent_100(self):
        assert self.mapper.from_resistance_percent(100) == 16

    def test_resistance_percent_50(self):
        assert self.mapper.from_resistance_percent(50) == 8


class TestCommandHandler:
    def setup_method(self):
        self.config = _test_config()
        self.sim = ButtonSimulator(self.config)
        self.sim.start()
        self.handler = CommandHandler(self.config, self.sim)

    def teardown_method(self):
        self.sim.stop()

    def test_control_required(self):
        # Sending inclination without requesting control first
        data = bytes([OP_SET_TARGET_INCLINATION]) + struct.pack("<h", 50)
        result = self.handler.handle_control_point(OP_SET_TARGET_INCLINATION, data)
        assert result == RESULT_CONTROL_NOT_PERMITTED

    def test_request_control(self):
        result = self.handler.handle_control_point(OP_REQUEST_CONTROL, bytes([OP_REQUEST_CONTROL]))
        assert result == RESULT_SUCCESS

    def test_set_inclination_after_control(self):
        self.handler.handle_control_point(OP_REQUEST_CONTROL, bytes([OP_REQUEST_CONTROL]))

        # Set +5% grade → should map to level 9
        data = bytes([OP_SET_TARGET_INCLINATION]) + struct.pack("<h", 50)  # 50 * 0.1 = 5.0%
        result = self.handler.handle_control_point(OP_SET_TARGET_INCLINATION, data)
        assert result == RESULT_SUCCESS

        # Wait for button presses to execute
        time.sleep(0.3)
        assert self.sim.current_level == 9

    def test_indoor_bike_simulation(self):
        self.handler.handle_control_point(OP_REQUEST_CONTROL, bytes([OP_REQUEST_CONTROL]))

        # Simulate 8% grade
        wind = struct.pack("<h", 0)
        grade = struct.pack("<h", 800)  # 800 * 0.01 = 8.0%
        data = bytes([OP_SET_INDOOR_BIKE_SIMULATION]) + wind + grade + bytes([33, 51])
        result = self.handler.handle_control_point(OP_SET_INDOOR_BIKE_SIMULATION, data)
        assert result == RESULT_SUCCESS

        time.sleep(0.5)
        # 8.0% should interpolate between 5.0→9 and 10.0→14: about level 12
        assert self.sim.current_level == 12

    def test_telemetry_values(self):
        telemetry = self.handler.get_telemetry()
        assert "speed_kmh" in telemetry
        assert "cadence_rpm" in telemetry
        assert "resistance_level" in telemetry
        assert "power_watts" in telemetry
        assert "elapsed_seconds" in telemetry
        assert "total_distance_m" in telemetry
        assert telemetry["resistance_level"] == 5  # initial level
