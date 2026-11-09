#!/usr/bin/env bash
# ==============================================================================
# build_raspberry_pi.sh
# Builds the standalone HologramDetector executable on Raspberry Pi.
# Run this ONCE on the Pi — output goes to  dist/HologramDetector/
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "================================================================"
echo "  AI Hologram Authenticity Detector — Raspberry Pi Builder"
echo "================================================================"
echo ""

# ── 1. Make sure pip / pyinstaller are available ──────────────────────────
echo "[1/5] Checking / installing dependencies..."
python3 -m pip install --upgrade pip --quiet
python3 -m pip install pyinstaller --quiet
python3 -m pip install \
    PyQt5 \
    opencv-python-headless \
    numpy \
    reportlab \
    --quiet || true   # non-fatal: picamera2 installed separately on Pi OS

# Picamera2 is pre-installed on Raspberry Pi OS — attempt install for completeness
python3 -m pip install picamera2 --quiet 2>/dev/null || true

echo "   ✔  Dependencies ready"
echo ""

# ── 2. Make sure hologram_core.py and styles.py are next to raspberry.py ──
echo "[2/5] Resolving source files..."
for f in hologram_core.py styles.py camera_manager.py report_generator.py; do
    if [ ! -f "$f" ]; then
        # Try SRC/ subfolder
        for src_dir in "SRC" "Counterfeit-Hologram-Detector-main/SRC"; do
            if [ -f "$src_dir/$f" ]; then
                cp "$src_dir/$f" "$f"
                echo "   Copied $src_dir/$f → $f"
                break
            fi
        done
    fi
done
echo "   ✔  Source files resolved"
echo ""

# ── 3. Build the executable with PyInstaller ──────────────────────────────
echo "[3/5] Running PyInstaller (this takes 2-5 minutes on Pi)..."
python3 -m PyInstaller raspberry_pi.spec --clean --noconfirm
echo "   ✔  Build complete → dist/HologramDetector/"
echo ""

# ── 4. Run the installer ──────────────────────────────────────────────────
echo "[4/5] Installing desktop launcher..."
bash install_raspberry_pi.sh
echo ""

echo "[5/5] Done!"
echo ""
echo "================================================================"
echo "  ✅ HologramDetector installed successfully!"
echo "     • Desktop icon:  ~/Desktop/HologramDetector.desktop"
echo "     • App directory: ~/HologramDetector/"
echo "     • Run manually:  ~/HologramDetector/HologramDetector"
echo "================================================================"

