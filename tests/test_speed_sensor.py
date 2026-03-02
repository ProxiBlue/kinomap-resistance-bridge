"""Tests for the speed sensor module (mock mode)."""

import time
import pytest

from src.gpio.speed_sensor import SpeedSensor


def _sensor_config(**overrides):
    """Create a config dict with mock GPIO and speed sensor enabled."""
    config = {
        "gpio": {"mock": True},
        "speed_sensor": {
            "enabled": True,
            "pin": 22,
            "pull_up": True,
            "debounce_ms": 5,
            "timeout_s": 2.0,
            "flywheel_circumference_m": 0.5,
            "gear_ratio": 5.0,
            "power_estimation": {
                "enabled": True,
                "base_watts_per_kmh": 3.0,
                "watts_per_level": 1.5,
            },
        },
    }
    for key, value in overrides.items():
        parts = key.split(".")
        d = config
        for part in parts[:-1]:
            d = d[part]
        d[parts[-1]] = value
    return config


class TestSpeedSensorBasics:
    def test_initial_rpm_is_zero(self):
        sensor = SpeedSensor(_sensor_config())
        assert sensor.rpm == 0.0

    def test_initial_speed_is_zero(self):
        sensor = SpeedSensor(_sensor_config())
        assert sensor.speed_kmh == 0.0

    def test_initial_cadence_is_zero(self):
        sensor = SpeedSensor(_sensor_config())
        assert sensor.cadence_rpm == 0.0

    def test_total_distance_starts_at_zero(self):
        sensor = SpeedSensor(_sensor_config())
        assert sensor.total_distance_m == 0.0


class TestSpeedSensorMockPulses:
    def test_mock_set_rpm(self):
        sensor = SpeedSensor(_sensor_config())
        sensor.mock_set_rpm(120.0)
        assert sensor.rpm == pytest.approx(120.0, rel=0.01)

    def test_speed_from_rpm(self):
        # circumference=0.5m, gear_ratio=5.0
        # At 300 flywheel RPM: effective_rpm = 300/5 = 60
        # speed = 60 * 0.5 * 60 / 1000 = 1.8 km/h
        sensor = SpeedSensor(_sensor_config())
        sensor.mock_set_rpm(300.0)
        assert sensor.speed_kmh == pytest.approx(1.8, rel=0.01)

    def test_cadence_from_rpm(self):
        # gear_ratio=5.0, flywheel at 300 RPM → cadence = 300/5 = 60 RPM
        sensor = SpeedSensor(_sensor_config())
        sensor.mock_set_rpm(300.0)
        assert sensor.cadence_rpm == pytest.approx(60.0, rel=0.01)

    def test_pulse_counting(self):
        sensor = SpeedSensor(_sensor_config())
        sensor.mock_pulse()
        sensor.mock_pulse()
        sensor.mock_pulse()
        assert sensor.total_revolutions == 3

    def test_distance_from_revolutions(self):
        # 10 revolutions, circumference=0.5m, gear_ratio=5.0
        # distance = (10 / 5.0) * 0.5 = 1.0m
        sensor = SpeedSensor(_sensor_config())
        for _ in range(10):
            sensor.mock_pulse()
        assert sensor.total_distance_m == pytest.approx(1.0, rel=0.01)

    def test_reset_clears_counters(self):
        sensor = SpeedSensor(_sensor_config())
        sensor.mock_set_rpm(100.0)
        sensor.mock_pulse()
        sensor.mock_pulse()
        sensor.reset()
        assert sensor.total_revolutions == 0
        assert sensor.total_distance_m == 0.0
        assert sensor.rpm == 0.0


class TestSpeedSensorTimeout:
    def test_speed_zero_after_timeout(self):
        sensor = SpeedSensor(_sensor_config(**{"speed_sensor.timeout_s": 0.1}))
        sensor.mock_set_rpm(100.0)
        assert sensor.rpm > 0
        # Wait for timeout
        time.sleep(0.15)
        assert sensor.rpm == 0.0
        assert sensor.speed_kmh == 0.0


class TestSpeedSensorGearRatio:
    def test_gear_ratio_1(self):
        # 1:1 ratio, 60 flywheel RPM, circumference 1.0m
        # speed = 60 * 1.0 * 60 / 1000 = 3.6 km/h
        config = _sensor_config(
            **{"speed_sensor.gear_ratio": 1.0, "speed_sensor.flywheel_circumference_m": 1.0}
        )
        sensor = SpeedSensor(config)
        sensor.mock_set_rpm(60.0)
        assert sensor.speed_kmh == pytest.approx(3.6, rel=0.01)
        assert sensor.cadence_rpm == pytest.approx(60.0, rel=0.01)

    def test_high_gear_ratio(self):
        # gear_ratio=10, flywheel at 600 RPM → cadence = 60, same speed math
        config = _sensor_config(**{"speed_sensor.gear_ratio": 10.0})
        sensor = SpeedSensor(config)
        sensor.mock_set_rpm(600.0)
        assert sensor.cadence_rpm == pytest.approx(60.0, rel=0.01)
