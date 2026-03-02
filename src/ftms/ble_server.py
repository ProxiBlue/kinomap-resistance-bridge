"""BLE GATT server setup and lifecycle management.

This module handles the BlueZ D-Bus integration for creating a BLE peripheral
that advertises as an FTMS Indoor Bike device. It orchestrates the advertisement
and GATT service registration.

For standalone testing:
    python -m src.ftms.ble_server --test
"""

import argparse
import asyncio
import logging
import sys

from dbus_next.aio import MessageBus

logger = logging.getLogger(__name__)

BLUEZ_BUS_NAME = "org.bluez"
ADAPTER_IFACE = "org.bluez.Adapter1"
GATT_MANAGER_IFACE = "org.bluez.GattManager1"
LE_ADV_MANAGER_IFACE = "org.bluez.LEAdvertisingManager1"


async def find_adapter(bus: MessageBus, adapter_name: str = "hci0") -> str:
    """Find the BlueZ adapter D-Bus object path.

    Args:
        bus: Connected D-Bus message bus.
        adapter_name: Bluetooth adapter name (e.g., "hci0").

    Returns:
        D-Bus object path for the adapter (e.g., "/org/bluez/hci0").

    Raises:
        RuntimeError: If the adapter is not found.
    """
    introspection = await bus.introspect(BLUEZ_BUS_NAME, "/org/bluez")
    proxy = bus.get_proxy_object(BLUEZ_BUS_NAME, "/org/bluez", introspection)

    # Check if the adapter exists
    adapter_path = f"/org/bluez/{adapter_name}"
    try:
        adapter_intro = await bus.introspect(BLUEZ_BUS_NAME, adapter_path)
        adapter_proxy = bus.get_proxy_object(BLUEZ_BUS_NAME, adapter_path, adapter_intro)
        adapter_props = adapter_proxy.get_interface("org.freedesktop.DBus.Properties")

        powered = await adapter_props.call_get(ADAPTER_IFACE, "Powered")
        if not powered.value:
            logger.warning("Adapter %s is not powered on. Attempting to power on...", adapter_name)
            await adapter_props.call_set(ADAPTER_IFACE, "Powered", powered.__class__(True))
            logger.info("Adapter %s powered on", adapter_name)

        address = await adapter_props.call_get(ADAPTER_IFACE, "Address")
        logger.info("Using adapter %s at %s (address: %s)", adapter_name, adapter_path, address.value)
        return adapter_path

    except Exception as e:
        raise RuntimeError(
            f"Bluetooth adapter '{adapter_name}' not found. "
            f"Available adapters can be listed with 'hciconfig'. Error: {e}"
        ) from e


async def check_ble_capabilities(bus: MessageBus, adapter_path: str) -> dict:
    """Check what BLE capabilities the adapter supports.

    Returns a dict with boolean flags for GATT server and advertising support.
    """
    intro = await bus.introspect(BLUEZ_BUS_NAME, adapter_path)
    proxy = bus.get_proxy_object(BLUEZ_BUS_NAME, adapter_path, intro)

    capabilities = {
        "gatt_manager": False,
        "le_advertising": False,
    }

    for iface in intro.interfaces:
        if iface.name == GATT_MANAGER_IFACE:
            capabilities["gatt_manager"] = True
        elif iface.name == LE_ADV_MANAGER_IFACE:
            capabilities["le_advertising"] = True

    return capabilities


async def test_ble_setup():
    """Standalone test: connect to BlueZ, find adapter, check capabilities."""
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")

    logger.info("Connecting to D-Bus system bus...")
    bus = await MessageBus(bus_type=1).connect()

    adapter_path = await find_adapter(bus, "hci0")
    caps = await check_ble_capabilities(bus, adapter_path)

    logger.info("BLE capabilities:")
    logger.info("  GATT Manager: %s", "YES" if caps["gatt_manager"] else "NO")
    logger.info("  LE Advertising: %s", "YES" if caps["le_advertising"] else "NO")

    if caps["gatt_manager"] and caps["le_advertising"]:
        logger.info("All required BLE capabilities are available.")
    else:
        logger.error("Missing required BLE capabilities. Check BlueZ version (need 5.50+).")
        sys.exit(1)

    bus.disconnect()
    logger.info("BLE test complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BLE FTMS server for Kinomap Resistance Bridge")
    parser.add_argument("--test", action="store_true", help="Test BLE adapter setup and exit")
    args = parser.parse_args()

    if args.test:
        asyncio.run(test_ble_setup())
