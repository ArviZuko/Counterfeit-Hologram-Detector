#!/usr/bin/env bash
# ==============================================================================
# install_raspberry_pi.sh
# Installs the HologramDetector app on Raspberry Pi desktop.
#
# After running this script the user can:
#   • Double-click the desktop icon to launch the app
#   • The app auto-detects display size (320x240 / 480x320 / 800x480 / HD)
#
# Usage:
#   bash install_raspberry_pi.sh           # install from dist/HologramDetector/
#   bash install_raspberry_pi.sh --uninstall   # remove app & desktop icon
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_NAME="HologramDetector"
INSTALL_DIR="$HOME/$APP_NAME"
DESKTOP_FILE="$HOME/Desktop/${APP_NAME}.desktop"
EXE_SRC="$SCRIPT_DIR/dist/$APP_NAME/$APP_NAME"
ICON_SRC="$SCRIPT_DIR/icon.png"

# ── Uninstall mode ────────────────────────────────────────────────────────
if [[ "$1" == "--uninstall" ]]; then
    echo "Removing $APP_NAME..."
    rm -f  "$DESKTOP_FILE"
    rm -f  "$HOME/.config/autostart/${APP_NAME}.desktop"
    rm -f  "$HOME/.local/share/applications/${APP_NAME}.desktop"
    rm -rf "$INSTALL_DIR"
    echo "✔  $APP_NAME uninstalled completely (Desktop icon & Autostart removed)."
    exit 0
fi

# ── Detect display size from framebuffer ─────────────────────────────────
DISPLAY_W=1920
DISPLAY_H=1080
for fb in /sys/class/graphics/fb1/virtual_size /sys/class/graphics/fb0/virtual_size; do
    if [ -f "$fb" ]; then
        IFS=',' read -r DISPLAY_W DISPLAY_H < "$fb"
        break
    fi
done
MIN_DIM=$(( DISPLAY_W < DISPLAY_H ? DISPLAY_W : DISPLAY_H ))

if   [ "$MIN_DIM" -le 240 ]; then SCREEN_CLASS="pitft_240"
elif [ "$MIN_DIM" -le 320 ]; then SCREEN_CLASS="small_320"
elif [ "$MIN_DIM" -le 480 ]; then SCREEN_CLASS="medium_480"
else                               SCREEN_CLASS="desktop"
fi

echo "Display detected: ${DISPLAY_W}x${DISPLAY_H}  (class: $SCREEN_CLASS)"

# ── Build extra launch args based on display class ────────────────────────
LAUNCH_ARGS=""
if [[ "$SCREEN_CLASS" == "pitft_240" || "$SCREEN_CLASS" == "small_320" ]]; then
    LAUNCH_ARGS="--pitft"
fi

# ── 1. Copy compiled app to home directory ────────────────────────────────
echo "Installing to $INSTALL_DIR ..."
mkdir -p "$INSTALL_DIR"

if [ -d "$SCRIPT_DIR/dist/$APP_NAME" ]; then
    # PyInstaller one-folder build is available — copy it
    cp -r "$SCRIPT_DIR/dist/$APP_NAME/." "$INSTALL_DIR/"
    EXEC_PATH="$INSTALL_DIR/$APP_NAME"
else
    # Fallback: install Python source directly (no compiled exe)
    echo "[Info] Compiled executable not found — installing Python source instead."
    EXEC_PATH="/usr/bin/python3 $INSTALL_DIR/raspberry.py"
    cp "$SCRIPT_DIR/raspberry.py"       "$INSTALL_DIR/"
    cp "$SCRIPT_DIR/styles.py"          "$INSTALL_DIR/" 2>/dev/null || true
    # Copy hologram_core from SRC/ if needed
    for f in hologram_core.py camera_manager.py report_generator.py; do
        if [ -f "$SCRIPT_DIR/$f" ]; then
            cp "$SCRIPT_DIR/$f" "$INSTALL_DIR/"
        elif [ -f "$SCRIPT_DIR/SRC/$f" ]; then
            cp "$SCRIPT_DIR/SRC/$f" "$INSTALL_DIR/"
        elif [ -f "$SCRIPT_DIR/Counterfeit-Hologram-Detector-main/SRC/$f" ]; then
            cp "$SCRIPT_DIR/Counterfeit-Hologram-Detector-main/SRC/$f" "$INSTALL_DIR/"
        fi
    done
    # Copy data assets
    for asset in weight.npz Template.png icon.png cr_weights; do
        [ -e "$SCRIPT_DIR/$asset" ] && cp -r "$SCRIPT_DIR/$asset" "$INSTALL_DIR/"
    done
fi

# Copy icon
[ -f "$ICON_SRC" ] && cp "$ICON_SRC" "$INSTALL_DIR/icon.png"

chmod +x "$INSTALL_DIR/$APP_NAME" 2>/dev/null || true

echo "✔  App files installed."

