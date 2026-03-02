"""Tests for FTMS characteristic encoding/decoding."""

import struct
import pytest

from src.ftms.characteristics import (
    decode_indoor_bike_simulation,
    decode_set_target_inclination,
    decode_set_target_resistance,
    encode_control_point_response,
    encode_fitness_machine_features,
    encode_indoor_bike_data,
    encode_supported_resistance_range,
    OP_RESPONSE_CODE,
    OP_SET_TARGET_INCLINATION,
    RESULT_SUCCESS,
)


class TestEncodeFeatures:
    def test_feature_bytes_length(self):
        result = encode_fitness_machine_features()
        assert len(result) == 8

    def test_inclination_supported(self):
        result = encode_fitness_machine_features()
        machine_features = struct.unpack("<I", result[:4])[0]
        assert machine_features & (1 << 3)  # Inclination Supported

    def test_resistance_level_supported(self):
        result = encode_fitness_machine_features()
        machine_features = struct.unpack("<I", result[:4])[0]
        assert machine_features & (1 << 7)  # Resistance Level Supported

    def test_indoor_bike_simulation_target(self):
        result = encode_fitness_machine_features()
        target_features = struct.unpack("<I", result[4:])[0]
        assert target_features & (1 << 13)  # Indoor Bike Simulation Supported


class TestEncodeResistanceRange:
    def test_range_1_to_16(self):
        result = encode_supported_resistance_range(1, 16)
        min_val, max_val, step = struct.unpack("<hhH", result)
        assert min_val == 10   # 1 * 10
        assert max_val == 160  # 16 * 10
        assert step == 10      # 1 * 10


class TestEncodeIndoorBikeData:
    def test_data_length(self):
        result = encode_indoor_bike_data(20.0, 70.0, 5, 100, 60, 1500.0)
        # 2 flags + 2 speed + 2 cadence + 3 distance + 2 resistance + 2 power + 2 elapsed = 15
        assert len(result) == 15

    def test_speed_encoding(self):
        result = encode_indoor_bike_data(25.5, 70.0, 5, 100, 0)
        # Speed is at bytes 2-3, uint16, resolution 0.01 km/h
        speed_raw = struct.unpack("<H", result[2:4])[0]
        assert speed_raw == 2550  # 25.5 * 100

    def test_cadence_encoding(self):
        result = encode_indoor_bike_data(20.0, 80.0, 5, 100, 0)
        # Cadence is at bytes 4-5, uint16, resolution 0.5 rpm
        cadence_raw = struct.unpack("<H", result[4:6])[0]
        assert cadence_raw == 160  # 80.0 * 2

    def test_distance_encoding(self):
        result = encode_indoor_bike_data(20.0, 70.0, 5, 100, 0, total_distance_m=1234.0)
        # Distance is uint24 at bytes 6-8
        dist_raw = struct.unpack("<I", result[6:9] + b'\x00')[0]
        assert dist_raw == 1234


class TestDecodeInclination:
    def test_positive_grade(self):
        # Opcode + sint16 (5.0% = 50 at 0.1 resolution)
        data = bytes([0x03]) + struct.pack("<h", 50)
        assert decode_set_target_inclination(data) == pytest.approx(5.0)

    def test_negative_grade(self):
        data = bytes([0x03]) + struct.pack("<h", -30)
        assert decode_set_target_inclination(data) == pytest.approx(-3.0)

    def test_zero_grade(self):
        data = bytes([0x03]) + struct.pack("<h", 0)
        assert decode_set_target_inclination(data) == pytest.approx(0.0)


class TestDecodeResistance:
    def test_mid_range(self):
        # Opcode + uint8 (50% = 500 at 0.1 resolution... but spec says uint8 * 0.1)
        data = bytes([0x04, 100])  # 100 * 0.1 = 10.0
        assert decode_set_target_resistance(data) == pytest.approx(10.0)


class TestDecodeSimulation:
    def test_grade_extraction(self):
        # Opcode 0x11 + wind(sint16) + grade(sint16) + crr(uint8) + cw(uint8)
        wind = struct.pack("<h", 0)       # 0 m/s
        grade = struct.pack("<h", 800)    # 8.00%
        data = bytes([0x11]) + wind + grade + bytes([33, 51])  # crr=0.0033, cw=0.51

        result = decode_indoor_bike_simulation(data)
        assert result["grade_percent"] == pytest.approx(8.0)
        assert result["wind_speed_ms"] == pytest.approx(0.0)
        assert result["crr"] == pytest.approx(0.0033)
        assert result["cw"] == pytest.approx(0.51)


class TestControlPointResponse:
    def test_success_response(self):
        result = encode_control_point_response(OP_SET_TARGET_INCLINATION, RESULT_SUCCESS)
        assert result == bytes([OP_RESPONSE_CODE, OP_SET_TARGET_INCLINATION, RESULT_SUCCESS])
