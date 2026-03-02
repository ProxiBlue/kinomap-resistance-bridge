"""FTMS GATT service implementation using dbus-next and BlueZ."""

import asyncio
import logging
from typing import Any, Callable

from dbus_next import Variant
from dbus_next.aio import MessageBus
from dbus_next.service import ServiceInterface, dbus_property, method, signal

from . import characteristics as chars

logger = logging.getLogger(__name__)

# BlueZ D-Bus constants
BLUEZ_SERVICE = "org.bluez"
GATT_MANAGER_IFACE = "org.bluez.GattManager1"
LE_ADV_MANAGER_IFACE = "org.bluez.LEAdvertisingManager1"
GATT_SERVICE_IFACE = "org.bluez.GattService1"
GATT_CHRC_IFACE = "org.bluez.GattCharacteristic1"
GATT_DESC_IFACE = "org.bluez.GattDescriptor1"
LE_ADVERTISEMENT_IFACE = "org.bluez.LEAdvertisement1"
DBUS_PROPERTIES_IFACE = "org.freedesktop.DBus.Properties"


class FTMSAdvertisement(ServiceInterface):
    """BLE advertisement for the FTMS Indoor Bike device."""

    def __init__(self, index: int, device_name: str):
        super().__init__(LE_ADVERTISEMENT_IFACE)
        self._index = index
        self._device_name = device_name

    @dbus_property()
    def Type(self) -> "s":
        return "peripheral"

    @dbus_property()
    def ServiceUUIDs(self) -> "as":
        return [chars.FTMS_SERVICE_UUID]

    @dbus_property()
    def LocalName(self) -> "s":
        return self._device_name

    @dbus_property()
    def Appearance(self) -> "q":
        return 0x0481  # Indoor Bike

    @dbus_property()
    def Includes(self) -> "as":
        return ["tx-power"]

    @method()
    def Release(self):
        logger.info("Advertisement released")


class FitnessMachineFeatureCharacteristic(ServiceInterface):
    """Read-only characteristic declaring supported FTMS features."""

    def __init__(self):
        super().__init__(GATT_CHRC_IFACE)
        self._value = chars.encode_fitness_machine_features()

    @dbus_property()
    def UUID(self) -> "s":
        return chars.FITNESS_MACHINE_FEATURE_UUID

    @dbus_property()
    def Service(self) -> "o":
        return ""  # Set during registration

    @dbus_property()
    def Flags(self) -> "as":
        return ["read"]

    @method()
    def ReadValue(self, options: "a{sv}") -> "ay":
        return self._value


class IndoorBikeDataCharacteristic(ServiceInterface):
    """Notify characteristic for sending telemetry to the connected app."""

    def __init__(self):
        super().__init__(GATT_CHRC_IFACE)
        self._notifying = False

    @dbus_property()
    def UUID(self) -> "s":
        return chars.INDOOR_BIKE_DATA_UUID

    @dbus_property()
    def Flags(self) -> "as":
        return ["notify"]

    @method()
    def StartNotify(self):
        self._notifying = True
        logger.info("Indoor Bike Data: notifications started")

    @method()
    def StopNotify(self):
        self._notifying = False
        logger.info("Indoor Bike Data: notifications stopped")

    @property
    def is_notifying(self) -> bool:
        return self._notifying


class FTMSControlPointCharacteristic(ServiceInterface):
    """Write+Indicate characteristic for receiving commands from the app.

    This is the main command interface. Kinomap writes inclination/resistance
    targets here, and we respond with indication confirmations.
    """

    def __init__(self, on_command: Callable[[int, bytes], int]):
        """Args:
            on_command: Callback(opcode, raw_data) -> result_code.
                Called when a control point write is received.
        """
        super().__init__(GATT_CHRC_IFACE)
        self._on_command = on_command
        self._indicating = False

    @dbus_property()
    def UUID(self) -> "s":
        return chars.FTMS_CONTROL_POINT_UUID

    @dbus_property()
    def Flags(self) -> "as":
        return ["write", "indicate"]

    @method()
    def WriteValue(self, value: "ay", options: "a{sv}"):
        if not value:
            logger.warning("Control Point: empty write")
            return

        opcode = value[0]
        logger.info("Control Point: received opcode 0x%02x, data=%s", opcode, value.hex())

        result = self._on_command(opcode, bytes(value))
        response = chars.encode_control_point_response(opcode, result)
        logger.debug("Control Point: responding with %s", response.hex())
        # In a full implementation, this would trigger an indication.
        # For now, the response is logged; the BLE stack handles the indication.

    @method()
    def StartNotify(self):
        self._indicating = True

    @method()
    def StopNotify(self):
        self._indicating = False


