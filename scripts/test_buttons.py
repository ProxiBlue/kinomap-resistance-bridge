#!/usr/bin/env python3
"""Standalone button/relay tester.

Tests the relay module and GPIO wiring independently from the BLE stack.
Useful for verifying hardware before running the full bridge.

Usage:
    python scripts/test_buttons.py               # Interactive test
    python scripts/test_buttons.py --gpio-only    # Test GPIO without relay
    python scripts/test_buttons.py --cycle 5      # Press up 5, then down 5
"""

import argparse
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import load_config, setup_logging
from src.gpio.relay_controller import RelayController


def interactive_test(relay: RelayController):
    """Interactive test mode — press buttons manually."""
    print("\n=== Interactive Relay Test ===")
    print(f"  UP pin:   GPIO {relay.pin_up}")
    print(f"  DOWN pin: GPIO {relay.pin_down}")
    print("\nCommands:")
    print("  u = press UP once")
    print("  d = press DOWN once")
    print("  U = press UP 5 times")
    print("  D = press DOWN 5 times")
    print("  q = quit")
    print()

    while True:
        try:
            cmd = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if cmd == "q":
            break
        elif cmd == "u":
            print("Pressing UP...")
            relay.press_up()
            print("Done.")
        elif cmd == "d":
            print("Pressing DOWN...")
            relay.press_down()
            print("Done.")
        elif cmd == "U":
            print("Pressing UP x5...")
            for i in range(5):
                relay.press_up()
                time.sleep(relay.inter_press_delay)
                print(f"  {i+1}/5")
            print("Done.")
        elif cmd == "D":
            print("Pressing DOWN x5...")
            for i in range(5):
                relay.press_down()
                time.sleep(relay.inter_press_delay)
                print(f"  {i+1}/5")
            print("Done.")
        else:
            print("Unknown command. Use u/d/U/D/q.")


def cycle_test(relay: RelayController, count: int):
    """Press UP count times, then DOWN count times."""
    print(f"\n=== Cycle Test: {count} UP, then {count} DOWN ===")

    print(f"\nPressing UP x{count}...")
    for i in range(count):
        relay.press_up()
        time.sleep(relay.inter_press_delay)
        print(f"  UP {i+1}/{count}")

    print(f"\nPausing 1 second...")
    time.sleep(1.0)

    print(f"\nPressing DOWN x{count}...")
    for i in range(count):
        relay.press_down()
        time.sleep(relay.inter_press_delay)
        print(f"  DOWN {i+1}/{count}")

    print("\nCycle complete.")


def gpio_only_test(relay: RelayController):
    """Quick GPIO pin toggle test without caring about relay response."""
    print("\n=== GPIO-Only Test ===")
    print("Toggling each pin for 500ms. Watch relay LEDs or use multimeter.\n")

    print(f"Activating UP (GPIO {relay.pin_up}) for 500ms...")
    relay.press(relay.pin_up, hold_ms=500)
    print("  Released.")

    time.sleep(0.5)

    print(f"Activating DOWN (GPIO {relay.pin_down}) for 500ms...")
    relay.press(relay.pin_down, hold_ms=500)
    print("  Released.")

    print("\nGPIO test complete.")


def main():
    parser = argparse.ArgumentParser(description="Test relay/GPIO wiring")
    parser.add_argument("--config", type=str, help="Config file path")
    parser.add_argument("--gpio-only", action="store_true", help="Quick GPIO toggle test")
    parser.add_argument("--cycle", type=int, metavar="N", help="Press UP N times then DOWN N times")
    parser.add_argument("--mock", action="store_true", help="Force mock mode (no real GPIO)")
    args = parser.parse_args()

    config = load_config(args.config)
    if args.mock:
        config["gpio"]["mock"] = True
    setup_logging(config)

    relay = RelayController(config)

    try:
        if args.gpio_only:
            gpio_only_test(relay)
        elif args.cycle:
            cycle_test(relay, args.cycle)
        else:
            interactive_test(relay)
    finally:
        relay.cleanup()


if __name__ == "__main__":
    main()
