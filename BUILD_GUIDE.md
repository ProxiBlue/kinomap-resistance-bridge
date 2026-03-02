# Build Guide: RPi to Bike Button Circuit

## Parts List

| Part | Qty | What to search for | ~AUD |
|------|-----|-------------------|------|
| **Raspberry Pi 3B+/4/Zero 2W** | 1 | Whichever you already have | $0-70 |
| **2-channel relay module (5V, opto-isolated)** | 1 | "2 channel relay module 5v opto" on eBay/Jaycar | $5-12 |
| **A3144 Hall effect sensor** | 1 | "A3144 hall effect sensor" (pack of 5 for $3) | $2-3 |
| **10kΩ resistor** | 1 | "10k ohm resistor 1/4W" | $0.10 |
| **Small magnet** | 1 | Any magnet that fits on the flywheel rim (fridge magnet, neodymium, whatever you have) | $0-2 |
| **Dupont jumper wires (F-F)** | 8 | "dupont jumper wire female female" | $3 |
| **2-core hookup wire** | ~1.5m | Thin gauge (22-26 AWG), for relay→buttons + sensor | $2 |
| **Soldering iron + solder** | - | You have these already | - |
| **Hot glue gun** | - | For mounting magnet and sensor | on hand |

That's it for the full build (relays + speed sensor). **~7 parts** beyond the RPi itself.

## Do I Need a Breadboard or PCB?