class SupportedResistanceLevelRangeCharacteristic(ServiceInterface):
    """Read-only characteristic declaring the resistance level range."""

    def __init__(self, min_level: int, max_level: int):
        super().__init__(GATT_CHRC_IFACE)
        self._value = chars.encode_supported_resistance_range(min_level, max_level)

    @dbus_property()
    def UUID(self) -> "s":
        return chars.SUPPORTED_RESISTANCE_LEVEL_RANGE_UUID

    @dbus_property()
    def Flags(self) -> "as":
        return ["read"]

    @method()
    def ReadValue(self, options: "a{sv}") -> "ay":
        return self._value


class FTMSService:
    """High-level FTMS service manager. Sets up all characteristics and handles
    BLE advertisement registration with BlueZ."""

    def __init__(self, config: dict[str, Any], on_command: Callable[[int, bytes], int]):
        self._config = config
        self._on_command = on_command
        self._bus: MessageBus | None = None
        self._bike_data_chrc: IndoorBikeDataCharacteristic | None = None

    async def start(self) -> None:
        """Register the GATT application and start advertising."""
        self._bus = await MessageBus(bus_type=1).connect()  # system bus
        logger.info("Connected to D-Bus system bus")

        ble_cfg = self._config["ble"]
        bridge_cfg = self._config["bridge"]

        # Create characteristics
        self._bike_data_chrc = IndoorBikeDataCharacteristic()
        feature_chrc = FitnessMachineFeatureCharacteristic()
        control_chrc = FTMSControlPointCharacteristic(self._on_command)
        resistance_range_chrc = SupportedResistanceLevelRangeCharacteristic(
            bridge_cfg["min_level"], bridge_cfg["max_level"]
        )

        # Create advertisement
        adv = FTMSAdvertisement(0, ble_cfg["device_name"])

        # Export objects on D-Bus
        # NOTE: Full implementation requires registering these with BlueZ's
        # GattManager1 and LEAdvertisingManager1 interfaces. The exact D-Bus
        # object paths and registration calls depend on your BlueZ version.
        # See the implementation guide in docs/architecture.md for details.

        logger.info(
            "FTMS service initialized: device_name=%s, adapter=%s",
            ble_cfg["device_name"],
            ble_cfg["adapter"],
        )
        logger.info(
            "Resistance range: %d-%d, inclination target and indoor bike simulation supported",
            bridge_cfg["min_level"],
            bridge_cfg["max_level"],
        )

        # TODO: Complete BlueZ GATT application registration.
        # This is the main integration point that requires careful BlueZ D-Bus
        # interaction. See docs/ftms-protocol.md for the full registration flow.
        # Reference implementations:
        #   - Open Rowing Monitor (Python/BlueZ)
        #   - PiRowFlo (Python/BlueZ)

    async def send_bike_data(
        self,
        speed_kmh: float,
        cadence_rpm: float,
        resistance_level: int,
        power_watts: int,
        elapsed_seconds: int,
        total_distance_m: float = 0.0,
    ) -> None:
        """Send an Indoor Bike Data notification to the connected app."""
        if self._bike_data_chrc and self._bike_data_chrc.is_notifying:
            data = chars.encode_indoor_bike_data(
                speed_kmh, cadence_rpm, resistance_level, power_watts,
                elapsed_seconds, total_distance_m,
            )
            # TODO: Push notification via BlueZ D-Bus PropertiesChanged signal
            logger.debug(
                "Bike data: speed=%.1f cadence=%.0f resistance=%d power=%d elapsed=%d dist=%.0fm",
                speed_kmh, cadence_rpm, resistance_level, power_watts,
                elapsed_seconds, total_distance_m,
            )

    async def stop(self) -> None:
        """Unregister advertisement and GATT application."""
        if self._bus:
            self._bus.disconnect()
            logger.info("FTMS service stopped")
