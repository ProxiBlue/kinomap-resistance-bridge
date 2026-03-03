# Kinomap Auto-Resistance Bridge

> **STATUS: CONCEPTUAL / IN DEVELOPMENT**
>
> This project is still in the design and planning phase. **Nothing has been built or tested on real hardware yet.** Parts have been ordered. The code, wiring diagrams, and documentation represent the intended design — expect changes as hardware testing begins. Contributions, feedback, and ideas are welcome!

---

**Automatically control a non-smart exercise bike's resistance from any FTMS-compatible cycling app (Kinomap, MyWhoosh, Zwift, Rouvy, etc.)**

This project turns a dumb exercise bike into a smart trainer by emulating a Bluetooth FTMS (Fitness Machine Service) device on a Raspberry Pi. The app sends resistance/gradient commands, and the RPi converts them into physical button presses on the bike via relay-controlled GPIO pins. A speed sensor provides real telemetry back to the app.

There are other projects as this existing, but they all target the drive motor/belt side, to set the resistance there. My bioke has electronic push buttons to increase/decrease resistance. My route is to allow remote action of the buttons. So I am doing less invasing changes to the bike.

## How It Works

```
┌─────────────────────┐     BLE/FTMS      ┌─────────────────────┐
│                     │ ◄───────────────── │                     │
│   Raspberry Pi      │   resistance &     │   Phone / Tablet /  │
│   (FTMS Emulator)   │   gradient cmds    │   PC running any    │
│                     │ ──────────────────►│   FTMS cycling app  │
│                     │   real telemetry   │                     │
└────────┬───────┬────┘   (speed, cadence, └─────────────────────┘
         │       │         power, distance)
         │       │
    GPIO out   GPIO in
         │       │
┌────────▼──┐ ┌──▼─────────────┐
│  Relay    │ │  Speed Sensor   │
│  Module   │ │  (Hall effect / │
│  (2-ch)   │ │   reed switch)  │
└────────┬──┘ └──┬─────────────┘
         │       │
    ┌────▼───────▼────┐
    │  Exercise Bike   │
    │  +/- buttons     │
    │  flywheel        │
    └─────────────────┘
```

**The flow:**
1. Any FTMS app detects the RPi as a standard smart indoor bike
2. As terrain changes, the app sends inclination/resistance commands via BLE
3. The RPi calculates how many +/- button presses are needed
4. GPIO pins trigger relays that short the bike's button contacts, simulating presses
5. A speed sensor on the flywheel provides real speed, cadence, and distance data back to the app

## Features

- **Standard FTMS protocol** — works with any FTMS-compatible app (Kinomap, MyWhoosh, Zwift, Rouvy, TrainerRoad, etc.)
- **Real speed telemetry** — Hall effect sensor or tap into the bike's existing sensor for real speed, cadence, distance, and estimated power
- **Configurable resistance mapping** — calibrate inclination-to-resistance curves for your specific bike
- **Safety limits** — configurable min/max resistance, rate limiting on button presses
- **Modular design** — easy to adapt for different bikes and button configurations
- **3D printable case** — parametric OpenSCAD design for RPi + relay module enclosure

## Hardware Requirements

| Component | Purpose | Est. Cost (AUD) |
|-----------|---------|-----------------|
| Raspberry Pi 3/4/Zero 2W | BLE + GPIO controller | $15-55 |
| 2-channel relay module (opto-isolated) | Button press simulation | $5-12 |
| A3144 Hall effect sensor | Speed/cadence sensing | $2-3 |
| Small magnet | Triggers sensor on flywheel | $0-2 |
| 10kΩ resistor | Pull-up for sensor signal | $0.10 |
| Dupont jumper wires (F-F) | RPi to relay connections | $3 |
| Hookup wire (22-26 AWG) | Relay to bike, sensor to RPi | $2 |
| **Total** | | **$30-80** |

> The speed sensor + magnet can be skipped if you tap into the bike's existing sensor instead. See [Tapping Existing Sensors](docs/tapping-existing-sensors.md).

## Software Requirements

- Raspberry Pi OS (Bullseye or later)
- Python 3.9+
- BlueZ 5.50+ (included in RPi OS)

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/lpetrolo/kinomap-resistance-bridge.git
cd kinomap-resistance-bridge
./scripts/setup_rpi.sh
```

### 2. Investigate your bike

Before wiring anything, investigate your bike's button circuit and existing sensors:
- [Button Investigation Guide](docs/hardware-investigation.md)
- [Tapping Existing Sensors](docs/tapping-existing-sensors.md) (if your bike has a digital display)

### 3. Build the hardware

Follow the [Build Guide](BUILD_GUIDE.md) for the complete parts list, wiring diagrams, and step-by-step assembly instructions.

### 4. Configure

```bash
cp config/default.yaml config/local.yaml
nano config/local.yaml
```

### 5. Test components individually

```bash
# Test relay/GPIO wiring (no bike connected)
python scripts/test_buttons.py

# Test speed sensor (spin flywheel by hand)
python scripts/test_speed_sensor.py

# Test BLE advertising (check with phone BLE scanner)
python scripts/scan_ble.py

