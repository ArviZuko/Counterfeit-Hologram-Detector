#!/bin/bash
# ==============================================================================
# AI-Powered Hologram Authenticity Detection System
# Raspberry Pi Automated Installation & Launch Script
# Supports: Raspberry Pi 3, 4, 5, Zero 2W (32-bit & 64-bit, Bullseye & Bookworm)
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Text Styling
BOLD='\033[1m'
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${CYAN}${BOLD}"
echo "======================================================================"
echo "    AI-POWERED HOLOGRAM AUTHENTICITY VERIFICATION SYSTEM"
echo "               Raspberry Pi Deployment Engine"
echo "======================================================================"
echo -e "${NC}"

# Parse Command Line Options
MODE="web"
PORT="5000"
SETUP_ONLY=false

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --pitft|--adafruit|--touch) MODE="pitft" ;;
        --gui|--desktop) MODE="gui" ;;
        --web) MODE="web" ;;
        --port) PORT="$2"; shift ;;
        --setup-only) SETUP_ONLY=true ;;
        --help|-h)
            echo "Usage: ./setup_and_run_raspberry.sh [OPTIONS]"
            echo "Options:"
            echo "  --pitft         Launch in Adafruit 2.8\" Touchscreen mode (320x240)"
            echo "  --web           Launch in formal Web Application mode (Default, accessible over WiFi)"
            echo "  --gui           Launch in Desktop GUI mode (Requires HDMI monitor & desktop environment)"
            echo "  --port <port>   Set web server port (Default: 5000)"
            echo "  --setup-only    Install all dependencies without starting the application"
            echo "  --help, -h      Show this help message"
            exit 0
            ;;
        *) echo -e "${YELLOW}Unknown option: $1 (ignoring)${NC}" ;;
    esac
    shift
done

echo -e "${BOLD}[1/4] Checking System & Architecture...${NC}"
ARCH=$(uname -m)
OS_INFO=$(cat /etc/os-release | grep PRETTY_NAME | cut -d= -f2 | tr -d '"')
echo "  * Architecture: $ARCH"
echo "  * Operating System: $OS_INFO"

# Add current user to video and render groups for camera hardware acceleration
CURRENT_USER=$(whoami)
echo "  * Configuring camera hardware permissions for user '$CURRENT_USER'..."
if groups "$CURRENT_USER" | grep &>/dev/null '\bvideo\b'; then
    echo "    - User is already in 'video' group."
else
    echo "    - Adding user to 'video' group..."
    sudo usermod -a -G video "$CURRENT_USER" 2>/dev/null || true
fi

if groups "$CURRENT_USER" | grep &>/dev/null '\brender\b'; then
    echo "    - User is already in 'render' group."
else
    sudo usermod -a -G render "$CURRENT_USER" 2>/dev/null || true
fi

echo -e "\n${BOLD}[2/4] Verifying and Installing Raspberry Pi Dependencies...${NC}"

