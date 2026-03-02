# Hardware Investigation Guide

Before wiring anything, you need to understand how your bike's resistance buttons work. This guide walks through the investigation process.

## Safety First

- **Unplug the bike from mains power** before opening the console
- Take photos at every step so you can reassemble correctly
- Use a multimeter set to the correct range — start with voltage, not current
- Don't short unknown circuits — measure first

## Step 1: Access the Button Circuit

### Tools needed
- Phillips/flathead screwdrivers
- Multimeter (essential)
- Phone camera for documentation photos

### Process
1. Locate the console/display unit on your bike
2. Remove screws holding the console cover (usually on the back)
3. Carefully separate the cover — watch for ribbon cables
4. Photograph the PCB, noting the button locations
5. Identify the +/- resistance button solder pads or ribbon cable contacts

### What to document
- [ ] Photo of console PCB (front)
- [ ] Photo of console PCB (back/solder side)
- [ ] Photo of button mechanism (membrane, tactile switch, etc.)
- [ ] Photo of any ribbon cables connecting buttons to main board
- [ ] Markings on the PCB near buttons (component labels, trace routing)

## Step 2: Identify Button Type

### Membrane switch (most common on exercise bikes)
- Flat flexible sheet with printed contacts
- Pressing flexes the membrane to complete a circuit
- Usually connected via a ribbon cable to the main PCB
- **Key measurement point**: Where the ribbon cable meets the PCB

### Tactile push button (click-style)
- Small through-hole or SMD component on the PCB
- Has 2 or 4 pins
- **Key measurement point**: Across the button pins

### Capacitive touch
- No physical switch — detects finger proximity
- Harder to simulate — may require a different approach
- Look for exposed copper pads with no mechanical switch

## Step 3: Measure the Button Circuit

### Voltage measurement
1. Power the bike ON (be careful with exposed PCB)
2. Set multimeter to DC voltage, 20V range
3. Measure across the button contacts (both sides) with button NOT pressed
4. Note the voltage: _____ V
5. Measure again while pressing the button
6. Note the voltage while pressed: _____ V

### Typical findings

| Scenario | Open voltage | Pressed voltage | What it means |
|----------|-------------|-----------------|---------------|
| Pull-up | 3.3V or 5V | 0V | Button pulls to ground — relay can short this |
| Pull-down | 0V | 3.3V or 5V | Button pulls to VCC — relay can short this |
| Matrix | Varies | Varies | Part of a scanning matrix — more complex |
| Analog | Varies | Varies | Analog resistance ladder — need specific resistance |

### Continuity test
1. Power the bike OFF
2. Set multimeter to continuity/beep mode
3. Place probes across button contacts
4. Press the button — should beep (closed circuit)
5. Release — should not beep (open circuit)

### Current measurement (if needed)
1. Set multimeter to mA DC range
2. Place in series with button (one probe on each contact)
3. Press the button
4. Note current draw: _____ mA

**Expected**: Usually < 1mA for digital button inputs. If you see > 10mA, the button may be driving something directly (unusual).

## Step 4: Determine Wiring Strategy

### Simple case (most common): Button shorts two contacts
The button simply connects two points when pressed. A relay contact in parallel achieves the same thing.

```
BEFORE (button only):

    PCB ──── Button ──── PCB
    (pad A)          (pad B)

AFTER (relay added in parallel):

    PCB ──── Button ──── PCB
    (pad A)  ║       ║  (pad B)
             ║       ║
             ╚═ Relay ═╝
               (N.O.)
```

Wire the relay's Normally Open (N.O.) contacts to pad A and pad B. When the relay energizes, it shorts the same two points the button does.

### Complex case: Matrix or analog buttons
If buttons are part of a scanning matrix or analog ladder, you'll need to identify the specific signals. See [troubleshooting.md](troubleshooting.md) for guidance.

## Step 5: Record Your Findings

Fill in this template for your bike:

```yaml
# Bike Investigation Results
bike_model: "Drax Recumbent 2017"
date_investigated: "YYYY-MM-DD"

buttons:
  type: "membrane"  # membrane, tactile, capacitive
  mechanism: "pull-up to ground"  # pull-up to ground, pull-down to vcc, matrix, analog

  resistance_up:
    open_voltage_v: null     # Voltage with button NOT pressed
    pressed_voltage_v: null  # Voltage with button pressed
    current_ma: null         # Current when pressed (if measured)
    pad_a_location: ""       # Description or photo reference
    pad_b_location: ""       # Description or photo reference

  resistance_down:
    open_voltage_v: null
    pressed_voltage_v: null
    current_ma: null
    pad_a_location: ""
    pad_b_location: ""

isolation_needed: true  # true if bike circuit > 3.3V or unknown
wire_length_cm: null    # Distance from console to where RPi will sit
notes: ""
```

## Step 6: Plan Your Wiring

### If voltage <= 3.3V and current < 1mA
You could potentially use GPIO directly with an optocoupler (no relay needed). However, a relay is still recommended for safety.

### If voltage is 5V-12V
Use opto-isolated relay module. Standard 5V relay modules from Arduino suppliers work fine.

### If voltage > 12V or unknown
Use relay module AND additional optocoupler isolation. Better safe than sorry.

### Wire routing
- Plan the cable path from RPi to bike console
- Use shielded wire if running alongside power cables
- Keep wire lengths reasonable (< 2m ideally)
- Consider strain relief at both ends

## Next Steps

Once you've completed this investigation:
1. Update `config/local.yaml` with your findings
2. Proceed to [schematics/relay-circuit.md](schematics/relay-circuit.md) for wiring instructions
3. Run `python scripts/test_buttons.py` to verify relay operation
