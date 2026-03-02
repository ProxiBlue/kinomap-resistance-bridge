#!/usr/bin/env python3
"""BLE scanning utility.

Scans for nearby BLE devices and specifically looks for FTMS services.
Useful for verifying that the bridge's advertisement is visible.

Usage:
    python scripts/scan_ble.py              # Scan for 10 seconds
    python scripts/scan_ble.py --duration 30  # Scan for 30 seconds
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

FTMS_UUID = "00001826-0000-1000-8000-00805f9b34fb"


async def scan(duration: int):
    """Scan for BLE devices and report FTMS-capable ones."""
    # Try to use bleak for scanning (more portable than raw BlueZ)
    try:
        from bleak import BleakScanner
    except ImportError:
        print("'bleak' package not installed. Install it with:")
        print("  pip install bleak")
        print()
        print("Alternatively, use bluetoothctl to scan:")
        print("  sudo bluetoothctl")
        print("  > scan on")
        print("  (wait, then look for 'RPi Resistance Bridge')")
        print("  > scan off")
        print("  > exit")
        sys.exit(1)

    print(f"Scanning for BLE devices for {duration} seconds...")
    print(f"Looking for FTMS service UUID: {FTMS_UUID}")
    print()

    ftms_devices = []

    def detection_callback(device, advertisement_data):
        uuids = advertisement_data.service_uuids or []
        is_ftms = FTMS_UUID in uuids

        rssi = advertisement_data.rssi
        name = advertisement_data.local_name or device.name or "Unknown"

        if is_ftms:
            ftms_devices.append((name, device.address, rssi))
            print(f"  ** FTMS DEVICE: {name} [{device.address}] RSSI={rssi}dBm **")
        else:
            print(f"     {name} [{device.address}] RSSI={rssi}dBm")

    scanner = BleakScanner(detection_callback)
    await scanner.start()
    await asyncio.sleep(duration)
    await scanner.stop()

    print()
    print("=" * 50)
    if ftms_devices:
        print(f"Found {len(ftms_devices)} FTMS device(s):")
        for name, addr, rssi in ftms_devices:
            print(f"  {name} [{addr}] RSSI={rssi}dBm")
    else:
        print("No FTMS devices found.")
        print("If the bridge is running, check:")
        print("  - Is Bluetooth enabled? (hciconfig)")
        print("  - Is the bridge process running? (ps aux | grep src.main)")
        print("  - Check bridge logs for BLE errors")


def main():
    parser = argparse.ArgumentParser(description="Scan for BLE devices")
    parser.add_argument("--duration", type=int, default=10, help="Scan duration in seconds")
    args = parser.parse_args()

    asyncio.run(scan(args.duration))


if __name__ == "__main__":
    main()
