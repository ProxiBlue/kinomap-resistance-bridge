# Relay Circuit Schematics

## Basic Setup: RPi → Relay Module → Bike Buttons

### Component Overview

```
Raspberry Pi                   Relay Module (opto-isolated)
┌────────────┐                 ┌─────────────────────────────────┐
│            │                 │  VCC ── 5V power                │
│  GPIO 17 ──┼── IN1 ─────────┤  IN1    Relay 1 (Resistance UP) │
│  GPIO 27 ──┼── IN2 ─────────┤  IN2    Relay 2 (Resistance DN) │
│            │                 │  GND ── Ground                  │
│  5V (pin 2)┼── VCC ─────────┤                                 │
│  GND (pin 6)┼── GND ────────┤  Jumper: VCC-JD connected       │
└────────────┘                 └──────┬─────┬──────┬─────┬───────┘
                                      │     │      │     │
                                 Relay 1          Relay 2
                                 COM   N.O.       COM   N.O.
                                  │     │          │     │
                                  ▼     ▼          ▼     ▼
                               Bike + Button    Bike - Button
                               pad A  pad B     pad A  pad B
```

## GPIO Pin Mapping (Default)

| RPi GPIO | Physical Pin | Relay Channel | Function |
|----------|-------------|---------------|----------|
| GPIO 17  | Pin 11      | IN1           | Resistance UP (+) |
| GPIO 27  | Pin 13      | IN2           | Resistance DOWN (-) |
| GPIO 22  | Pin 15      | -             | Speed sensor signal (INPUT) |
| 5V       | Pin 2       | VCC           | Relay module power |
| 3.3V     | Pin 1       | -             | Speed sensor power |
| GND      | Pin 6       | GND           | Common ground (relay) |
| GND      | Pin 9       | -             | Common ground (speed sensor) |

### RPi GPIO Header Reference (relevant pins)

```
  Sensor VCC ──► 3.3V [1 ] [2 ] 5V ◄── Relay VCC
                      [3 ] [4 ] 5V
                      [5 ] [6 ] GND ◄── Relay GND
                      [7 ] [8 ]
  Sensor GND ──►  GND [9 ] [10]
  GPIO17/UP  ────────► [11] [12]
  GPIO27/DN  ────────► [13] [14] GND
  GPIO22/SPEED ──────► [15] [16]
                 3.3V [17] [18]
                      [19] [20] GND
                      [21] [22]
                      [23] [24]
                  GND [25] [26]
```

## Relay Module Wiring Detail

### Understanding the relay contacts

Each relay has three terminals:

```
         ┌─────┐
   COM ──┤     ├── N.O. (Normally Open)
         │Relay│
   N.C.──┤     │
         └─────┘
```

- **COM** (Common): Always connected to one side
- **N.O.** (Normally Open): Disconnected when relay is off, connected to COM when relay is on
- **N.C.** (Normally Closed): Connected to COM when relay is off, disconnected when on

**We use COM and N.O.** — the circuit is open (button not pressed) when relay is off, and closed (button pressed) when relay is on.

### Wiring to bike button

```
Bike Button PCB
                    ┌───────────────────┐
                    │   ┌─Button──┐     │
  Pad A ──────────────┤          ├──────────── Pad B
                    │   └────────┘     │
                    │                   │
                    │   Wire from relay │
                    │   ┌─ COM         │
  Pad A ──────────────┤              ├──────── Pad B
                    │   └─ N.O.        │
                    │                   │
                    └───────────────────┘

Result: Button OR relay can close the circuit
```

**Important**: Wire in PARALLEL with the existing button, not in series. The original button should still work normally.

## Enhanced Setup: With Optocoupler Isolation

If you want extra isolation (recommended for bikes with higher voltage circuits):

```
RPi GPIO 17 ───[330Ω]───┐
                          │ Anode
                     ┌────┴────┐
                     │ PC817   │
                     │ Opto-   │
                     │ coupler │
                     └────┬────┘
                          │ Cathode
RPi GND ─────────────────┘

                     ┌────┴────┐
                     │ PC817   │
                     │ Output  │──── Bike Pad A
                     │ side    │
                     └────┬────┘
                          │
                          └──── Bike Pad B
```

This removes the need for a relay module entirely if the button circuit is low-current (< 50mA). The optocoupler provides complete galvanic isolation.

### Optocoupler Component Values

| Component | Value | Purpose |
|-----------|-------|---------|
| R1 (LED side) | 330Ω | Limits current through opto LED (~10mA at 3.3V) |
| PC817 | - | Standard optocoupler, CTR > 50% |