**No.** The relay module is already a self-contained PCB with screw terminals and pin headers. The RPi has a GPIO header. You're just running wires between them — dupont jumpers on the RPi side, screw terminals on the relay side, solder joints on the bike side. The speed sensor's pull-up resistor can be soldered inline on the wire itself (or skipped entirely using the RPi's internal pull-up).

There's nothing that needs a breadboard or custom PCB. Everything connects directly.

For a clean permanent build, a **screw terminal GPIO breakout hat** (~$3-5, "raspberry pi gpio screw terminal") is nice — lets you screw wires down instead of relying on push-fit dupont connectors. But it's optional.

## 3D Printed Case

A parametric OpenSCAD case design is included in `hardware/case.scad`. It holds the RPi and relay module side by side with standoffs, snap-fit lid, ventilation slots, and cable exit holes. See [hardware/README.md](hardware/README.md) for print settings and dimensions.

## The Circuit

There are only 5 connections from RPi to relay module, and 4 wires from relay to bike:

```
Raspberry Pi                    2-Channel Relay Module
─────────────                   ──────────────────────
Pin 2  (5V)  ───────────────►  VCC
Pin 6  (GND) ───────────────►  GND
Pin 11 (GPIO 17) ───────────►  IN1  (controls Relay 1 = UP)
Pin 13 (GPIO 27) ───────────►  IN2  (controls Relay 2 = DOWN)

                              Relay 1               Relay 2
                              COM   N.O.            COM   N.O.
                               │     │               │     │
                               │     │               │     │
                               ▼     ▼               ▼     ▼
                            Bike + button         Bike - button
                            pad A  pad B          pad A  pad B
```

## Step by Step

### 1. RPi → Relay Module

5 female-to-female dupont wires, no soldering needed:

| RPi Physical Pin | Wire to relay | Purpose |
|---|---|---|
| Pin 2 (top right) | VCC | Powers the relay coils |
| Pin 6 (3rd left) | GND | Common ground |
| Pin 11 (6th left) | IN1 | Triggers "resistance up" relay |
| Pin 13 (7th left) | IN2 | Triggers "resistance down" relay |

### RPi GPIO Header Reference

```
             3.3V [1 ] [2 ] 5V ◄── to relay VCC
          GPIO  2 [3 ] [4 ] 5V
          GPIO  3 [5 ] [6 ] GND ◄── to relay GND
          GPIO  4 [7 ] [8 ] GPIO 14
              GND [9 ] [10] GPIO 15
 UP relay ►  GPIO 17 [11] [12] GPIO 18
 DN relay ►  GPIO 27 [13] [14] GND
          GPIO 22 [15] [16] GPIO 23
             3.3V [17] [18] GPIO 24
          GPIO 10 [19] [20] GND
          GPIO  9 [21] [22] GPIO 25
          GPIO 11 [23] [24] GPIO  8
              GND [25] [26] GPIO  7
```

### 2. Relay Module → Bike Buttons

Each relay has 3 screw terminals. You only use 2 of them:

```
         ┌─────────┐
   COM ──┤  Relay  ├── N.O. (Normally Open)  ← USE THESE TWO
         │         │
   N.C.──┤         │   (Normally Closed)     ← IGNORE THIS ONE
         └─────────┘
```

- **COM** (Common): always connected to one side
- **N.O.** (Normally Open): disconnected when relay is off, shorts to COM when relay activates
- **N.C.** (Normally Closed): ignore, don't use

For each button (UP and DOWN):

1. Solder a wire to **pad A** of the button on the bike's PCB → screw into relay **COM** terminal
2. Solder a wire to **pad B** of the button on the bike's PCB → screw into relay **N.O.** terminal

```
Bike Button PCB (zoomed in)
┌─────────────────────────────┐
│                             │
│   Pad A ─── [Button] ─── Pad B     ← original button (keep as-is)
│     │                       │
│     │    ┌── COM            │
│     └────┤  Relay           │
│          └── N.O. ──────────┘       ← your added wires (in parallel)
│                             │
└─────────────────────────────┘
```

When the RPi activates the relay, COM and N.O. short together — electrically identical to pressing the button. The original button still works because the relay is wired **in parallel**.

### 3. That's the Whole Circuit

```
┌──────────┐    dupont     ┌──────────────┐   solder    ┌──────────────┐
│          │    wires      │              │   + wire     │              │
│   RPi    ├──────────────►│ Relay Module ├────────────►│  Bike PCB    │
│          │  (push-on)    │              │ (screw term) │  +/- buttons │
└──────────┘               └──────────────┘             └──────────────┘
      no soldering              no soldering              soldering here
```

## Before You Wire the Bike Side

You need to investigate the button circuit with a multimeter first.

### Quick Check (5 minutes)

1. Open the bike console (screws on the back)
2. Find the +/- resistance buttons on the PCB
3. Set multimeter to **continuity mode** (beep mode)
4. Touch probes to the two pads/contacts on one button
5. **Press the button** — should beep (confirms it's a simple switch)
6. **Release** — should stop beeping
7. Repeat for the other button
8. Note which two pads correspond to each button

If both buttons beep on press → you're good, the relay will work.

### Where to Find the Solder Points

If the buttons are **on the main PCB**: solder directly to the button pads (the two traces on either side of the button component).

If the buttons are on a **separate panel connected by ribbon cable**: the easiest solder points are where the ribbon cable meets the main board. Each button will correspond to two pins on the connector.

### What to Document

Take a photo and note:
- Which pads are for the + (up) button
- Which pads are for the - (down) button
- The voltage across the pads (multimeter on DC 20V range, bike powered on)

See [docs/hardware-investigation.md](docs/hardware-investigation.md) for the full investigation checklist.

## Why This Is Safe

- The relay provides **galvanic isolation** — the RPi circuit and bike circuit are electrically separate
- The opto-isolated relay module adds a second isolation layer on the input side
- You're wiring in **parallel** with the existing buttons — worst case the relay doesn't work and the buttons still function normally
- The relay contacts are passive (just a switch), so polarity doesn't matter
- The bike's button circuit is low-voltage/low-current — no shock hazard

## Optional Upgrade: Optocouplers Instead of Relays

If you find the bike buttons operate at low voltage (3.3V) and very low current (< 1mA), you can skip the relay module entirely and use **PC817 optocouplers** (~$1 for a pack of 10):

```
RPi GPIO 17 ──[330Ω]──┐
                       │ LED anode
                  ┌────┴────┐
                  │  PC817  │
                  │  opto-  │       ┌── Bike pad A
                  │  coupler├───────┤
                  └────┬────┘       └── Bike pad B
                       │ LED cathode
RPi GND ───────────────┘
```

Advantages over relay: smaller, silent (no click), faster switching, no mechanical wear. But the relay module is simpler to start with, works regardless of button voltage, and requires zero soldering on the RPi side.

---

## Speed Sensor: Real Speed & Cadence for Kinomap

Without a speed sensor, the bridge sends simulated/fake speed data to Kinomap. Adding a sensor gives you real speed, real cadence, better power estimates, and accurate distance tracking.

### Extra Parts

| Part | Qty | What to search for | ~AUD |
|------|-----|-------------------|------|
| **A3144 Hall effect sensor** | 1 | "A3144 hall effect sensor" (often sold in packs of 5-10) | $2-3 |
| **10kΩ resistor** | 1 | "10k ohm resistor" (1/4W, any tolerance) | $0.10 |
| **Small magnet** | 1 | Any magnet — fridge magnet, neodymium, whatever you have lying around | $0-2 |
| **Hot glue or tape** | - | To attach magnet to flywheel | on hand |
| **Heat shrink tubing** (optional) | - | To insulate solder joints | $2 |

Total extra cost: **~$5-7**

### Two Options

**Option 1 — Tap the bike's existing sensor** (recommended if your bike has a digital display showing RPM/distance). No magnet or sensor to buy/mount. See [docs/tapping-existing-sensors.md](docs/tapping-existing-sensors.md) for a step-by-step guide to find and identify the sensor.

**Option 2 — Add your own Hall sensor + magnet** (if no existing sensor, or if you can't access it). Detailed below.

### How It Works (Option 2: Add Your Own)

```
Flywheel spins
    │
    │  Magnet passes sensor once per revolution
    ▼
┌──────────┐
│  Magnet  │ ← glued to flywheel rim
│  (on     │
│ flywheel)│
└────┬─────┘
     │ magnetic field
     ▼
┌──────────┐        ┌──────────┐
│  A3144   │        │          │
│  Hall    ├────────┤  RPi     │
│  Sensor  │ GPIO22 │  GPIO    │
└──────────┘        └──────────┘
                    Counts pulses → calculates RPM → speed in km/h
```

Each time the magnet passes the sensor = 1 flywheel revolution. The RPi counts the time between pulses to calculate RPM, then converts to speed using the flywheel circumference.

### A3144 Hall Effect Sensor Pinout

The A3144 has 3 pins. Looking at the **flat face** with the **leads pointing down**:

```
    ┌─────────┐
    │  A3144  │  ← flat face (printed side)
    │         │
    └─┬──┬──┬┘
      │  │  │
      1  2  3

  1 = VCC (3.3V)
  2 = GND
  3 = Signal (OUTPUT) → to RPi GPIO
```

### Wiring: Sensor → RPi

Only 3 wires + 1 resistor:

```
RPi 3.3V (Pin 1) ──────────────── A3144 Pin 1 (VCC)
                                       │
                                   ┌───┘
                                   │
                                [10kΩ]  ← pull-up resistor
                                   │
RPi GPIO 22 (Pin 15) ─────────────┤
                                   │
                              A3144 Pin 3 (Signal)

RPi GND (Pin 9) ───────────────── A3144 Pin 2 (GND)
```

The 10kΩ pull-up resistor connects between VCC (3.3V) and the signal pin. This ensures a clean HIGH signal when no magnet is present, and the A3144 pulls it LOW when the magnet passes.

> **Note**: If using the RPi's internal pull-up (enabled by default in config), you can skip the physical 10kΩ resistor. The internal pull-up works fine for short wire runs (< 50cm). For longer wires, use the physical resistor.

### Updated GPIO Header (with speed sensor)

```
   3.3V ◄── sensor VCC [1 ] [2 ] 5V ◄── relay VCC
                        [3 ] [4 ] 5V
                        [5 ] [6 ] GND ◄── relay GND
                        [7 ] [8 ]
   sensor GND ────────► [9 ] [10]
   UP relay ──────────► GPIO 17 [11] [12]
   DN relay ──────────► GPIO 27 [13] [14] GND
   speed sensor ──────► GPIO 22 [15] [16]
                        [17] [18]
                        ...
```

### Mounting the Magnet

1. **Find the flywheel** — on a recumbent bike it's usually near the front, covered by a plastic shroud. You may need to remove a panel.

2. **Glue the magnet** to the outer rim of the flywheel. Use hot glue or epoxy.
   - Position it near the edge for maximum radius (stronger signal)
   - Make sure it doesn't hit anything as the flywheel spins
   - The magnet should pass within **5-10mm** of where you'll mount the sensor

3. **Mount the sensor** on the frame, positioned so the flat face points at the magnet's path.
   - Use hot glue, cable ties, or a small bracket
   - Gap between sensor and magnet: **2-8mm** (closer = more reliable)
   - The sensor must be stationary; only the magnet moves

```
Side view:

  Flywheel rim ──────────────►  direction of rotation
  ┌───────────────────────────────────────┐
  │                                       │
  │    ┌────────┐                         │
  │    │ Magnet │ (glued to rim)          │
  │    └────────┘                         │
  │         ↕ 2-8mm gap                   │
  │    ┌────────┐                         │
  │    │ A3144  │ (mounted to frame)      │
  │    └───┬────┘                         │
  │        │ wires to RPi                 │
  └────────┼──────────────────────────────┘
           ▼
```

### Tapping the Bike's Existing Sensor (Alternative)

Your Drax already has a speed sensor for its built-in display. If you can find it, you can tap into its signal instead of adding your own magnet:

1. **Find it**: Look for a small component near the flywheel with 2 wires (reed switch) or 3 wires (Hall sensor) going back to the console PCB.

2. **If it's a reed switch** (2 wires): Wire one side to RPi GPIO 22 and the other to RPi GND. Enable `pull_up: true` in config.

3. **If it's a Hall sensor** (3 wires): Identify VCC, GND, Signal. Tap the signal wire to RPi GPIO 22 (don't disconnect it from the bike's own circuit — just add a wire in parallel).

> **Caution**: If the bike's sensor runs at 5V, add a voltage divider (two resistors) or a level shifter to bring the signal down to 3.3V for the RPi GPIO.

### Calibration

You need two values in `config/local.yaml`:

**flywheel_circumference_m**: Measure the flywheel diameter and multiply by pi (3.14159).
  - Example: 20cm diameter flywheel → 0.20 * 3.14159 = 0.628m

**gear_ratio**: How many flywheel revolutions per one pedal revolution.
  - Mark the flywheel with tape
  - Turn the pedals exactly 1 full revolution
  - Count flywheel revolutions (typically 3-8 for exercise bikes)
  - Example: 5 flywheel revs per pedal rev → `gear_ratio: 5.0`

```yaml
# config/local.yaml
speed_sensor:
  enabled: true
  flywheel_circumference_m: 0.628   # Your measured value
  gear_ratio: 5.0                    # Your counted value
```

### Testing the Sensor

```bash
# Quick test — spin the flywheel by hand and watch for pulses
python scripts/test_speed_sensor.py

# Should show RPM and speed updating as you spin
```

## Sourcing in Australia

- **Jaycar**: Relay modules (Cat# XC4419 or similar), dupont wires, hookup wire — walk-in stores nationwide
- **Core Electronics** (coreelectronics.com.au): RPi, relay modules, everything — fast AU shipping
- **Altronics**: Similar range to Jaycar
- **eBay AU**: Cheapest for relay modules and dupont wires, 1-2 week delivery
- **AliExpress**: Cheapest overall but 2-4 week shipping
