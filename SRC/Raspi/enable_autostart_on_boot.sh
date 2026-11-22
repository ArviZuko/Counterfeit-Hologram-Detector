#!/usr/bin/env bash
# ==============================================================================
# enable_autostart_on_boot.sh
# Enables automatic startup of Hologram Detector when Raspberry Pi is powered on.
# Works across Raspberry Pi OS (Bullseye, Bookworm, Wayland, X11, PiTFT).
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_NAME="HologramDetector"
INSTALL_DIR="$HOME/$APP_NAME"
LAUNCH_SCRIPT="$INSTALL_DIR/launch.sh"
DESKTOP_SRC="$HOME/Desktop/${APP_NAME}.desktop"
AUTOSTART_DIR="$HOME/.config/autostart"
AUTOSTART_FILE="$AUTOSTART_DIR/${APP_NAME}.desktop"

echo "======================================================================"
echo "    Enabling Auto-Start on Boot for Hologram Detector"
echo "======================================================================"

# If app is not installed to ~/HologramDetector, run installer first
if [ ! -f "$LAUNCH_SCRIPT" ]; then
    echo "[Info] Running installer first to prepare application..."
    bash "$SCRIPT_DIR/install_raspberry_pi.sh"
fi

mkdir -p "$AUTOSTART_DIR"

# Create / update autostart desktop entry
cat > "$AUTOSTART_FILE" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Hologram Detector
Comment=AI Hologram Authenticity Verification
Exec=bash "$LAUNCH_SCRIPT"
Icon=$INSTALL_DIR/icon.png
Terminal=false
Categories=Science;Education;
StartupNotify=true
X-GNOME-Autostart-enabled=true
EOF

chmod +x "$AUTOSTART_FILE"

# Make sure desktop file exists on user's desktop too
mkdir -p "$HOME/Desktop"
cp "$AUTOSTART_FILE" "$HOME/Desktop/${APP_NAME}.desktop"
chmod +x "$HOME/Desktop/${APP_NAME}.desktop"

if command -v gio &>/dev/null; then
    gio set "$HOME/Desktop/${APP_NAME}.desktop" "metadata::trusted" true 2>/dev/null || true
fi

# Ensure Raspberry Pi is configured to automatically log in to desktop
# (raspi-config nonint do_boot_behaviour B4 = Desktop Auto-login)
if command -v raspi-config &>/dev/null; then
    echo "Configuring Raspberry Pi OS for Auto-login to Desktop..."
    sudo raspi-config nonint do_boot_behaviour B4 2>/dev/null || true
fi

echo ""
echo "======================================================================"
echo "  ✅  AUTO-START ON BOOT IS NOW ENABLED!"
echo ""
echo "  When you plug in your Raspberry Pi to power:"
echo "    1. Raspberry Pi OS boots up and logs in automatically"
echo "    2. The display size is automatically detected"
echo "    3. Hologram Detector launches full screen"
echo "    4. Camera feed starts streaming right away"
echo ""
echo "  To disable at any time, run: ./disable_autostart_on_boot.sh"
echo "======================================================================"