## Speed Sensor (Hall Effect A3144)

### Wiring

```
RPi 3.3V (Pin 1) ──────────────── A3144 Pin 1 (VCC)
                                       │
                                   ┌───┘
                                   │
                                [10kΩ]  ← pull-up resistor (optional if using
                                   │      RPi internal pull-up for short wires)
                                   │
RPi GPIO 22 (Pin 15) ─────────────┤
                                   │
                              A3144 Pin 3 (Signal)

RPi GND (Pin 9) ───────────────── A3144 Pin 2 (GND)
```

### A3144 Pinout (flat face toward you, leads down)

```
    ┌─────────┐
    │  A3144  │  ← flat face (printed side)
    │         │
    └─┬──┬──┬┘
      │  │  │
      1  2  3

  1 = VCC (3.3V from RPi Pin 1)
  2 = GND (RPi Pin 9)
  3 = Signal → RPi GPIO 22 (Pin 15)
```

### Mounting

- Attach any small magnet to the outer rim of the flywheel (glue, tape, whatever holds)
- Mount the A3144 on the bike frame, flat face pointing at the magnet path
- Gap between sensor and magnet: 2-8mm
- The magnet should pass the sensor once per flywheel revolution

```
  Flywheel rim ──────────────►  direction of rotation
  ┌───────────────────────────────────────┐
  │    ┌────────┐                         │
  │    │ Magnet │ (glued to rim)          │
  │    └────────┘                         │
  │         ↕ 2-8mm gap                   │
  │    ┌────────┐                         │
  │    │ A3144  │ (mounted to frame)      │
  │    └───┬────┘                         │
  │        │ 3 wires to RPi               │
  └────────┼──────────────────────────────┘
           ▼
```

### Tapping Existing Bike Sensor (Alternative)

If your bike already has a speed sensor (reed switch or Hall sensor near the flywheel):

- **Reed switch (2 wires)**: Wire one side to GPIO 22, other to GND. Enable `pull_up: true`.
- **Hall sensor (3 wires)**: Tap the signal wire to GPIO 22 in parallel (don't disconnect from bike's circuit).
- **Caution**: If the bike sensor runs at 5V, use a voltage divider (10kΩ + 20kΩ) to bring the signal to 3.3V-safe levels.

## Power Considerations

### Relay module power
- Most 2-channel relay modules draw 70-100mA total
- RPi 5V pin can supply up to ~300mA safely
- If using more relays, consider a separate 5V power supply

### Speed sensor power
- A3144 draws < 10mA at 3.3V — negligible
- Powered from RPi 3.3V pin (Pin 1) which can supply up to ~50mA

### GPIO current
- RPi GPIO pins can source ~16mA each (max)
- Opto-isolated relay modules typically draw 5-10mA per input — well within limits
- Speed sensor signal pin draws effectively 0mA (high-impedance input)

## Wiring Checklist

### Relay module
- [ ] RPi powered off during wiring
- [ ] Bike unplugged from mains during wiring
- [ ] Relay module VCC connected to RPi 5V (Pin 2)
- [ ] Relay module GND connected to RPi GND (Pin 6)
- [ ] GPIO 17 (Pin 11) connected to relay IN1 (resistance up)
- [ ] GPIO 27 (Pin 13) connected to relay IN2 (resistance down)
- [ ] Relay 1 COM connected to bike + button pad A
- [ ] Relay 1 N.O. connected to bike + button pad B
- [ ] Relay 2 COM connected to bike - button pad A
- [ ] Relay 2 N.O. connected to bike - button pad B
- [ ] All connections secure (soldered or firmly crimped)
- [ ] No bare wire touching other components
- [ ] Original buttons still function when relay is off
- [ ] Test with `python scripts/test_buttons.py` before connecting to bike

### Speed sensor
- [ ] A3144 VCC (pin 1) connected to RPi 3.3V (Pin 1)
- [ ] A3144 GND (pin 2) connected to RPi GND (Pin 9)
- [ ] A3144 Signal (pin 3) connected to RPi GPIO 22 (Pin 15)
- [ ] 10kΩ pull-up resistor between 3.3V and signal (optional for short wires)
- [ ] Magnet securely glued to flywheel rim
- [ ] Sensor mounted on frame, 2-8mm gap from magnet path
- [ ] Magnet clears sensor without contact when flywheel spins
- [ ] Test with `python scripts/test_speed_sensor.py` — spin flywheel by hand
