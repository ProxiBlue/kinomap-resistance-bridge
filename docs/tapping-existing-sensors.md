# Option 1: Tapping Your Bike's Existing Sensors

Your Drax recumbent already has a display showing RPM and distance — which means there's already a sensor on the flywheel feeding a signal to the console PCB. Tapping into that signal is easier than adding your own magnet and sensor.

## What You're Looking For

The bike's console gets its RPM/distance data from a sensor near the flywheel. There are two common types used in exercise bikes:

### Type A: Reed Switch (most common in 2017-era bikes)

- A small glass tube (~15mm long) mounted near the flywheel
- 2 wires going back to the console
- A magnet on the flywheel passes it to trigger a pulse
- No power needed — it's a passive switch

```
What it looks like:

    ┌──────────────┐
    │  Glass tube   │  ~15mm long, ~3mm diameter
    │  with 2 wires │  Often in a plastic housing or heat-shrink
    └──┬────────┬──┘
       │        │
       wire     wire  (2 wires only, going to console)
```

### Type B: Hall Effect Sensor

- A small black plastic component (looks like a transistor) near the flywheel
- 3 wires going back to the console
- A magnet on the flywheel triggers it
- Needs power (usually 5V from the console)

```
What it looks like:

    ┌─────────┐
    │  Small   │  ~4mm x 3mm, flat black plastic
    │  black   │  Looks like a tiny transistor
    │  chip    │
    └─┬──┬──┬─┘
      │  │  │
      V  G  S   (3 wires: VCC, GND, Signal)
```

## Finding the Sensor: Step by Step

### Step 1: Locate the flywheel

On a recumbent bike, the flywheel is typically:
- At the front of the bike, behind a plastic shroud/cover
- Connected to the pedals via a belt or chain
- A heavy metal disc, 15-30cm diameter

Remove or open the shroud to expose the flywheel area.

### Step 2: Find the sensor

Look around the edge of the flywheel for:
- A small component mounted to the frame, pointed at the flywheel rim
- 2 or 3 thin wires running from it back toward the console
- A magnet on the flywheel rim (may be glued, embedded, or a bump on the surface)

**Common mounting locations:**
```
Side view of flywheel area:

         Flywheel
        ┌────────────────────┐
        │                    │
        │    ╭────╮          │
        │    │ Mag│          │  ← magnet glued to rim
        │    ╰────╯          │
        │       ↕ small gap  │
        │    ┌──────┐        │
        │    │Sensor│        │  ← mounted on frame or bracket
        │    └──┬───┘        │
        │       │ wires      │
        └───────┼────────────┘
                │
                ▼ to console PCB
```

### Step 3: Count the wires

This tells you what type of sensor it is:

| Wires | Sensor type | Signal type |
|-------|-------------|-------------|
| **2** | Reed switch | Passive switch — closes when magnet passes |
| **3** | Hall effect | Active — outputs a voltage pulse when magnet passes |

### Step 4: Trace the wires to the console

Follow the sensor wires back to the console PCB. They may:
- Run through the frame tubes
- Be bundled with other wires (power, buttons)
- Connect to the PCB via a plug/connector or soldered directly

Note where they connect to the PCB — you'll tap into the signal there OR at the sensor end.

## Identifying the Signal

### If 2 wires (reed switch)

1. Set multimeter to **continuity/beep mode**
2. Disconnect the sensor from the console (unplug or desolder one wire)
3. Touch probes to the two sensor wires
4. Slowly rotate the flywheel by hand
5. You should hear a **beep once per revolution** as the magnet passes

If it beeps: confirmed reed switch. You can tap this directly.

### If 3 wires (Hall sensor)

1. With the bike powered on, set multimeter to **DC voltage, 20V range**
2. Find the GND wire (usually black or the one connected to ground on the PCB)
3. Measure each of the other two wires against GND:
   - One should show steady voltage (VCC — likely 5V or 3.3V)
   - One should show voltage that **pulses or fluctuates** when you spin the flywheel — that's the signal wire
4. Note the voltage levels:
   - Signal HIGH voltage: _____ V (when magnet NOT near sensor)
   - Signal LOW voltage: _____ V (when magnet passes)

## Tapping the Signal

### Reed switch (2 wires) → easiest

Wire in parallel — don't cut or disconnect anything. The bike's own display keeps working.

