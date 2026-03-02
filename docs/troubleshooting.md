# Troubleshooting

## BLE / Bluetooth Issues

### Kinomap doesn't see the device

1. **Check BlueZ is running**:
   ```bash
   sudo systemctl status bluetooth
   ```

2. **Check BLE adapter is up**:
   ```bash
   sudo hciconfig hci0 up
   hciconfig  # Should show "UP RUNNING"
   ```

3. **Verify advertisement is active**:
   ```bash
   # On another device, or using btmon on the RPi:
   sudo btmon
   # Look for "LE Advertising Report" entries
   ```

4. **Check for adapter conflicts**: If using the RPi's built-in Bluetooth AND a USB dongle, BlueZ may default to the wrong one. Specify the adapter in config:
   ```yaml
   ble:
     adapter: "hci0"  # or "hci1" for USB dongle
   ```

5. **Appearance value**: Kinomap filters by device type. Ensure the advertisement includes appearance `0x0481` (Indoor Bike). Check `src/ftms/ble_server.py`.

### Kinomap connects but immediately disconnects

- Ensure the FTMS Feature characteristic reports the correct capabilities
- Kinomap may disconnect if it doesn't receive telemetry within a few seconds — check that notifications are starting
- Check RPi system logs: `journalctl -u bluetooth -f`

### Kinomap connects but never sends commands

- The app must first send a `Request Control` (0x00) command. Ensure your control point characteristic is writable and responds with success.
- Try a different Kinomap ride/video — some modes may not send resistance commands.

### "Command Disallowed" or pairing errors

```bash
# Reset Bluetooth and clear paired devices:
sudo bluetoothctl
> remove <device_address>
> exit
sudo systemctl restart bluetooth
```

## GPIO / Relay Issues

### Relay clicks but bike doesn't respond

1. **Check wiring**: Use multimeter continuity mode across the relay's N.O. contacts while triggering the relay. You should get a beep when active.

2. **Check button contact points**: Re-verify you're wired to the correct pads. Measure voltage at the pads — it should change when the relay fires.

3. **Press duration too short**: Some bikes need a minimum hold time. Increase `button_hold_ms` in config (try 150ms, 200ms, 300ms).

4. **Press duration too long**: Some bikes interpret a long press differently (e.g., rapid-change mode). Try shorter durations.

### Relay doesn't click

1. **Check GPIO pin**: Run the test script to verify GPIO output:
   ```bash
   python scripts/test_buttons.py --gpio-only
   ```

2. **Check relay power**: Most relay modules need 5V on VCC. The RPi's 5V pin (physical pin 2 or 4) should power the module.

3. **Check relay logic**: Some modules are active-LOW (relay activates when GPIO goes LOW). Check your module's documentation and set `relay_active_low: true` in config if needed.

### Multiple presses register as one (or vice versa)

Adjust timing parameters in config:
```yaml
gpio:
  button_hold_ms: 100      # How long to hold the relay closed
  inter_press_delay_ms: 150 # Delay between consecutive presses
```

Start with longer values and reduce until reliable.

## Resistance Mapping Issues

### Resistance changes are too aggressive / not enough

Edit the inclination-to-level mapping in `config/local.yaml`:
```yaml
bridge:
  inclination_map:
    -10.0: 1    # -10% grade → level 1
    0.0: 5      # flat → level 5
    5.0: 10     # 5% grade → level 10
    15.0: 16    # 15% grade → level 16
```

### Resistance drifts over time (gets out of sync)

Since we track resistance in software with no feedback from the bike, drift can occur if:
- A button press doesn't register (relay timing issue)
- The bike was manually adjusted

**Fix**: The bridge runs a "home" procedure on startup (presses DOWN enough times to guarantee minimum resistance). You can trigger this manually:
```bash
# Send SIGUSR1 to re-home
kill -USR1 $(pgrep -f "src.main")
```

Or increase the home presses in config to exceed your bike's max range:
```yaml
bridge:
  home_presses: 30  # Press DOWN this many times on startup
```

### Flat terrain but resistance isn't at minimum

Check your `inclination_map`. A grade of 0.0% maps to whatever level you configure. Set it to `1` if you want flat = minimum resistance.

## Software Issues

### "Permission denied" errors with BLE

BlueZ requires root or proper capabilities:
```bash
# Option 1: Run as root
sudo python -m src.main

# Option 2: Set capabilities (preferred)
sudo setcap cap_net_raw,cap_net_admin+eip $(which python3)
```

### "dbus-next" connection errors

```bash
# Ensure D-Bus system bus is accessible:
dbus-send --system --dest=org.freedesktop.DBus \
  --type=method_call --print-reply /org/freedesktop/DBus \
  org.freedesktop.DBus.ListNames
```

### Module not found errors

```bash
# Ensure you're in the project directory:
cd /path/to/kinomap-resistance-bridge

# Install dependencies:
pip install -r requirements.txt

# Run with module syntax:
python -m src.main
```

### High CPU usage

The BLE event loop should be idle most of the time. If CPU is high:
- Check that telemetry notification interval isn't too fast (1Hz is fine)
- Ensure no busy-wait loops in GPIO thread
- Check system logs for BlueZ errors causing reconnection loops

## General Debugging

### Enable verbose logging
```bash
python -m src.main --log-level DEBUG
```

### Monitor BLE traffic
```bash
sudo btmon | tee ble_capture.log
```

### Test FTMS with a phone app
Use "nRF Connect" (Nordic Semiconductor) on your phone to:
- Scan and find the RPi device
- Connect and browse FTMS characteristics
- Write to the control point manually
- Verify notifications are being sent

This helps isolate whether issues are in the FTMS layer vs. Kinomap specifically.
