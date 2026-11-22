#!/usr/bin/env bash
# ==============================================================================
# disable_autostart_on_boot.sh
# Disables automatic startup of Hologram Detector when Raspberry Pi powers on.
# (Keeps the desktop shortcut intact so you can still open it by clicking).
# ==============================================================================

set -e

APP_NAME="HologramDetector"
AUTOSTART_FILE="$HOME/.config/autostart/${APP_NAME}.desktop"

echo "======================================================================"
echo "    Disabling Auto-Start on Boot for Hologram Detector"
echo "======================================================================"

if [ -f "$AUTOSTART_FILE" ]; then
    rm -f "$AUTOSTART_FILE"
    echo "✔  Removed $AUTOSTART_FILE"
    echo ""
    echo "✅  Auto-start on boot is now DISABLED."
    echo "    The app will no longer open automatically when powered on."
    echo "    You can still open it anytime by double-clicking the Desktop icon."
else
    echo "✔  Auto-start was not enabled."
fi

echo "======================================================================"