```
Existing circuit (don't touch):

    Console PCB ─────── Reed Switch ─────── Console PCB
    (pin A)              (on frame)          (pin B)


Add your tap wires in parallel:

    Console PCB ─────── Reed Switch ─────── Console PCB
    (pin A)              (on frame)          (pin B)
        │                                       │
        │           Your added wires            │
        └──────── RPi GPIO 22 (Pin 15)          │
                                                │
                  RPi GND (Pin 9) ──────────────┘
```

Config settings:
```yaml
speed_sensor:
  enabled: true
  pin: 22
  pull_up: true     # RPi internal pull-up, since reed switch is passive
  debounce_ms: 10   # Reed switches can bounce — slightly higher than Hall
```

### Hall sensor (3 wires)

Tap only the signal wire — don't disturb VCC or GND.

```
Existing circuit (don't touch):

    Console ── VCC ──── Hall Sensor ──── Signal ──── Console
    Console ── GND ──── Hall Sensor                  (pin S)
                                                       │
                                              Your tap wire
                                                       │
                                                       ▼
                                               RPi GPIO 22 (Pin 15)

    Also connect RPi GND to the bike's GND:
    Console GND ──────────── RPi GND (Pin 9)
```

**IMPORTANT: Check the signal voltage!**

| Signal voltage | Action needed |
|----------------|---------------|
| 3.3V or less | Wire directly to RPi GPIO — safe |
| 5V | Need a voltage divider (see below) |
| Higher than 5V | Unlikely, but use an optocoupler if so |

### 5V → 3.3V voltage divider

If the Hall sensor signal is 5V, the RPi GPIO is only 3.3V tolerant. Use two resistors:

```
Hall signal (5V) ──── [10kΩ] ────┬──── RPi GPIO 22
                                 │
                               [20kΩ]
                                 │
                                GND

Output = 5V × 20k / (10k + 20k) = 3.33V ✓
```

Use any two resistors with a 1:2 ratio. Examples: 4.7kΩ + 10kΩ, 10kΩ + 22kΩ, 3.3kΩ + 6.8kΩ. Close enough is fine — anything that brings 5V down to ≤3.3V.

## What to Record

Fill in this template when you investigate:

```yaml
# Existing Sensor Investigation
bike_model: "Drax Recumbent 2017"
date_investigated: ""

sensor:
  type: ""               # "reed_switch" or "hall_effect"
  wire_count: null        # 2 or 3
  location: ""            # Description of where on the frame
  wire_colors: ""         # e.g. "red and black" or "red, black, white"
  connector_type: ""      # "soldered", "JST plug", "bare wire twist"

  # For Hall sensor only:
  vcc_voltage: null       # Voltage on VCC wire (e.g. 5.0)
  signal_high_v: null     # Signal voltage when magnet is NOT near
  signal_low_v: null      # Signal voltage when magnet passes
  signal_wire_color: ""   # Which wire is the signal

  # For reed switch only:
  continuity_confirmed: false  # Did it beep on continuity test?

magnet:
  location: ""            # Where on the flywheel
  type: ""                # "glued disc", "embedded", "bolted"
  count: null             # How many magnets (usually 1, sometimes 2-4)

pulses_per_revolution: null  # Usually 1, but some bikes have multiple magnets
flywheel_circumference_m: null  # Measure diameter × 3.14159

notes: ""
```

## Multiple Magnets

Some bikes have 2, 4, or even more magnets evenly spaced around the flywheel for smoother speed readings. If yours does:

1. Spin the flywheel slowly and count how many times the multimeter beeps per revolution
2. Set this in the config:

```yaml
speed_sensor:
  # If your flywheel has 4 magnets, each revolution produces 4 pulses
  # The code needs to know this to calculate RPM correctly
  pulses_per_revolution: 4
```

**We need to add this config option to the code** — I've noted it below.

## Advantages Over Adding Your Own Sensor

- No magnet to glue on — already there
- No sensor to mount and align — already mounted
- Factory-calibrated positioning — reliable gap distance
- Bike's own display keeps working (tapping in parallel)
- Cleaner install — fewer things attached to the bike

## Next Steps

1. Open the flywheel shroud and find the sensor
2. Count wires (2 or 3)
3. Do the multimeter tests described above
4. Record your findings in the template
5. Tap the signal wire to RPi GPIO 22 following the wiring guide above
6. Update `config/local.yaml` with your findings
7. Test with `python scripts/test_speed_sensor.py`