# ── 2. Create wrapper launch script (sets env vars before starting) ───────
WRAPPER="$INSTALL_DIR/launch.sh"
cat > "$WRAPPER" <<WRAPPER_EOF
#!/usr/bin/env bash
# Auto-generated launcher for HologramDetector — do not edit manually

# Settle display and camera hardware during early system boot
sleep 2

# Dynamically re-check display size at launch time
if [ -f /sys/class/graphics/fb1/virtual_size ]; then
    IFS=',' read -r CURR_W CURR_H < /sys/class/graphics/fb1/virtual_size
    export DISPLAY_WIDTH=\$CURR_W
    export DISPLAY_HEIGHT=\$CURR_H
elif [ -f /sys/class/graphics/fb0/virtual_size ]; then
    IFS=',' read -r CURR_W CURR_H < /sys/class/graphics/fb0/virtual_size
    export DISPLAY_WIDTH=\$CURR_W
    export DISPLAY_HEIGHT=\$CURR_H
else
    export DISPLAY_WIDTH=$DISPLAY_W
    export DISPLAY_HEIGHT=$DISPLAY_H
fi

# Ensure GUI display variable exists
if [ -z "\$DISPLAY" ] && [ -z "\$WAYLAND_DISPLAY" ]; then
    export DISPLAY=:0
fi

# Prevent screen sleep / blanking during operation
if command -v xset &>/dev/null && [ -n "\$DISPLAY" ]; then
    xset s off -dpms s noblank 2>/dev/null || true
fi

export QT_QPA_PLATFORM=xcb
export LIBGL_ALWAYS_SOFTWARE=1
export AUTOSTART_CAMERA=1

# On headless PiTFT without active X11, use Linux framebuffer platform directly
if [ -e /dev/fb1 ]; then
    if ! command -v xset &>/dev/null || ! xset q &>/dev/null; then
        export QT_QPA_PLATFORM=linuxfb:fb=/dev/fb1
        export TSLIB_TSDEVICE=/dev/input/touchscreen0
    fi
fi

cd "$INSTALL_DIR"
WRAPPER_EOF

if [ -f "$INSTALL_DIR/$APP_NAME" ]; then
    echo "\"$INSTALL_DIR/$APP_NAME\" $LAUNCH_ARGS --auto-camera \"\$@\"" >> "$WRAPPER"
else
    echo "/usr/bin/python3 \"$INSTALL_DIR/raspberry.py\" $LAUNCH_ARGS --auto-camera \"\$@\"" >> "$WRAPPER"
fi
chmod +x "$WRAPPER"
echo "✔  Launcher script created: $WRAPPER"

# ── 3. Create .desktop file (double-click icon on Pi desktop & Autostart) ──
mkdir -p "$HOME/Desktop"
mkdir -p "$HOME/.config/autostart"

ICON_PATH="$INSTALL_DIR/icon.png"
[ ! -f "$ICON_PATH" ] && ICON_PATH="utilities-system-monitor"  # fallback system icon

cat > "$DESKTOP_FILE" <<DESKTOP_EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Hologram Detector
Comment=AI-Powered Hologram Authenticity Verification System
Exec=bash "$WRAPPER"
Icon=$ICON_PATH
Terminal=false
Categories=Science;Education;
StartupNotify=true
X-GNOME-Autostart-enabled=true
DESKTOP_EOF

chmod +x "$DESKTOP_FILE"

# Make Pi OS trust the desktop file (required on Raspberry Pi OS Bookworm)
if command -v gio &>/dev/null; then
    gio set "$DESKTOP_FILE" "metadata::trusted" true 2>/dev/null || true
fi

echo "✔  Desktop icon created: $DESKTOP_FILE"

# ── 4. Enable Auto-Start on Boot (Plug-and-Play Kiosk Mode) ────────────────
AUTOSTART_FILE="$HOME/.config/autostart/HologramDetector.desktop"
cp "$DESKTOP_FILE" "$AUTOSTART_FILE"
chmod +x "$AUTOSTART_FILE"
echo "✔  Auto-start on boot ENABLED ($AUTOSTART_FILE)"

# ── 5. Also add to applications menu ─────────────────────────────────────
APP_MENU_DIR="$HOME/.local/share/applications"
mkdir -p "$APP_MENU_DIR"
cp "$DESKTOP_FILE" "$APP_MENU_DIR/${APP_NAME}.desktop"
echo "✔  Applications menu entry added."

# ── 6. Summary ────────────────────────────────────────────────────────────
echo ""
echo "================================================================"
echo "  ✅  Hologram Detector installed successfully!"
echo ""
echo "  Display     : ${DISPLAY_W}x${DISPLAY_H}  →  $SCREEN_CLASS layout"
echo "  App dir     : $INSTALL_DIR"
echo "  Desktop     : $DESKTOP_FILE"
echo "  Boot Launch : ENABLED (App will automatically open when plugged in!)"
echo ""
echo "  🔌 PLUG & PLAY READY:"
echo "     Whenever you power on or plug in your Raspberry Pi,"
echo "     the Hologram Detector will launch automatically!"
echo "================================================================"

