#!/usr/bin/env bash
# Kinomap Resistance Bridge — Raspberry Pi Setup Script
# Run this once after cloning the repository.

set -euo pipefail

echo "=== Kinomap Resistance Bridge — RPi Setup ==="
echo ""

# Check we're on a Raspberry Pi (or at least Linux ARM)
if [[ ! -f /proc/device-tree/model ]] && [[ "$(uname -m)" != arm* ]] && [[ "$(uname -m)" != aarch64 ]]; then
    echo "WARNING: This doesn't appear to be a Raspberry Pi."
    echo "GPIO features won't work, but you can still develop/test the BLE code."
    echo ""
fi

# Update package lists
echo "[1/5] Updating package lists..."
sudo apt-get update -qq

# Install system dependencies
echo "[2/5] Installing system dependencies..."
sudo apt-get install -y -qq \
    python3 \
    python3-pip \
    python3-venv \
    python3-dbus \
    bluetooth \
    bluez \
    libdbus-1-dev \
    libglib2.0-dev

# Check BlueZ version
BLUEZ_VERSION=$(bluetoothctl --version 2>/dev/null | grep -oP '\d+\.\d+' || echo "unknown")
echo "   BlueZ version: $BLUEZ_VERSION"
if [[ "$BLUEZ_VERSION" != "unknown" ]]; then
    MAJOR=$(echo "$BLUEZ_VERSION" | cut -d. -f1)
    MINOR=$(echo "$BLUEZ_VERSION" | cut -d. -f2)
    if (( MAJOR < 5 || (MAJOR == 5 && MINOR < 50) )); then
        echo "   WARNING: BlueZ 5.50+ recommended. You have $BLUEZ_VERSION."
    fi
fi

# Create Python virtual environment
echo "[3/5] Creating Python virtual environment..."
VENV_DIR="$(cd "$(dirname "$0")/.." && pwd)/venv"
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

# Install Python dependencies
echo "[4/5] Installing Python dependencies..."
pip install --upgrade pip -q
pip install -r "$(dirname "$0")/../requirements.txt" -q

# Enable Bluetooth service
echo "[5/5] Ensuring Bluetooth service is running..."
sudo systemctl enable bluetooth
sudo systemctl start bluetooth

# Check BLE adapter
echo ""
echo "=== Checking BLE adapter ==="
if command -v hciconfig &>/dev/null; then
    hciconfig
else
    echo "hciconfig not found — using bluetoothctl instead"
    bluetoothctl show 2>/dev/null || echo "No adapter found"
fi

echo ""
echo "=== Setup complete! ==="
echo ""
echo "Next steps:"
echo "  1. Copy config:        cp config/default.yaml config/local.yaml"
echo "  2. Edit your config:   nano config/local.yaml"
echo "  3. Test BLE adapter:   python -m src.ftms.ble_server --test"
echo "  4. Test GPIO/relays:   python scripts/test_buttons.py"
echo "  5. Run the bridge:     python -m src.main"
echo ""
echo "Activate the venv in future sessions with:"
echo "  source venv/bin/activate"
