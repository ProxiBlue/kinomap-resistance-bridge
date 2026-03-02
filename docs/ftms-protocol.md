# FTMS Protocol Reference

This document covers the specific FTMS (Fitness Machine Service) characteristics and behaviors relevant to this project.

## FTMS Overview

FTMS is a Bluetooth SIG standard (assigned number 0x1826) for fitness equipment. It defines how apps communicate with smart bikes, treadmills, rowers, etc.

**Specification**: [Fitness Machine Service (FTMS) v1.0](https://www.bluetooth.com/specifications/specs/fitness-machine-service-1-0/)

## Services and Characteristics We Implement

### Fitness Machine Service (0x1826)

| Characteristic | UUID | Properties | Purpose |
|---|---|---|---|
| Fitness Machine Feature | 0x2ACC | Read | Declares supported features |
| Indoor Bike Data | 0x2AD2 | Notify | Sends telemetry to app |
| Training Status | 0x2AD3 | Read, Notify | Current training state |
| Supported Resistance Level Range | 0x2AD6 | Read | Min/max/step for resistance |
| Fitness Machine Control Point | 0x2AD9 | Write, Indicate | Receives commands from app |
| Fitness Machine Status | 0x2ADA | Notify | Reports state changes |

### Additional Required Services

| Service | UUID | Purpose |
|---|---|---|
| Generic Access | 0x1800 | Device name, appearance |
| Device Information | 0x180A | Manufacturer, model, firmware |

## Fitness Machine Feature (0x2ACC)

This read-only characteristic tells Kinomap what our device supports. It's a pair of 32-bit bitfields.

### Fitness Machine Features (first 4 bytes)
```
Bit  Feature                        We set?
───  ─────────────────────────────  ───────
 0   Average Speed Supported        No
 1   Cadence Supported              Yes
 2   Total Distance Supported       No
 3   Inclination Supported          Yes
 4   Elevation Gain Supported       No
 5   Pace Supported                 No
 6   Step Count Supported           No
 7   Resistance Level Supported     Yes
 8   Stride Count Supported         No
 9   Expended Energy Supported      No
10   Heart Rate Supported           No
11   Metabolic Equivalent Supported No
12   Elapsed Time Supported         Yes
13   Remaining Time Supported       No
14   Power Measurement Supported    Yes
15   Force on Belt Supported        No
16   User Data Retention Supported  No
```

### Target Setting Features (second 4 bytes)
```
Bit  Feature                              We set?
───  ────────────────────────────────────  ───────
 0   Speed Target Supported               No
 1   Inclination Target Supported         Yes  ← KEY
 2   Resistance Target Supported          Yes  ← KEY
 3   Power Target Supported               No
 4   Heart Rate Target Supported          No
 5   Targeted Expended Energy Supported   No
 6   Targeted Steps Supported             No
 7   Targeted Strides Supported           No
 8   Targeted Distance Supported          No
 9   Targeted Training Time Supported     No
10   Targeted Time in 2 HR Zones          No
11   Targeted Time in 3 HR Zones          No
12   Targeted Time in 5 HR Zones          No
13   Indoor Bike Simulation Supported     Yes  ← KEY
14   Wheel Circumference Config           No
15   Spin Down Control Supported          No
16   Targeted Cadence Config Supported    No
```

## Indoor Bike Data (0x2AD2)

Notification characteristic sent at ~1Hz. Variable-length based on which fields are present, controlled by a flags field.

### Flags (first 2 bytes, little-endian)
```
Bit  Field                          Size     We include?
───  ─────────────────────────────  ───────  ───────────
 0   More Data (inverted logic)     -        0 (= speed present)
 1   Average Speed Present          uint16   No
 2   Instantaneous Cadence          uint16   Yes
 3   Average Cadence                uint16   No
 4   Total Distance                 uint24   No
 5   Resistance Level               sint16   Yes
 6   Instantaneous Power            sint16   Yes
 7   Average Power                  sint16   No
 8   Expended Energy                uint16x3 No
 9   Heart Rate                     uint8    No
10   Metabolic Equivalent           uint8    No
11   Elapsed Time                   uint16   Yes
12   Remaining Time                 uint16   No
```

### Data format (with our flags = 0b0000_1000_0110_0100 = 0x0864)
```
Bytes  Field                  Type      Unit          Resolution
─────  ─────────────────────  ────────  ────────────  ──────────
0-1    Flags                  uint16    -             -
2-3    Instantaneous Speed    uint16    km/h          0.01
4-5    Instantaneous Cadence  uint16    rpm           0.5
6-7    Resistance Level       sint16    unitless      1
8-9    Instantaneous Power    sint16    watts         1
10-11  Elapsed Time           uint16    seconds       1
```

## Fitness Machine Control Point (0x2AD9)

This is where Kinomap sends commands. Write + Indicate characteristic.

### Opcodes we handle

| Opcode | Name | Parameters | Our action |
|--------|------|------------|------------|
| 0x00 | Request Control | None | Grant control (respond 0x80, 0x00, 0x01) |
| 0x01 | Reset | None | Reset to initial state |
| 0x03 | Set Target Inclination | sint16 (0.1% resolution) | Map to resistance level |
| 0x04 | Set Target Resistance Level | uint8 (0.1 resolution) | Map to resistance level |
| 0x07 | Start or Resume | None | Begin session |
| 0x08 | Stop or Pause | uint8 (1=stop, 2=pause) | End/pause session |
| 0x11 | Set Indoor Bike Simulation | sint16 wind, sint16 grade, uint8 crr, uint8 cw | Use grade for resistance |

### Response format
Every control point write gets an indication response:
```
Byte 0: 0x80 (Response Code)
Byte 1: Request Opcode (echo back)
Byte 2: Result Code (0x01 = Success, 0x02 = Not Supported, 0x03 = Invalid Parameter)
```

### Set Indoor Bike Simulation (0x11) — Most Important for Kinomap

This is the primary command Kinomap uses for video rides:

```
Byte 0:    0x11 (opcode)
Bytes 1-2: Wind Speed (sint16, 0.001 m/s resolution)
Bytes 3-4: Grade (sint16, 0.01% resolution)  ← THIS IS WHAT WE USE
Byte 5:    Crr (uint8, 0.0001 resolution) — rolling resistance coefficient
Byte 6:    Cw (uint8, 0.01 kg/m resolution) — wind resistance coefficient
```

The **grade** value is the terrain inclination. Example values:
- `-500` = -5.00% (downhill)
- `0` = 0.00% (flat)
- `800` = +8.00% (steep uphill)

## Kinomap-Specific Behavior

Based on community testing:

1. **Kinomap prefers Indoor Bike Simulation (0x11)** over Set Target Inclination (0x03) for video rides
2. **Grade values** typically range from -10% to +15% for cycling videos
3. **Kinomap expects regular telemetry notifications** (~1Hz) or it may disconnect
4. **Control request (0x00)** is always sent first — must be accepted before other commands work
5. **Kinomap scans for FTMS Indoor Bike** — the advertisement must include the correct service UUID and appearance

## BLE Advertisement

For Kinomap to discover the device:

```
Advertisement Type: Connectable, Undirected
Service UUIDs: 0x1826 (Fitness Machine Service)
Local Name: "RPi Resistance Bridge"  (configurable)
Appearance: 0x0481 (Indoor Bike)  — IMPORTANT for Kinomap filtering
Flags: 0x06 (General Discoverable, BR/EDR Not Supported)
```

## Implementation Notes

### BlueZ and D-Bus

On Linux (RPi), BLE GATT servers are created via BlueZ's D-Bus API:

1. Register a GATT application with `org.bluez.GattManager1.RegisterApplication`
2. Register an advertisement with `org.bluez.LEAdvertisingManager1.RegisterAdvertisement`
3. Implement characteristic read/write/notify callbacks as D-Bus objects

The `dbus-next` library provides async Python bindings for this.

### Byte order

All multi-byte FTMS values are **little-endian** as per Bluetooth specification.

### Signed integers

Inclination and grade values are signed (sint16). In Python:
```python
import struct
grade_raw = struct.unpack('<h', data[3:5])[0]  # signed int16, little-endian
grade_percent = grade_raw * 0.01
```
