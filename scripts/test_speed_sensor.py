#!/usr/bin/env python3
"""Standalone speed sensor tester.

Reads the Hall effect sensor and displays live RPM/speed data.
Spin the flywheel by hand to see values update.

Usage:
    python scripts/test_speed_sensor.py               # Live monitoring
    python scripts/test_speed_sensor.py --mock         # Mock mode (no hardware)
    python scripts/test_speed_sensor.py --raw          # Show raw pulse timestamps
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import load_config, setup_logging
from src.gpio.speed_sensor import SpeedSensor


def live_monitor(sensor: SpeedSensor):
    """Show live RPM, speed, and cadence, updating every 500ms."""
    print("\n=== Speed Sensor Live Monitor ===")
    print(f"  Pin: GPIO {sensor._pin}")
    print(f"  Flywheel circumference: {sensor._flywheel_circumference_m:.3f} m")
    print(f"  Gear ratio: {sensor._gear_ratio:.1f}")
    print("\nSpin the flywheel to see data. Press Ctrl+C to stop.\n")
    print(f"{'RPM':>8}  {'Speed (km/h)':>12}  {'Cadence (rpm)':>14}  {'Distance (m)':>13}  {'Revolutions':>12}")
    print("-" * 68)

    try:
        while True:
            rpm = sensor.rpm
            speed = sensor.speed_kmh
            cadence = sensor.cadence_rpm
            dist = sensor.total_distance_m
            revs = sensor.total_revolutions

            print(
                f"\r{rpm:8.1f}  {speed:12.1f}  {cadence:14.1f}  {dist:13.1f}  {revs:12d}",
                end="", flush=True,
            )
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n\nStopped.")


def raw_pulse_monitor(sensor: SpeedSensor):
    """Show raw pulse count, useful for verifying the sensor triggers."""
    print("\n=== Raw Pulse Monitor ===")
    print("Watching for pulses. Spin the flywheel. Press Ctrl+C to stop.\n")

    last_count = 0
    try:
        while True:
            count = sensor.total_revolutions
            if count != last_count:
                print(f"  Pulse #{count}  (interval: {sensor._pulse_interval*1000:.1f} ms)")
                last_count = count
            time.sleep(0.01)
    except KeyboardInterrupt:
        print(f"\n\nTotal pulses: {sensor.total_revolutions}")


def mock_demo(sensor: SpeedSensor):
    """Demo with simulated pulses at various RPMs."""
    print("\n=== Mock Speed Sensor Demo ===\n")

    for rpm in [0, 30, 60, 90, 120, 60, 0]:
        sensor.mock_set_rpm(rpm)
        speed = sensor.speed_kmh
        cadence = sensor.cadence_rpm
        print(f"  Set RPM={rpm:3d}  →  speed={speed:5.1f} km/h  cadence={cadence:5.1f} rpm")
        time.sleep(0.5)

    print("\nDemo complete.")


def main():
    parser = argparse.ArgumentParser(description="Test speed sensor")
    parser.add_argument("--config", type=str, help="Config file path")
    parser.add_argument("--mock", action="store_true", help="Force mock mode")
    parser.add_argument("--raw", action="store_true", help="Show raw pulse timestamps")
    args = parser.parse_args()

    config = load_config(args.config)
    if args.mock:
        config["gpio"]["mock"] = True
    setup_logging(config)

    sensor = SpeedSensor(config)

    try:
        if args.mock:
            mock_demo(sensor)
        elif args.raw:
            raw_pulse_monitor(sensor)
        else:
            live_monitor(sensor)
    finally:
        sensor.cleanup()


if __name__ == "__main__":
    main()
