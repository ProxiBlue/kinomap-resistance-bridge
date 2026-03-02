# Architecture

## Overview

The bridge has three layers that form a pipeline:

```
Kinomap App
    │
    ▼
┌──────────────────────────────────────────────────┐
│  FTMS Layer (src/ftms/)                          │
│  - BLE GATT server with FTMS service             │
│  - Advertises as "Indoor Bike" device            │
│  - Receives: Set Target Inclination, Set Target  │
│    Resistance Level, Start/Stop commands          │
│  - Sends: Indoor Bike Data (speed, cadence,      │
│    power, resistance level)                       │
└──────────────────┬───────────────────────────────┘
                   │ FTMS control point opcodes
                   ▼
┌──────────────────────────────────────────────────┐
│  Bridge Layer (src/bridge/)                      │
│  - Maps FTMS inclination/resistance → bike level │
│  - Tracks current resistance state               │
│  - Calculates delta (how many +/- presses)       │
│  - Applies safety limits and rate limiting       │
└──────────────────┬───────────────────────────────┘
                   │ press_up(n) / press_down(n)
                   ▼
┌──────────────────────────────────────────────────┐
│  GPIO Layer (src/gpio/)                          │
│  - Controls relay module via GPIO pins           │
│  - Handles button press timing (hold duration,   │
│    inter-press delay)                            │
│  - Supports both relay and optocoupler modes     │
└──────────────────────────────────────────────────┘
```

## Data Flow: Kinomap → Bike

1. **Kinomap sends an FTMS control point command** — typically `Set Target Inclination` with a value like +5.0% grade, or `Set Target Resistance Level` with a value 0-100%.

2. **FTMS layer decodes the command** — parses the BLE characteristic write, validates the opcode and parameters, and passes structured data to the bridge layer.

3. **Bridge layer calculates button presses** — using the configured mapping table, it determines what bike resistance level corresponds to the FTMS command, compares to the current tracked level, and computes how many +/- presses are needed.

4. **GPIO layer executes button presses** — activates the appropriate relay for the configured hold duration, waits the inter-press delay, and repeats for the required number of presses.

5. **Bridge layer updates state and telemetry** — updates the tracked resistance level and generates plausible telemetry data (speed, cadence, power) to report back to Kinomap.

## Data Flow: Bike → Kinomap (Simulated Telemetry)

Since the bike has no sensors we can read, telemetry is simulated:

- **Speed**: Calculated from a base speed modified by current resistance level
- **Cadence**: Configurable fixed value or slowly varying random
- **Power**: Estimated from resistance level using a simple model
- **Resistance Level**: The current tracked level (0-100%)

This is sufficient to keep Kinomap's session active. For more accurate telemetry, a cadence sensor could be added to the bike in a future phase.

## Key Design Decisions

### Why Python + dbus-next (not Node.js/Zwack)?

- `dbus-next` provides async D-Bus access to BlueZ, giving full control over BLE GATT server setup
- Python is the standard language for RPi GPIO projects, with mature libraries
- Avoids the complexity of Node.js native BLE modules (`noble`/`bleno`) which have known issues on newer RPi OS versions
- Open Rowing Monitor proved this stack works with Kinomap

### Why relay module instead of direct GPIO?

- Relay provides galvanic isolation between RPi and bike circuits
- Bike button circuits may operate at different voltages (5V, 12V, or higher)
- Relay contacts are bidirectional — works regardless of button circuit polarity
- Opto-isolated relay modules add a second layer of protection

### Why track resistance state in software?

- The bike has no feedback mechanism to report its current resistance
- We must track state ourselves, starting from a known position (e.g., minimum resistance on startup)
- The "home" procedure (press DOWN many times on startup) establishes a known baseline

### Inclination vs. Resistance mapping

Kinomap typically sends `Set Target Inclination` for video rides (terrain following). This is a grade percentage (e.g., -5% to +15%). The bridge maps this to the bike's discrete resistance levels using a configurable curve:

```
Inclination (%)     Bike Level
─────────────────────────────
   -10 or less  →    1 (min)
    -5          →    3
     0 (flat)   →    5
    +5          →    8
   +10          →   12
   +15 or more  →   16 (max)
```

The mapping is defined in `config/default.yaml` and can be customized. Linear interpolation is used between defined points.

## Threading Model

```
Main Thread
├── asyncio event loop
│   ├── BLE GATT server (dbus-next)
│   ├── FTMS command handler (async callbacks)
│   └── Telemetry notification timer (1Hz)
│
└── GPIO thread (separate, with queue)
    ├── Reads press commands from queue
    └── Executes timed relay activations
```

GPIO operations are isolated in a separate thread because relay timing requires precise delays that shouldn't block the BLE event loop. Communication is via a thread-safe queue.

## Configuration

All tunable parameters live in YAML config files:

- `config/default.yaml` — sensible defaults for a generic bike
- `config/local.yaml` — your bike-specific overrides (git-ignored)

See [default.yaml](../config/default.yaml) for the full list of parameters.