# Test FTMS service in isolation
python -m src.ftms.ble_server --test
```

### 6. Run the bridge

```bash
python -m src.main
```

### 7. Connect your app

1. Open Kinomap / MyWhoosh / Zwift on your device
2. Go to device pairing / Bluetooth settings
3. Look for "RPi Resistance Bridge" (or your configured name)
4. Pair and start riding — resistance auto-adjusts with the terrain!

## Project Structure

```
kinomap-resistance-bridge/
├── README.md                      # This file
├── BUILD_GUIDE.md                 # Complete build & wiring guide
├── nice-to-have-additions.md      # Future feature ideas
├── LICENSE                        # MIT License
├── requirements.txt               # Python dependencies
├── config/
│   └── default.yaml               # Default configuration
├── docs/
│   ├── architecture.md            # Design decisions & data flow
│   ├── hardware-investigation.md  # Button circuit investigation guide
│   ├── tapping-existing-sensors.md # Tap bike's built-in speed sensor
│   ├── ftms-protocol.md           # FTMS protocol reference
│   ├── troubleshooting.md         # Common issues and solutions
│   └── schematics/
│       └── relay-circuit.md       # Wiring diagrams (relay + speed sensor)
├── hardware/
│   ├── README.md                  # Case dimensions & print settings
│   └── case.scad                  # Parametric OpenSCAD case design
├── src/
│   ├── main.py                    # Application entry point
│   ├── config.py                  # Configuration loader
│   ├── ftms/                      # Bluetooth FTMS emulation
│   │   ├── ble_server.py          # BLE GATT server setup
│   │   ├── ftms_service.py        # FTMS service & characteristics
│   │   └── characteristics.py     # FTMS data encoding/decoding
│   ├── gpio/                      # Hardware control
│   │   ├── relay_controller.py    # Low-level relay/GPIO control
│   │   ├── button_simulator.py    # Button press timing & sequencing
│   │   └── speed_sensor.py        # Hall effect / reed switch reader
│   └── bridge/                    # Command translation logic
│       ├── resistance_mapper.py   # FTMS commands → resistance levels
│       └── command_handler.py     # Orchestrates FTMS → GPIO pipeline
├── tests/                         # Unit tests (run without hardware)
│   ├── test_ftms.py
│   ├── test_gpio.py
│   ├── test_bridge.py
│   └── test_speed_sensor.py
└── scripts/                       # Setup and utility scripts
    ├── setup_rpi.sh               # RPi initial setup
    ├── test_buttons.py            # Standalone relay tester
    ├── test_speed_sensor.py       # Standalone speed sensor tester
    └── scan_ble.py                # BLE scanning utility
```

## Documentation

- **[Build Guide](BUILD_GUIDE.md)** — Parts list, wiring, assembly, speed sensor mounting
- **[Architecture](docs/architecture.md)** — Design decisions, data flow, threading model
- **[Hardware Investigation](docs/hardware-investigation.md)** — How to investigate your bike's buttons
- **[Tapping Existing Sensors](docs/tapping-existing-sensors.md)** — Use the bike's built-in speed sensor
- **[FTMS Protocol](docs/ftms-protocol.md)** — Protocol details and implementation notes
- **[Relay & Sensor Schematics](docs/schematics/relay-circuit.md)** — Wiring diagrams
- **[3D Printed Case](hardware/README.md)** — Case design, dimensions, print settings
- **[Troubleshooting](docs/troubleshooting.md)** — Common problems and solutions
- **[Future Additions](nice-to-have-additions.md)** — HR relay, OLED display, fan control, etc.

## App Compatibility

The bridge speaks standard FTMS, so it works with any app that supports FTMS smart bikes:

| App | Subscription | Tested |
|-----|-------------|--------|
| Kinomap | Paid | Not yet |
| MyWhoosh | Free | Not yet |
| Zwift | Paid | Not yet |
| Rouvy | Paid | Not yet |
| TrainerRoad | Paid | Not yet |

## Adapting for Other Bikes

This project is designed to be bike-agnostic. To adapt it for a different bike:

1. Investigate your bike's button circuit (see [hardware guide](docs/hardware-investigation.md))
2. Update `config/local.yaml` with your bike's resistance levels, button timing, and GPIO mapping
3. If your bike uses a different button mechanism (e.g., mechanical toggle, rotary dial), you may need to modify `src/gpio/button_simulator.py`

## Related Projects

Projects that inspired or inform this work:

- [Zwack](https://github.com/paixaop/zwack) — BLE sensor simulator with FTMS, Node.js
- [Open Rowing Monitor](https://github.com/laberning/openrowingmonitor) — Full FTMS implementation, tested with Kinomap
- [qdomyos-zwift](https://github.com/cagnulein/qdomyos-zwift) — FTMS bridge for non-smart equipment
- [PiRowFlo](https://github.com/inokinoki/pirowflo) — Python-based BLE fitness device emulator

## License

MIT License. See [LICENSE](LICENSE) for details.

## Contributing

Contributions welcome! This is a DIY project and every non-smart bike is slightly different. If you adapt this for your bike, please consider submitting a PR with your configuration and any hardware notes.

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
