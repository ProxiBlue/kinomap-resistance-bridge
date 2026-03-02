"""FTMS characteristic UUID constants and data encoding helpers."""

import struct

# Bluetooth SIG assigned UUIDs
FTMS_SERVICE_UUID = "00001826-0000-1000-8000-00805f9b34fb"
FITNESS_MACHINE_FEATURE_UUID = "00002acc-0000-1000-8000-00805f9b34fb"
INDOOR_BIKE_DATA_UUID = "00002ad2-0000-1000-8000-00805f9b34fb"
TRAINING_STATUS_UUID = "00002ad3-0000-1000-8000-00805f9b34fb"
SUPPORTED_RESISTANCE_LEVEL_RANGE_UUID = "00002ad6-0000-1000-8000-00805f9b34fb"
FTMS_CONTROL_POINT_UUID = "00002ad9-0000-1000-8000-00805f9b34fb"
FITNESS_MACHINE_STATUS_UUID = "00002ada-0000-1000-8000-00805f9b34fb"

# Control Point opcodes
OP_REQUEST_CONTROL = 0x00
OP_RESET = 0x01
OP_SET_TARGET_INCLINATION = 0x03
OP_SET_TARGET_RESISTANCE = 0x04
OP_START_RESUME = 0x07
OP_STOP_PAUSE = 0x08
OP_SET_INDOOR_BIKE_SIMULATION = 0x11
OP_RESPONSE_CODE = 0x80

# Result codes
RESULT_SUCCESS = 0x01
RESULT_NOT_SUPPORTED = 0x02
RESULT_INVALID_PARAMETER = 0x03
RESULT_OPERATION_FAILED = 0x04
RESULT_CONTROL_NOT_PERMITTED = 0x05


def encode_fitness_machine_features() -> bytes:
    """Encode the Fitness Machine Feature characteristic value.

    Returns 8 bytes: 4 bytes machine features + 4 bytes target setting features.
    """
    # Machine features: cadence, total distance, inclination, resistance level, elapsed time, power
    machine_features = (
        (1 << 1)   # Cadence Supported
        | (1 << 2)  # Total Distance Supported
        | (1 << 3)  # Inclination Supported
        | (1 << 7)  # Resistance Level Supported
        | (1 << 12) # Elapsed Time Supported
        | (1 << 14) # Power Measurement Supported
    )

    # Target setting features: inclination target, resistance target, indoor bike sim
    target_features = (
        (1 << 1)    # Inclination Target Supported
        | (1 << 2)  # Resistance Target Supported
        | (1 << 13) # Indoor Bike Simulation Supported
    )

    return struct.pack("<II", machine_features, target_features)


def encode_supported_resistance_range(min_level: int, max_level: int, step: int = 1) -> bytes:
    """Encode the Supported Resistance Level Range characteristic."""
    # sint16 minimum, sint16 maximum, uint16 increment (resolution 0.1)
    return struct.pack("<hhH", min_level * 10, max_level * 10, step * 10)


def encode_indoor_bike_data(
    speed_kmh: float,
    cadence_rpm: float,
    resistance_level: int,
    power_watts: int,
    elapsed_seconds: int,
    total_distance_m: float = 0.0,
) -> bytes:
    """Encode the Indoor Bike Data notification value.

    Flags layout (uint16):
      Bit 0 = 0: Instantaneous Speed present (inverted logic)
      Bit 2 = 1: Instantaneous Cadence present
      Bit 4 = 1: Total Distance present
      Bit 5 = 1: Resistance Level present
      Bit 6 = 1: Instantaneous Power present
      Bit 11 = 1: Elapsed Time present
    """
    flags = (1 << 2) | (1 << 4) | (1 << 5) | (1 << 6) | (1 << 11)

    # Total Distance is uint24 (3 bytes, little-endian) in meters
    dist_int = min(int(total_distance_m), 0xFFFFFF)
    dist_bytes = struct.pack("<I", dist_int)[:3]  # Take lower 3 bytes

    # Pack fixed-size fields, then insert the 3-byte distance
    return struct.pack(
        "<HHH",
        flags,
        int(speed_kmh * 100),        # uint16, 0.01 km/h resolution
        int(cadence_rpm * 2),         # uint16, 0.5 rpm resolution
    ) + dist_bytes + struct.pack(
        "<hhH",
        resistance_level,              # sint16, unitless
        power_watts,                   # sint16, watts
        elapsed_seconds,               # uint16, seconds
    )


def encode_control_point_response(request_opcode: int, result: int) -> bytes:
    """Encode a Control Point response indication."""
    return struct.pack("BBB", OP_RESPONSE_CODE, request_opcode, result)


def decode_set_target_inclination(data: bytes) -> float:
    """Decode Set Target Inclination parameter. Returns grade in percent."""
    raw = struct.unpack("<h", data[1:3])[0]
    return raw * 0.1


def decode_set_target_resistance(data: bytes) -> float:
    """Decode Set Target Resistance Level parameter. Returns 0-100 scale."""
    raw = data[1]
    return raw * 0.1


def decode_indoor_bike_simulation(data: bytes) -> dict:
    """Decode Set Indoor Bike Simulation parameters."""
    wind_speed_raw = struct.unpack("<h", data[1:3])[0]
    grade_raw = struct.unpack("<h", data[3:5])[0]
    crr = data[5] if len(data) > 5 else 0
    cw = data[6] if len(data) > 6 else 0

    return {
        "wind_speed_ms": wind_speed_raw * 0.001,
        "grade_percent": grade_raw * 0.01,
        "crr": crr * 0.0001,
        "cw": cw * 0.01,
    }
