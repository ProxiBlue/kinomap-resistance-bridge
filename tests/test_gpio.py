"""Tests for GPIO relay controller and button simulator (mock mode)."""

import time
import pytest

from src.gpio.relay_controller import RelayController
from src.gpio.button_simulator import ButtonSimulator


def _mock_config(**overrides):
    """Create a config dict with mock GPIO enabled."""
    config = {
        "gpio": {
            "pin_up": 17,
            "pin_down": 27,
            "relay_active_low": False,
            "button_hold_ms": 10,      # Short for fast tests
            "inter_press_delay_ms": 10,
            "mock": True,
        },
        "bridge": {
            "total_levels": 16,
            "initial_level": 1,
            "min_level": 1,
            "max_level": 16,
            "home_on_startup": False,
            "home_presses": 20,
            "home_press_delay_ms": 10,
            "max_presses_per_command": 5,
            "inclination_map": {-10.0: 1, 0.0: 5, 15.0: 16},
            "resistance_pct_map": {0: 1, 100: 16},
        },
    }
    for key, value in overrides.items():
        section, param = key.split(".", 1)
        config[section][param] = value
    return config


class TestRelayController:
    def test_mock_mode_no_error(self):
        config = _mock_config()
        relay = RelayController(config)
        relay.press_up()
        relay.press_down()
        relay.cleanup()

    def test_inter_press_delay(self):
        config = _mock_config(**{"gpio.inter_press_delay_ms": 200})
        relay = RelayController(config)
        assert relay.inter_press_delay == pytest.approx(0.2)
        relay.cleanup()


class TestButtonSimulator:
    def test_initial_level(self):
        config = _mock_config(**{"bridge.initial_level": 5})
        sim = ButtonSimulator(config)
        assert sim.current_level == 5

    def test_press_up_increments(self):
        config = _mock_config()
        sim = ButtonSimulator(config)
        sim.start()
        sim.press_up(3)
        time.sleep(0.2)  # Allow worker thread to process
        assert sim.current_level == 4  # Started at 1, pressed up 3
        sim.stop()

    def test_press_down_decrements(self):
        config = _mock_config(**{"bridge.initial_level": 10})
        sim = ButtonSimulator(config)
        sim.start()
        sim.press_down(2)
        time.sleep(0.2)
        assert sim.current_level == 8  # Started at 10, pressed down 2
        sim.stop()

    def test_does_not_go_below_min(self):
        config = _mock_config(**{"bridge.initial_level": 2})
        sim = ButtonSimulator(config)
        sim.start()
        sim.press_down(5)  # Try to go 5 below, but min is 1
        time.sleep(0.2)
        assert sim.current_level == 1
        sim.stop()

    def test_does_not_go_above_max(self):
        config = _mock_config(**{"bridge.initial_level": 14})
        sim = ButtonSimulator(config)
        sim.start()
        sim.press_up(5)  # Try to go 5 above, but max is 16
        time.sleep(0.2)
        assert sim.current_level == 16
        sim.stop()

    def test_homing(self):
        config = _mock_config(**{"bridge.initial_level": 10})
        sim = ButtonSimulator(config)
        sim.home(presses=20, delay_ms=5)
        assert sim.current_level == 1  # Should be at min after homing