# Check for apt-get
if command -v apt-get &> /dev/null; then
    MISSING_PKGS=()
    for pkg in python3-pip python3-numpy python3-scipy python3-opencv python3-flask python3-pil python3-reportlab libcamera-apps v4l-utils; do
        if ! dpkg -s "$pkg" &> /dev/null; then
            MISSING_PKGS+=("$pkg")
        fi
    done

    # Check for Picamera2 on Raspberry Pi OS Bookworm / Bullseye
    if ! dpkg -s "python3-picamera2" &> /dev/null; then
        MISSING_PKGS+=("python3-picamera2")
    fi

    if [ ${#MISSING_PKGS[@]} -gt 0 ]; then
        echo -e "${YELLOW}  * Missing system packages detected: ${MISSING_PKGS[*]}${NC}"
        echo "  * Installing required packages via apt (this may take a few moments)..."
        sudo apt-get update -y
        sudo apt-get install -y --no-install-recommends "${MISSING_PKGS[@]}" || {
            echo -e "${YELLOW}[Warning] Some packages could not be installed via apt. Falling back to pip...${NC}"
        }
    else
        echo -e "${GREEN}  * All system packages are already installed.${NC}"
    fi
fi

# Install Python requirements via pip if needed
echo "  * Verifying Python libraries..."
python3 -c "import cv2, numpy, flask, reportlab" &> /dev/null || {
    echo "  * Installing remaining Python requirements..."
    pip3 install -r requirements.txt --break-system-packages 2>/dev/null || pip3 install -r requirements.txt || true
}

echo -e "\n${BOLD}[3/4] Probing Raspberry Pi Camera System...${NC}"
# Check for libcamera / CSI camera
if command -v libcamera-hello &> /dev/null; then
    echo "  * libcamera is available."
fi

# List video devices
if [ -e /dev/video0 ]; then
    echo -e "${GREEN}  * Hardware camera detected at /dev/video0${NC}"
else
    echo -e "${YELLOW}  * Note: No /dev/video0 detected yet. CSI camera (Picamera2) or WiFi camera will be used.${NC}"
fi

# Detect Local Network IP Addresses (WiFi / Ethernet)
IP_ADDRS=($(hostname -I 2>/dev/null || true))
PRIMARY_IP="${IP_ADDRS[0]:-127.0.0.1}"

echo -e "\n${BOLD}[4/4] Network & Camera Configuration Complete!${NC}"
echo -e "${CYAN}======================================================================${NC}"
echo -e "${BOLD}SYSTEM ACCESS ADDRESSES (Connect your Laptop/Phone to the same WiFi):${NC}"
echo -e "  * ${GREEN}WiFi / Network URL: http://${PRIMARY_IP}:${PORT}${NC}"
for ip in "${IP_ADDRS[@]:1}"; do
    echo -e "  * Secondary IP URL:  http://${ip}:${PORT}"
done
echo -e "  * Localhost URL:     http://localhost:${PORT}"
echo -e "${CYAN}======================================================================${NC}"
echo "  - Open the WiFi URL on your laptop's browser to access the system!"
echo "  - Stream live video from the Raspberry Pi camera over WiFi."
echo "  - Or connect any external WiFi/IP camera directly in the dashboard."
echo -e "${CYAN}======================================================================${NC}\n"

if [ "$SETUP_ONLY" = true ]; then
    echo -e "${GREEN}Setup completed successfully. Exiting (--setup-only).${NC}"
    exit 0
fi

# Determine python file to launch
LAUNCH_FILE="raspberry.py"
if [ ! -f "$LAUNCH_FILE" ]; then
    if [ -f "Counterfeit-Hologram-Detector-main/raspberry.py" ]; then
        LAUNCH_FILE="Counterfeit-Hologram-Detector-main/raspberry.py"
    else
        LAUNCH_FILE="final.app.py"
    fi
fi

if [ "$MODE" = "pitft" ]; then
    echo -e "${BOLD}Launching Adafruit 2.8\" PiTFT Touchscreen Interface (320x240)...${NC}"
    export QT_SCALE_FACTOR=1
    export QT_AUTO_SCREEN_SCALE_FACTOR=0
    # Framebuffer setup for direct PiTFT execution
    if [ -e /dev/fb1 ] && [ -z "$DISPLAY" ]; then
        echo "  * Direct framebuffer output to /dev/fb1"
        export QT_QPA_PLATFORM="linuxfb:fb=/dev/fb1"
        if [ -e /dev/input/touchscreen ]; then
            export QT_QPA_EVDEV_TOUCHSCREEN_PARAMETERS="/dev/input/touchscreen:rotate=90"
        fi
    fi
    if [ -f "$LAUNCH_FILE" ]; then
        python3 "$LAUNCH_FILE" --pitft
    else
        python3 final.app.py --rpi --pitft
    fi
elif [ "$MODE" = "gui" ]; then
    echo -e "${BOLD}Launching Desktop Qt Application on Raspberry Pi screen...${NC}"
    if [ -f "$LAUNCH_FILE" ]; then
        python3 "$LAUNCH_FILE"
    else
        python3 final.app.py --rpi
    fi
else
    echo -e "${BOLD}Starting Formal Web Server on 0.0.0.0:${PORT}...${NC}"
    python3 final.app.py --web --port "$PORT"
fi
