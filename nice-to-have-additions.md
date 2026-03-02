# Nice-to-Have Additions

Features to add once the basic bridge (resistance control + speed sensor) is working. Roughly ordered by impact vs effort.

---

## Multi-App Compatibility (MyWhoosh, Zwift, etc.)

**Priority: High — do this first after basics work**

MyWhoosh is a free alternative to Kinomap that also supports FTMS. Since our bridge already speaks standard FTMS protocol, it should work with any app that supports FTMS smart bikes — including MyWhoosh, Zwift, Rouvy, TrainerRoad, etc.

**What to check/adjust:**
- MyWhoosh may send different FTMS opcodes or prefer different control modes (e.g. ERG/power target mode vs simulation mode)
- May need to support `Set Target Power` (opcode 0x05) in addition to `Set Target Inclination` and `Set Indoor Bike Simulation`
- Test advertisement discovery — some apps filter by device name or appearance differently
- Add a config option for app-specific quirks if needed

**Hardware changes:** None — pure software.

**Effort:** Low if it works out of the box, medium if app-specific tweaks are needed.

---

## Easy Wins (minimal or no hardware)

### Heart Rate Relay

Pair a standard BLE heart rate strap (Polar H10, Garmin HRM, etc.) to the RPi. Read HR data via BLE and relay it through the FTMS Indoor Bike Data notifications to the app.

- FTMS already has an HR field in Indoor Bike Data (bit 9 in flags)
- The RPi acts as a BLE central (connecting to HR strap) AND peripheral (advertising to app) simultaneously — may need a USB BLE dongle for the second role
- No extra physical hardware beyond a HR strap (~$30-50, likely already owned)

**Effort:** Medium (BLE dual-role can be tricky).

### Session Logging & Strava Export

Log all telemetry (speed, cadence, power, HR, resistance) to a standard file format per ride session.

- Write FIT files (Garmin/Strava standard) or TCX files (simpler XML format)
- Auto-save to a folder on the RPi
- Optional: auto-upload to Strava via their API after the ride ends
- No hardware, just software using data already flowing through the bridge

**Effort:** Low-medium.

### Web Dashboard

Small web server (Flask/FastAPI) running on the RPi. Access from phone/tablet on the same WiFi.

- Live telemetry display (speed, cadence, power, resistance level, HR)
- Configuration editor (change resistance mapping, sensor calibration without SSH)
- Session history and stats
- Connection status and diagnostics
- No extra hardware

**Effort:** Medium.

### OLED Status Display

Small 0.96" I2C OLED screen (~$3-5) mounted on the case or bike.

- Shows: current resistance level, speed, cadence, connection status, HR
- Useful because the bike's own display won't reflect RPi-controlled resistance changes
- 4 wires: SDA (GPIO 2), SCL (GPIO 3), 3.3V, GND
- Libraries: `luma.oled` or `adafruit-circuitpython-ssd1306`

**Effort:** Low. Parts: ~$5.

---

## Medium Effort

### Automatic Fan Control

Wire a desk fan through a spare relay channel or MOSFET. Speed up/down based on cycling speed.

- Map speed ranges to fan states (off / low / high) or use PWM via MOSFET for variable speed
- Uses a spare GPIO pin + one relay channel or a logic-level MOSFET
- Very satisfying — wind on downhills, calm on climbs

**Effort:** Low-medium. Parts: one MOSFET ($1) or use spare relay channel.

### Dedicated Cadence Sensor

Second Hall effect sensor + magnet on the pedal crank arm, independent of the flywheel speed sensor.

- More accurate cadence than deriving from flywheel RPM via gear ratio
- Same wiring pattern as speed sensor: A3144 + magnet, 3 wires to another GPIO pin
- Improves power estimation (power = f(cadence, resistance) is more accurate than f(speed, resistance))

**Effort:** Low. Parts: ~$3 (same as speed sensor).

### LED Status Indicators

A few LEDs on the case for at-a-glance status.

- Green: connected to app
- Blue: BLE advertising (waiting for connection)
- Red: error / disconnected
- Yellow blink: resistance changing

**Effort:** Very low. Parts: ~$1.

---

## Bigger Projects

### Run Kinomap/MyWhoosh on the RPi Itself

Use Waydroid (Android runtime on Linux) to run the cycling app directly on the RPi. Output to a screen via HDMI.

- Eliminates the separate Android device / Chromecast entirely
- BLE connection becomes local (same device) — simpler and more reliable
- Needs RPi 4 with 4GB+ RAM
- Waydroid performance varies — needs testing with specific apps

**Effort:** High. Reward: simplified single-device setup.

### Auto-Calibration

Use the speed sensor to verify that resistance changes actually happened.

- When the bridge presses UP, speed should drop slightly (more resistance = slower)
- If speed doesn't change after a button press, the press may not have registered — retry
- Over time, builds a model of how speed relates to each resistance level on your specific bike
- Solves the drift-over-time problem without manual re-homing

**Effort:** Medium-high (needs data collection, statistical model, edge case handling).

### Physical Override Controls

Rotary encoder or physical buttons on the RPi case for manual resistance override.

- Override the app's resistance command temporarily
- Trigger re-homing manually
- Pause/resume auto-resistance
- Useful if the app sets resistance too high and you need to back off immediately

**Effort:** Low-medium. Parts: ~$2 (rotary encoder or buttons).

### ANT+ Support

Some apps (especially older ones or Garmin devices) use ANT+ instead of BLE. An ANT+ USB dongle (~$25) on the RPi could broadcast the same data via ANT+ FE-C protocol.

- Broadens compatibility beyond BLE-only apps
- Requires `python-ant` or `openant` library
- FE-C (Fitness Equipment Control) is the ANT+ equivalent of FTMS

**Effort:** Medium-high. Parts: ~$25 (ANT+ USB stick).

---

## Shopping List (all additions combined)

| Item | For which feature | ~AUD |
|------|------------------|------|
| BLE heart rate strap | HR relay | $30-50 |
| 0.96" I2C OLED SSD1306 | Status display | $3-5 |
| A3144 Hall sensor + magnet | Cadence sensor | $3 |
| Logic-level MOSFET (IRLZ44N) | Fan control | $1-2 |
| Rotary encoder | Physical override | $2 |
| LEDs + 330Ω resistors | Status indicators | $1 |
| USB BLE dongle | HR relay (dual-role BLE) | $10-15 |
| ANT+ USB dongle | ANT+ support | $25 |

None of these block each other — add them in any order once the basics are solid.
