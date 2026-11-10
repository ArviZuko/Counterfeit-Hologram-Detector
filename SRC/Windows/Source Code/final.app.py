"""
AI-Powered Hologram Authenticity Detection System
Main Application Launcher (Offline Desktop GUI & Web Dashboard)

Usage:
    python final.app.py         # Launches the Standalone Desktop GUI (Default, 100% Offline)
    python final.app.py --gui   # Explicit flag for Standalone Desktop GUI
    python final.app.py --web   # Launches the Web Application server on 0.0.0.0:5000
"""

import os
import sys
import argparse

# Resolve paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sub_root = os.path.join(BASE_DIR, "Counterfeit-Hologram-Detector-main")
src_candidates = [
    os.path.join(BASE_DIR, "SRC"),
    os.path.join(sub_root, "SRC"),
    BASE_DIR
]

for p in src_candidates:
    if os.path.exists(p) and p not in sys.path:
        sys.path.insert(0, p)


def main():
    parser = argparse.ArgumentParser(description="AI Hologram Authenticity Detection System")
    parser.add_argument("--web", action="store_true", help="Launch optional web server interface")
    parser.add_argument("--gui", action="store_true", help="Launch native Desktop GUI application")
    parser.add_argument("--rpi", "--raspberry", action="store_true", help="Launch dedicated Raspberry Pi application")
    parser.add_argument("--pitft", "--adafruit", "--touch", action="store_true", help="Launch in Adafruit 2.8\" Touchscreen mode (320x240)")
    parser.add_argument("--port", type=int, default=5000, help="Web server port (default: 5000)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Web server bind host (default: 0.0.0.0)")

    args, unknown = parser.parse_known_args()

    # Optional: Launch web server if explicitly requested via --web
    if args.web:
        try:
            from web_app import run_server
            run_server(host=args.host, port=args.port)
            return
        except Exception as e:
            print(f"[Error] Failed to start web server: {e}")
            print("[Info] Launching native Desktop Application instead...")

    # Explicit or auto-detected Raspberry Pi mode
    is_rpi = False
    try:
        from camera_manager import is_raspberry_pi
        is_rpi = is_raspberry_pi()
    except Exception:
        pass

    if args.pitft or args.rpi or is_rpi:
        try:
            from raspberry import main as run_rpi
            run_rpi()
            return
        except Exception as e:
            print(f"[Warning] Could not load raspberry.py: {e}. Falling back to default GUI...")

    # Default (or if --gui): Native Desktop Application (100% Offline & Static, No Online Server)
    from Final_app import main as run_gui
    run_gui()


if __name__ == "__main__":
    main()
