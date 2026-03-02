# Hardware: 3D Printed Case & Mounting

## Case Design

The OpenSCAD file `case.scad` generates a snap-fit case that holds:
- Raspberry Pi (3B+/4 or Zero 2W — configurable)
- 2-channel relay module

Both components mount on M2.5 standoffs inside the case.

### Features
- Snap-fit lid (no screws needed for the case itself)
- Ventilation slots on both sides
- 3 cable exit holes: USB power (left), bike button wires (back), speed sensor (back)
- No supports needed for printing
- Parametric — adjust wall thickness, standoff height, tolerances etc. in the config section

### How to Use

1. **Install OpenSCAD**: https://openscad.org/ (free)
2. **Open** `case.scad`
3. **Configure**:
   - Set `rpi_model` to `"3"` (RPi 3B+/4) or `"zero"` (RPi Zero 2W)
   - Set `part` to `"base"`, `"lid"`, or `"both"` (exploded preview)
4. **Render** (F6) and **Export STL** (F7)
5. **Print** base and lid as separate STL exports

### Print Settings

| Setting | Value |
|---------|-------|
| Layer height | 0.2mm |
| Infill | 15-20% |
| Supports | None needed |
| Material | PLA or PETG |
| Orientation | Flat (open side up for base, flat side down for lid) |

### Approximate Dimensions

| RPi Model | Case size (W x D x H) |
|-----------|----------------------|
| RPi 3B+/4 | ~150 x 64 x 34 mm |
| RPi Zero 2W | ~130 x 46 x 34 mm |

## Component Mounting Dimensions

Reference for designing your own case or modifying the OpenSCAD file.

### Raspberry Pi 3B+/4

```
PCB: 85 x 56 mm
Mounting holes: M2.5, 4 corners

    3.5mm    58mm
    ├──┤├───────────┤
    ●───────────────● ─┬─ 3.5mm
    │               │  │
    │   Raspberry   │  49mm
    │     Pi 3/4    │  │
    │               │  │
    ●───────────────● ─┴─ 3.5mm

    Hole positions from bottom-left:
    (3.5, 3.5)  (61.5, 3.5)
    (3.5, 52.5) (61.5, 52.5)
```

### Raspberry Pi Zero 2W

```
PCB: 65 x 30 mm
Mounting holes: M2.5, 4 corners

    3.5mm    58mm
    ├──┤├───────────┤
    ●───────────────● ─┬─ 3.5mm
    │  RPi Zero 2W  │  23mm
    ●───────────────● ─┴─ 3.5mm

    Hole positions from bottom-left:
    (3.5, 3.5)  (61.5, 3.5)
    (3.5, 26.5) (61.5, 26.5)
```

### 2-Channel Relay Module (typical)

```
PCB: ~50 x 38 mm
Mounting holes: M3, 4 corners (varies by manufacturer — measure yours!)

    3.5mm   43mm
    ├──┤├─────────┤
    ●─────────────● ─┬─ 3.5mm
    │             │  │
    │   [Relay1]  │  31mm
    │   [Relay2]  │  │
    │             │  │
    ●─────────────● ─┴─ 3.5mm

    Screw terminals along one long edge
    Signal pins (IN1, IN2, VCC, GND) along the other
```

> **Note**: Relay module dimensions vary by manufacturer. Measure your actual module and update the `relay_pcb` and `relay_holes` values in `case.scad` if needed.

### A3144 Hall Effect Sensor

The sensor is tiny (4 x 3 x 1.5mm) and mounts on the bike frame near the flywheel, not inside the case. Route its 3 wires through the back cable hole into the case.

## Assembly Inside the Case

```
Top-down view (lid removed):

┌─────────────────────────────────────────────────┐
│                                                 │
│  ┌──────────────────┐    ┌───────────────┐      │
│  │                  │    │ ○ Relay 1     │ ←cables
│  │   Raspberry Pi   │    │ ○ Relay 2     │  out
│  │                  │    │               │      │
│  │              USB→│    │  IN1 IN2 V G  │      │
│  └──────────────────┘    └───────────────┘      │
│  ↑                                              │
│  USB power in                                   │
└─────────────────────────────────────────────────┘

Dupont wires connect RPi GPIO header to relay module pins.
No breadboard needed — wires route directly between the two boards.
```

## Speed Sensor Mounting

The A3144 and magnet mount on the **bike itself**, not in the case:

- **Magnet**: Any magnet, attached to the flywheel rim with hot glue, tape, or epoxy
- **Sensor**: Mount on the bike frame 2-8mm from the magnet path. Hot glue, cable tie, or a small 3D printed bracket

### Optional: Sensor Bracket

A simple bracket can be printed to hold the A3144 at the right distance from the flywheel. The design depends on your bike's frame shape — a small L-bracket with a slot for adjusting the gap distance works well. If you want, you can add a parametric bracket to this folder.

## Bill of Fasteners

| Fastener | Qty | Purpose |
|----------|-----|---------|
| M2.5 x 6mm screw | 4 | Mount RPi to standoffs |
| M2.5 x 6mm screw | 4 | Mount relay module to standoffs (or M3 depending on your module) |
| M2.5 nut (optional) | 4 | If standoffs aren't self-tapping |

If you prefer not to use screws, friction fit with slightly taller standoffs (add 1mm) works for a case that won't be moved often.
