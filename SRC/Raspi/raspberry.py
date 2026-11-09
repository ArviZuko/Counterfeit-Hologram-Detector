#!/usr/bin/env python3
"""
==============================================================================
AI-Powered Hologram Authenticity Detection System
Raspberry Pi & Desktop Standalone Edition (raspberry.py)
==============================================================================
Production Security Inspection System:
- Clean Executive White Interface (with 1-click Dark Theme Switcher)
- Rock-Solid Screen Stability:
    * Zero layout jitter / zero window oscillation during live camera streaming
    * Fixed viewport size policies prevent pixmap sizeHint feedback loops
- Hardware Camera Operations:
    * "▶ Start Camera" immediately begins live acquisition (Pi Camera Module / USB / Network)
    * "⏹ Stop Camera" cleanly releases hardware resources
    * "📸 Capture Snapshot" freezes current specimen and saves Capture.png
    * "📂 Load Image" allows loading test specimens from disk
- 100% Autonomous Spectral & Optical Gain Calibration:
    * Wavelength automatically calibrated to 500 nm VIS-HSI band (Mukundan et al.)
    * Optical Gain dynamically calibrated per hologram based on real-time exposure
- Exactly TWO Visual Verification Panels:
    1. Live Acquisition Specimen (ROI): Camera frame with detected hologram bounding box
    2. Extracted Specimen Hologram Feature: Cropped security hologram from the specimen
- Standard Certified Outcomes:
    * THE HOLOGRAM IS ORIGINAL (High-visibility emerald green)
    * THE HOLOGRAM IS COUNTERFEIT (High-visibility crimson red)
    * NO HOLOGRAM DETECTED (Amber alignment notice)
- Instant Formal PDF Inspection Certificate (ReportLab)
==============================================================================
"""

import os
import sys
import time
import datetime
import threading
import numpy as np
from numpy.linalg import inv, pinv
import cv2

# Optional ReportLab for PDF Certificate Generation
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, HRFlowable
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

# PyQt5 GUI Framework
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtGui import QPixmap, QImage, QColor, QFont, QIcon, QPainter, QPen
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot, QThread
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QComboBox,
    QFileDialog, QMessageBox, QFrame, QCheckBox, QSizePolicy, QInputDialog,
    QTabWidget
)


# ============================================================================
# Resource Path Resolver
# ============================================================================

def resolve_resource(relative_path):
    """Locates asset files across root, SRC, and parent directories."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(script_dir, relative_path),
        os.path.join(script_dir, "SRC", relative_path),
        os.path.join(script_dir, "Counterfeit-Hologram-Detector-main", relative_path),
        os.path.join(script_dir, "Counterfeit-Hologram-Detector-main", "SRC", relative_path),
        os.path.abspath(relative_path)
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return os.path.join(script_dir, relative_path)


# Ensure SRC directories are in sys.path
for p in [os.path.dirname(os.path.abspath(__file__)),
          os.path.join(os.path.dirname(os.path.abspath(__file__)), "SRC"),
          os.path.join(os.path.dirname(os.path.abspath(__file__)), "Counterfeit-Hologram-Detector-main", "SRC")]:
    if os.path.exists(p) and p not in sys.path:
        sys.path.insert(0, p)

from hologram_core import SpectrumTransfer, ColorReproducer, FastHologramPipeline, HologramAnalyzer
from styles import LIGHT_THEME_QSS, MODERN_CYBER_DARK_QSS, PITFT_LIGHT_QSS, PITFT_DARK_QSS


# ============================================================================
# Platform & Hardware Detection
# ============================================================================

def is_raspberry_pi():
    """Detects if running on Raspberry Pi hardware."""
    try:
        if os.path.exists('/proc/device-tree/model'):
            with open('/proc/device-tree/model', 'r') as f:
                model = f.read().lower()
                return 'raspberry pi' in model
    except Exception:
        pass
    return sys.platform.startswith('linux') and ('arm' in os.uname().machine.lower() or 'aarch64' in os.uname().machine.lower())


# ============================================================================
# Universal Hardware Camera Acquisition Worker
# ============================================================================

class RaspberryCameraWorker(QThread):
    """
    Non-blocking, thread-safe hardware camera acquisition thread.
    Emits frames via Qt signals to prevent GUI lockups on Raspberry Pi Linux.
    """
    frame_ready = pyqtSignal(np.ndarray)
    fps_updated = pyqtSignal(float)
    status_changed = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self._running = False
        self.lock = threading.Lock()
        self.latest_frame = None

        self.source_type = "hardware"   # "picamera", "hardware", "network", "image"
        self.device_index = 0
        self.stream_url = ""
        self.static_image = None
        self.picam_instance = None
        self.fps = 0.0

    def set_hardware_camera(self, device_index=0):
        self.stop_capture()
        self.source_type = "hardware"
        self.device_index = int(device_index)

    def set_picamera(self):
        self.stop_capture()
        self.source_type = "picamera"

    def set_network_stream(self, url):
        self.stop_capture()
        self.source_type = "network"
        self.stream_url = url.strip()

    def set_static_image(self, img_or_path):
        self.stop_capture()
        self.source_type = "image"
        if isinstance(img_or_path, str):
            self.static_image = cv2.imread(img_or_path)
        else:
            self.static_image = img_or_path

    def stop_capture(self):
        self._running = False
        if self.isRunning():
            self.wait(1200)
        if self.picam_instance is not None:
            try:
                self.picam_instance.stop()
                self.picam_instance.close()
            except Exception:
                pass
            self.picam_instance = None
        self.status_changed.emit("Camera Standby", "#64748b")

    def run(self):
        self._running = True

        if self.source_type == "picamera":
            self._loop_picamera()
        elif self.source_type == "image":
            self._loop_image()
        else:
            self._loop_cv_capture()

    def _loop_picamera(self):
        try:
            from picamera2 import Picamera2
            self.status_changed.emit("Starting Pi Camera (Picamera2)...", "#2563eb")
            self.picam_instance = Picamera2()
            config = self.picam_instance.create_video_configuration(main={"size": (1280, 720), "format": "BGR888"})
            self.picam_instance.configure(config)
            self.picam_instance.start()
            self.status_changed.emit("Raspberry Pi Camera Live", "#059669")
        except Exception as e:
            self.status_changed.emit(f"Picamera2 init: {e}. Trying V4L2...", "#d97706")
            self.source_type = "hardware"
            self.device_index = 0
            self._loop_cv_capture()
            return

        last_time = time.time()
        while self._running:
            try:
                frame = self.picam_instance.capture_array()
                with self.lock:
                    self.latest_frame = frame
                self.frame_ready.emit(frame)

                now = time.time()
                dt = now - last_time
                last_time = now
                if dt > 0:
                    self.fps = round(1.0 / dt, 1)
                    self.fps_updated.emit(self.fps)
                time.sleep(0.01)
            except Exception:
                time.sleep(0.05)

    def _loop_cv_capture(self):
        cap = None
        is_windows = sys.platform.startswith('win')
        is_linux = sys.platform.startswith('linux')

        if self.source_type == "hardware":
            self.status_changed.emit(f"Opening Camera {self.device_index}...", "#2563eb")
            backends = []
            if is_linux:
                backends = [(cv2.CAP_V4L2, 'V4L2'), (cv2.CAP_ANY, 'Default')]
            elif is_windows:
                backends = [(cv2.CAP_MSMF, 'MSMF'), (cv2.CAP_DSHOW, 'DirectShow'), (cv2.CAP_ANY, 'Default')]
            else:
                backends = [(cv2.CAP_ANY, 'Default')]

            for b_flag, b_name in backends:
                try:
                    test_cap = cv2.VideoCapture(self.device_index, b_flag)
                    if test_cap.isOpened():
                        for _ in range(3):
                            ret, frame = test_cap.read()
                            if ret and frame is not None and np.mean(frame) > 0.1:
                                cap = test_cap
                                break
                        if cap is not None:
                            break
                        test_cap.release()
                except Exception:
                    pass

            if cap is None:
                try:
                    cap = cv2.VideoCapture(self.device_index)
                except Exception:
                    cap = None
        else:
            # Network RTSP / HTTP stream
            self.status_changed.emit("Connecting to Network Stream...", "#2563eb")
            cap = cv2.VideoCapture(self.stream_url)

        if cap is None or not cap.isOpened():
            target = f"Camera {self.device_index}" if self.source_type == "hardware" else self.stream_url
            self.status_changed.emit(f"Camera Device Unavailable: {target}", "#dc2626")
            self._running = False
            return

        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.status_changed.emit(f"Camera Live ({w}x{h})", "#059669")

        last_time = time.time()
        while self._running:
            ret, frame = cap.read()
            if not ret or frame is None:
                time.sleep(0.02)
                continue

            with self.lock:
                self.latest_frame = frame
            self.frame_ready.emit(frame)

            now = time.time()
            dt = now - last_time
            last_time = now
            if dt > 0:
                self.fps = round(1.0 / dt, 1)
                self.fps_updated.emit(self.fps)

            time.sleep(0.005)

        cap.release()
        self.status_changed.emit("Camera Standby", "#64748b")

    def _loop_image(self):
        if self.static_image is None:
            return
        self.status_changed.emit("Hologram Specimen Image Loaded", "#2563eb")
        while self._running:
            with self.lock:
                self.latest_frame = self.static_image
            self.frame_ready.emit(self.static_image)
            time.sleep(0.1)


# ============================================================================
# Camera Device Enumeration
# ============================================================================

def list_system_cameras():
    """Detects physical camera hardware across Raspberry Pi, Linux, and Windows."""
    devices = []
    is_rpi = is_raspberry_pi()

    if is_rpi:
        try:
            import picamera2
            devices.append({"id": "picamera", "name": "Raspberry Pi Camera Module (Picamera2 / libcamera)", "type": "picamera"})
        except Exception:
            pass

    # Probe hardware devices 0, 1, 2
    for idx in range(3):
        cap = None
        try:
            backend = cv2.CAP_V4L2 if sys.platform.startswith('linux') else cv2.CAP_ANY
            cap = cv2.VideoCapture(idx, backend)
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    label = f"Camera {idx} (USB / Hardware - {w}x{h})" if not is_rpi else f"Camera {idx} (/dev/video{idx})"
                    devices.append({"id": idx, "name": label, "type": "hardware"})
            cap.release()
        except Exception:
            if cap:
                try: cap.release()
                except: pass

    # WiFi / Network IP camera option
    devices.append({"id": "network", "name": "WiFi / Network Camera (RTSP / HTTP Stream)", "type": "network"})
    return devices


# ============================================================================
# Main Modern Desktop Application (Raspberry Pi & Desktop)
# ============================================================================

class RaspberryHologramApp(QMainWindow):
    """
    Sleek, high-contrast, clean White Desktop UI for Hologram Authenticity Verification.
    Optimized for Raspberry Pi 3/4/5 HDMI screens and touch displays.
    Features 100% rock-solid layout with zero jitter during live camera streaming.
    """
    def __init__(self, pitft_mode=None):
        super().__init__()
        self.setWindowTitle("AI Hologram Authenticity Detector • Raspberry Pi Edition")

        # ── Auto-detect display size and pick the best layout ──────────────────
        # Priority order:
        #   1. Explicit pitft_mode= argument passed by caller
        #   2. CLI flag (--pitft / --adafruit / --touch / --small-screen)
        #   3. Environment variable  PITFT_MODE=1
        #   4. Real screen geometry auto-detected at runtime
        if pitft_mode is not None:
            self.pitft_mode = bool(pitft_mode)
        else:
            cli_pitft = any(arg in sys.argv for arg in ["--pitft", "--adafruit", "--small-screen", "--touch"])
            env_pitft = os.environ.get("PITFT_MODE", "").lower() in ("1", "true", "yes")

            # ── Runtime screen-size auto-detection ─────────────────────────────
            screen = QApplication.primaryScreen()
            sw, sh = 1920, 1080  # sane defaults if screen query fails
            if screen is not None:
                geom = screen.geometry()
                sw, sh = geom.width(), geom.height()

            # Classify by the SMALLEST dimension so portrait & landscape both work
            min_dim = min(sw, sh)
            if min_dim <= 240:
                # Adafruit 2.8" PiTFT  320×240  (or 240×320 portrait)
                self._display_class = "pitft_240"
            elif min_dim <= 320:
                # Small embedded displays  480×320 etc.
                self._display_class = "small_320"
            elif min_dim <= 480:
                # Medium 800×480  Raspberry Pi Official 7"
                self._display_class = "medium_480"
            else:
                # Full HD desktop / HDMI monitor
                self._display_class = "desktop"

            screen_is_small = (self._display_class in ("pitft_240", "small_320"))
            self.pitft_mode = cli_pitft or env_pitft or screen_is_small

        # ── Window geometry based on detected display class ─────────────────
        if self.pitft_mode:
            screen = QApplication.primaryScreen()
            if screen is not None:
                geom = screen.geometry()
                sw, sh = geom.width(), geom.height()
            else:
                sw, sh = 320, 240
            # Clamp to actual screen size
            win_w = min(sw, 320)
            win_h = min(sh, 240)
            print(f"[Info] Small-screen mode active — display {sw}×{sh}, "
                  f"window {win_w}×{win_h}")
            self.resize(win_w, win_h)
            self.setMinimumSize(win_w, win_h)
            if is_raspberry_pi() and not any(arg in sys.argv for arg in ["--windowed", "--no-fullscreen"]):
                self.showFullScreen()
        elif hasattr(self, '_display_class') and self._display_class == "medium_480":
            # 7" official Pi display — 800×480
            self.resize(800, 460)
            self.setMinimumSize(640, 400)
        else:
            self.resize(1260, 780)
            self.setMinimumSize(800, 560)

        # Theme Tracking: default to White Theme
        self.current_theme = "light"

        # Set Window Icon
        icon_path = resolve_resource("icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # Core State
        self.camera_worker = RaspberryCameraWorker()
        self.current_frame = None
        self.last_analysis_result = None
        self.show_reticle = True

        # Load Hyperspectral Core Models
        self.transfer = SpectrumTransfer()
        weight_path = resolve_resource("weight.npz")
        if os.path.exists(weight_path):
            self.transfer.load(weight_path)
        else:
            print(f"[Warning] weight.npz not found at: {weight_path}")

        self.reproducer = ColorReproducer()
        cr_path = resolve_resource("cr_weights")
        if os.path.exists(cr_path):
            self.reproducer.load(cr_path)
        else:
            print(f"[Warning] cr_weights folder not found at: {cr_path}")

        template_path = resolve_resource("Template.png")
        self.fast_pipeline = FastHologramPipeline(self.transfer, self.reproducer)
        self.analyzer = HologramAnalyzer(template_path)
        self.master_template = self.analyzer.template_bgr

        # Build Interface
        self._init_ui()

        # Connect Worker Signals
        self.camera_worker.frame_ready.connect(self.on_frame_received)
        self.camera_worker.fps_updated.connect(self.on_fps_updated)
        self.camera_worker.status_changed.connect(self.on_camera_status)

        # Populate camera list
        self.refresh_cameras()

    # ------------------------------------------------------------------------
    # UI Layout Construction (Adaptive Desktop & Adafruit 2.8" PiTFT Touch)
    # ------------------------------------------------------------------------

    def _init_ui(self):
        if self.pitft_mode:
            self._init_pitft_ui()
        else:
            self._init_desktop_ui()

        # Status Bar Handling
        self.status_bar = self.statusBar()
        if not self.pitft_mode:
            arch_info = "Raspberry Pi ARM" if is_raspberry_pi() else "Desktop PC"
            self.status_bar.showMessage(f"System Ready • Architecture: {arch_info} • VIS-HSI Hyperspectral 401-Band Engine Calibrated")
        else:
            # On 320x240 screen, hide status bar to maximize touch viewport area
            self.status_bar.hide()

    def _init_desktop_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(14, 12, 14, 12)
        main_layout.setSpacing(10)

        # 1. Header Bar
        main_layout.addWidget(self._create_header_bar())

        # 2. Fixed Workspace Two-Column Layout (Equal stretch 1:1, non-shifting)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(12)

        # Left Column: Camera Feed & Acquisition Controls
        left_panel = self._create_camera_panel()
        content_layout.addWidget(left_panel, 1)

        # Right Column: Autonomous Calibration, Verification & Visual Matrix
        right_panel = self._create_analysis_panel()
        content_layout.addWidget(right_panel, 1)

        main_layout.addLayout(content_layout)

    def _init_pitft_ui(self):
        """Ultra-compact 3-tab layout specifically crafted for 320x240 Adafruit displays."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(2)

        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)

        # 1. Camera & Acquisition Tab
        tab_cam = self._create_pitft_camera_tab()
        self.tab_widget.addTab(tab_cam, "📷 Camera")

        # 2. Inspection & Verification Tab
        tab_verify = self._create_pitft_verify_tab()
        self.tab_widget.addTab(tab_verify, "⚡ Verify")

        # 3. Visual Evidence Matrix Tab
        tab_ev = self._create_pitft_evidence_tab()
        self.tab_widget.addTab(tab_ev, "🖼 Evidence")

        main_layout.addWidget(self.tab_widget)

    def _create_pitft_camera_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(3)

        top_row = QHBoxLayout()
        top_row.setSpacing(3)

        self.combo_cameras = QComboBox()
        self.combo_cameras.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.combo_cameras.currentIndexChanged.connect(self.on_camera_selected)
        top_row.addWidget(self.combo_cameras, stretch=2)

        btn_refresh = QPushButton("⟳")
        btn_refresh.setToolTip("Scan / Refresh Cameras")
        btn_refresh.setFixedWidth(24)
        btn_refresh.clicked.connect(self.refresh_cameras)
        top_row.addWidget(btn_refresh)

        btn_ip = QPushButton("🌐")
        btn_ip.setToolTip("WiFi / IP Camera Stream")
        btn_ip.setFixedWidth(24)
        btn_ip.clicked.connect(self.configure_ip_stream)
        top_row.addWidget(btn_ip)

        self.btn_start = QPushButton("▶ Start")
        self.btn_start.setObjectName("btnStartCam")
        self.btn_start.clicked.connect(self.start_camera)
        top_row.addWidget(self.btn_start, stretch=1)

        self.btn_stop = QPushButton("⏹")
        self.btn_stop.setObjectName("btnStopCam")
        self.btn_stop.setFixedWidth(26)
        self.btn_stop.clicked.connect(self.stop_camera)
        self.btn_stop.setEnabled(False)
        top_row.addWidget(self.btn_stop)

        self.btn_capture = QPushButton("📸 Snap")
        self.btn_capture.setObjectName("btnCapture")
        self.btn_capture.clicked.connect(self.capture_snapshot_pitft)
        top_row.addWidget(self.btn_capture, stretch=1)

        layout.addLayout(top_row)

        # Viewport Container
        self.viewport_container = QFrame()
        self.viewport_container.setObjectName("previewFrame")
        self.viewport_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        v_vp = QVBoxLayout(self.viewport_container)
        v_vp.setContentsMargins(1, 1, 1, 1)

        self.lbl_viewport = QLabel()
        self.lbl_viewport.setAlignment(Qt.AlignCenter)
        self.lbl_viewport.setStyleSheet(
            "background-color: #020617; border-radius: 4px; color: #94a3b8; font-size: 10px;"
        )
        self.lbl_viewport.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.lbl_viewport.setScaledContents(False)
        self.lbl_viewport.setText("Tap '▶ Start' to launch live camera stream")
        v_vp.addWidget(self.lbl_viewport)
        layout.addWidget(self.viewport_container, stretch=1)

        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(4)

        self.btn_load_file = QPushButton("📂 File")
        self.btn_load_file.clicked.connect(self.load_image_file)
        bottom_row.addWidget(self.btn_load_file)

        self.chk_reticle = QCheckBox("Reticle")
        self.chk_reticle.setChecked(True)
        self.chk_reticle.toggled.connect(self.on_toggle_reticle)
        bottom_row.addWidget(self.chk_reticle)

        bottom_row.addStretch()

        self.lbl_feed_info = QLabel("Standby • 0.0 FPS")
        self.lbl_feed_info.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.lbl_feed_info.setStyleSheet("color: #64748b; font-size: 9px;")
        bottom_row.addWidget(self.lbl_feed_info)

        layout.addLayout(bottom_row)
        return tab

    def _create_pitft_verify_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(3)

        top_row = QHBoxLayout()
        top_row.setSpacing(2)
        self.lbl_calib_status = QLabel("⚡ Auto: 500nm VIS-HSI • Dynamic Exposure")
        self.lbl_calib_status.setStyleSheet("font-size: 9px; color: #2563eb; font-weight: 700;")
        top_row.addWidget(self.lbl_calib_status, stretch=1)

        self.btn_theme_toggle = QPushButton("☀️")
        self.btn_theme_toggle.setObjectName("btnTheme")
        self.btn_theme_toggle.setFixedSize(24, 22)
        self.btn_theme_toggle.setToolTip("Toggle White / Dark Theme")
        self.btn_theme_toggle.clicked.connect(self.toggle_theme)
        top_row.addWidget(self.btn_theme_toggle)
        layout.addLayout(top_row)

        self.btn_verify = QPushButton("⚡ VERIFY HOLOGRAM AUTHENTICITY")
        self.btn_verify.setObjectName("btnAnalyze")
        self.btn_verify.setFixedHeight(34)
        self.btn_verify.clicked.connect(self.run_verification)
        layout.addWidget(self.btn_verify)

        self.banner_frame = QFrame()
        self.banner_frame.setStyleSheet(
            "background-color: #f8fafc; border-radius: 6px; border: 2px solid #cbd5e1; padding: 4px;"
        )
        v_banner = QVBoxLayout(self.banner_frame)
        v_banner.setContentsMargins(6, 4, 6, 4)
        v_banner.setSpacing(2)

        self.lbl_verdict_badge = QLabel("AWAITING SPECIMEN INSPECTION")
        self.lbl_verdict_badge.setStyleSheet("font-size: 13px; font-weight: 800; color: #64748b;")
        self.lbl_verdict_badge.setAlignment(Qt.AlignCenter)
        v_banner.addWidget(self.lbl_verdict_badge)

        self.lbl_verdict_detail = QLabel("Snap hologram in Camera tab and tap 'Verify'.")
        self.lbl_verdict_detail.setStyleSheet("font-size: 9px; color: #64748b;")
        self.lbl_verdict_detail.setWordWrap(True)
        self.lbl_verdict_detail.setAlignment(Qt.AlignCenter)
        v_banner.addWidget(self.lbl_verdict_detail)

        layout.addWidget(self.banner_frame, stretch=1)

        act_row = QHBoxLayout()
        act_row.setSpacing(4)

        self.btn_export_pdf = QPushButton("📄 PDF Cert")
        self.btn_export_pdf.setObjectName("btnPrimary")
        self.btn_export_pdf.clicked.connect(self.export_pdf_certificate)
        act_row.addWidget(self.btn_export_pdf)

        btn_view_ev = QPushButton("🖼 Visuals")
        btn_view_ev.clicked.connect(lambda: self.tab_widget.setCurrentIndex(2))
        act_row.addWidget(btn_view_ev)

        self.lbl_status_pill = QLabel("● READY")
        self._update_status_pill_style("ready")
        act_row.addWidget(self.lbl_status_pill)

        layout.addLayout(act_row)
        return tab

    def _create_pitft_evidence_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(3)

        lbl_title = QLabel("VISUAL VERIFICATION EVIDENCE (2 PANELS)")
        lbl_title.setStyleSheet("font-size: 9px; font-weight: 700; color: #2563eb;")
        lbl_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_title)

        h_matrix = QHBoxLayout()
        h_matrix.setSpacing(4)

        self.box_live = self._create_evidence_box("1. Specimen ROI", compact=True)
        h_matrix.addWidget(self.box_live)

        self.box_template = self._create_evidence_box("2. Extracted Feature", compact=True)
        h_matrix.addWidget(self.box_template)

        if self.master_template is not None:
            self._display_box_image(self.box_template.lbl_img, self.master_template)

        layout.addLayout(h_matrix, stretch=1)

        btn_back = QPushButton("⬅ Return to Verification")
        btn_back.setFixedHeight(24)
        btn_back.clicked.connect(lambda: self.tab_widget.setCurrentIndex(1))
        layout.addWidget(btn_back)

        return tab

    def capture_snapshot_pitft(self):
        """Captures frame and automatically switches to the verification tab."""
        self.capture_snapshot()
        if hasattr(self, 'tab_widget') and self.tab_widget is not None:
            self.tab_widget.setCurrentIndex(1)

    def keyPressEvent(self, event):
        """Allows toggling fullscreen via F11 or Esc."""
        if event.key() == Qt.Key_F11:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()
        elif event.key() == Qt.Key_Escape and self.isFullScreen():
            self.showNormal()
        super().keyPressEvent(event)

    def _create_header_bar(self):
        frame = QFrame()
        frame.setObjectName("cardFrame")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(16, 8, 16, 8)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title = QLabel("AI HOLOGRAM AUTHENTICITY DETECTOR")
        title.setObjectName("headerTitle")
        subtitle = QLabel("Precision Optical Security & VIS-HSI Narrow-Band Analysis • Offline Raspberry Pi Edition")
        subtitle.setObjectName("headerSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        layout.addLayout(title_box)

        layout.addStretch()

        # Theme Switcher Button (☀️ White Theme / 🌙 Dark Theme)
        self.btn_theme_toggle = QPushButton("☀️ White Theme")
        self.btn_theme_toggle.setObjectName("btnTheme")
        self.btn_theme_toggle.setToolTip("Switch between White and Cyber Dark theme")
        self.btn_theme_toggle.clicked.connect(self.toggle_theme)
        layout.addWidget(self.btn_theme_toggle)

        # Status Pill
        self.lbl_status_pill = QLabel("● SYSTEM READY")
        self._update_status_pill_style("ready")
        layout.addWidget(self.lbl_status_pill)
        return frame

    def toggle_theme(self):
        """Toggles cleanly between Executive White Theme and Cyber Dark Theme."""
        app = QApplication.instance()
        if self.current_theme == "light":
            self.current_theme = "dark"
            if getattr(self, 'pitft_mode', False):
                app.setStyleSheet(PITFT_DARK_QSS)
                self.btn_theme_toggle.setText("🌙")
            else:
                app.setStyleSheet(MODERN_CYBER_DARK_QSS)
                self.btn_theme_toggle.setText("🌙 Dark Theme")
        else:
            self.current_theme = "light"
            if getattr(self, 'pitft_mode', False):
                app.setStyleSheet(PITFT_LIGHT_QSS)
                self.btn_theme_toggle.setText("☀️")
            else:
                app.setStyleSheet(LIGHT_THEME_QSS)
                self.btn_theme_toggle.setText("☀️ White Theme")

        # Refresh styles on custom badges
        if self.last_analysis_result:
            outcome = self.last_analysis_result.get("outcome", "")
            self._update_verdict_styles(outcome)
        else:
            self._update_status_pill_style("ready")

    def _update_status_pill_style(self, state_type):
        is_dark = (self.current_theme == "dark")
        is_pitft = getattr(self, 'pitft_mode', False)

        if state_type == "ready":
            text = "● READY" if is_pitft else "● SYSTEM READY"
            color = "#10b981" if is_dark else "#059669"
            bg = "#064e3b" if is_dark else "#ecfdf5"
            border = "#059669" if is_dark else "#a7f3d0"
        elif state_type == "live":
            text = "● LIVE" if is_pitft else "● CAMERA LIVE"
            color = "#38bdf8" if is_dark else "#2563eb"
            bg = "#0c4a6e" if is_dark else "#eff6ff"
            border = "#0284c7" if is_dark else "#bfdbfe"
        elif state_type == "captured":
            text = "● CAPTURED" if is_pitft else "● SNAPSHOT CAPTURED"
            color = "#10b981" if is_dark else "#059669"
            bg = "#064e3b" if is_dark else "#ecfdf5"
            border = "#059669" if is_dark else "#a7f3d0"
        else:
            text = "● STANDBY" if is_pitft else "● CAMERA STANDBY"
            color = "#94a3b8" if is_dark else "#64748b"
            bg = "#1e293b" if is_dark else "#f1f5f9"
            border = "#334155" if is_dark else "#cbd5e1"

        if hasattr(self, 'lbl_status_pill'):
            self.lbl_status_pill.setText(text)
            f_size = "9px" if is_pitft else "12px"
            pad = "2px 6px" if is_pitft else "6px 14px"
            self.lbl_status_pill.setStyleSheet(
                f"color: {color}; font-weight: 800; font-size: {f_size}; background: {bg}; "
                f"padding: {pad}; border-radius: 4px; border: 1px solid {border};"
            )

    def _create_camera_panel(self):
        frame = QFrame()
        frame.setObjectName("cardFrame")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        # Section Header
        sec_title = QLabel("CAMERA & SPECIMEN INPUT")
        sec_title.setObjectName("sectionTitle")
        layout.addWidget(sec_title)

        # Device Selection Row
        dev_row = QHBoxLayout()
        dev_row.setSpacing(8)
        lbl_source = QLabel("Camera:")
        lbl_source.setStyleSheet("color: #64748b; font-weight: 600;")
        dev_row.addWidget(lbl_source)

        self.combo_cameras = QComboBox()
        self.combo_cameras.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.combo_cameras.currentIndexChanged.connect(self.on_camera_selected)
        dev_row.addWidget(self.combo_cameras)

        btn_refresh = QPushButton("⟳")
        btn_refresh.setToolTip("Scan / Refresh Hardware Cameras")
        btn_refresh.setFixedWidth(36)
        btn_refresh.clicked.connect(self.refresh_cameras)
        dev_row.addWidget(btn_refresh)

        btn_ip = QPushButton("🌐 IP Stream")
        btn_ip.setToolTip("Connect to custom WiFi / IP Camera stream")
        btn_ip.clicked.connect(self.configure_ip_stream)
        dev_row.addWidget(btn_ip)

        layout.addLayout(dev_row)

        # Primary Camera Control Bar: Start, Stop, Capture
        cam_btn_row = QHBoxLayout()
        cam_btn_row.setSpacing(8)

        self.btn_start = QPushButton("▶ Start Camera")
        self.btn_start.setObjectName("btnStartCam")
        self.btn_start.clicked.connect(self.start_camera)
        cam_btn_row.addWidget(self.btn_start)

        self.btn_stop = QPushButton("⏹ Stop Camera")
        self.btn_stop.setObjectName("btnStopCam")
        self.btn_stop.clicked.connect(self.stop_camera)
        self.btn_stop.setEnabled(False)
        cam_btn_row.addWidget(self.btn_stop)

        self.btn_capture = QPushButton("📸 Capture Snapshot")
        self.btn_capture.setObjectName("btnCapture")
        self.btn_capture.clicked.connect(self.capture_snapshot)
        cam_btn_row.addWidget(self.btn_capture)

        layout.addLayout(cam_btn_row)

        # Secondary Actions: Load File
        file_row = QHBoxLayout()
        self.btn_load_file = QPushButton("📂 Load Hologram Image from Disk")
        self.btn_load_file.clicked.connect(self.load_image_file)
        file_row.addWidget(self.btn_load_file)
        layout.addLayout(file_row)

        # Video Viewport Container (Rock-Solid Fixed Geometry)
        # Using QSizePolicy.Ignored prevents setPixmap from changing sizeHint and oscillating the layout
        self.viewport_container = QFrame()
        self.viewport_container.setObjectName("previewFrame")
        self.viewport_container.setMinimumHeight(350)
        self.viewport_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        v_vp = QVBoxLayout(self.viewport_container)
        v_vp.setContentsMargins(2, 2, 2, 2)

        self.lbl_viewport = QLabel()
        self.lbl_viewport.setAlignment(Qt.AlignCenter)
        self.lbl_viewport.setStyleSheet(
            "background-color: #020617; border-radius: 8px; color: #94a3b8; font-size: 13px;"
        )
        # Critical for screen stability: Ignored policy stops Qt sizeHint oscillation
        self.lbl_viewport.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.lbl_viewport.setScaledContents(False)
        self.lbl_viewport.setText("Click '▶ Start Camera' to launch live video stream\nor '📂 Load Hologram Image' to open a specimen image.")
        v_vp.addWidget(self.lbl_viewport)

        layout.addWidget(self.viewport_container, stretch=1)

        # Viewport Status & Reticle Checkbox (Fixed width elements prevent text jitter)
        bottom_row = QHBoxLayout()
        self.chk_reticle = QCheckBox("Show Alignment Reticle")
        self.chk_reticle.setChecked(True)
        self.chk_reticle.toggled.connect(self.on_toggle_reticle)
        bottom_row.addWidget(self.chk_reticle)

        bottom_row.addStretch()

        self.lbl_feed_info = QLabel("Standby • 0.0 FPS")
        self.lbl_feed_info.setFixedWidth(130)
        self.lbl_feed_info.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.lbl_feed_info.setStyleSheet("color: #64748b; font-size: 11px;")
        bottom_row.addWidget(self.lbl_feed_info)

        layout.addLayout(bottom_row)
        return frame

    def _create_analysis_panel(self):
        frame = QFrame()
        frame.setObjectName("cardFrame")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        # Section Header
        sec_title = QLabel("INSPECTION & VERIFICATION")
        sec_title.setObjectName("sectionTitle")
        layout.addWidget(sec_title)

        # Autonomous Spectral Calibration Card (Wavelength & Gain set automatically per hologram)
        param_frame = QFrame()
        param_frame.setStyleSheet(
            "background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 10px;"
        )
        v_param = QVBoxLayout(param_frame)
        v_param.setContentsMargins(12, 10, 12, 10)
        v_param.setSpacing(4)

        lbl_auto_title = QLabel("⚡ AUTONOMOUS SPECTRAL & OPTICAL GAIN CALIBRATION")
        lbl_auto_title.setStyleSheet("font-size: 11px; font-weight: 800; color: #2563eb; letter-spacing: 0.5px;")
        v_param.addWidget(lbl_auto_title)

        self.lbl_calib_status = QLabel("Wavelength: Auto (500 nm VIS-HSI) • Optical Gain: Dynamic Exposure Calibration")
        self.lbl_calib_status.setStyleSheet("font-size: 12px; color: #0f172a; font-weight: 600;")
        v_param.addWidget(self.lbl_calib_status)

        lbl_auto_sub = QLabel("Autonomous optical calibration dynamically tunes wavelength and exposure per hologram specimen for certified counterfeit detection accuracy.")
        lbl_auto_sub.setStyleSheet("font-size: 11px; color: #64748b;")
        v_param.addWidget(lbl_auto_sub)

        layout.addWidget(param_frame)

        # Prominent Authenticity Verification Button
        self.btn_verify = QPushButton("⚡ VERIFY HOLOGRAM AUTHENTICITY")
        self.btn_verify.setObjectName("btnAnalyze")
        self.btn_verify.clicked.connect(self.run_verification)
        layout.addWidget(self.btn_verify)

        # Verdict Outcome Banner
        self.banner_frame = QFrame()
        self.banner_frame.setStyleSheet(
            "background-color: #f8fafc; border-radius: 8px; border: 2px solid #cbd5e1; padding: 12px;"
        )
        v_banner = QVBoxLayout(self.banner_frame)
        v_banner.setContentsMargins(14, 12, 14, 12)
        v_banner.setSpacing(4)

        self.lbl_verdict_badge = QLabel("AWAITING SPECIMEN INSPECTION")
        self.lbl_verdict_badge.setStyleSheet("font-size: 18px; font-weight: 800; color: #64748b;")
        self.lbl_verdict_badge.setAlignment(Qt.AlignCenter)
        v_banner.addWidget(self.lbl_verdict_badge)

        self.lbl_verdict_detail = QLabel("Position hologram inside camera reticle and click '⚡ Verify Hologram Authenticity'.")
        self.lbl_verdict_detail.setStyleSheet("font-size: 12px; color: #64748b;")
        self.lbl_verdict_detail.setWordWrap(True)
        self.lbl_verdict_detail.setAlignment(Qt.AlignCenter)
        v_banner.addWidget(self.lbl_verdict_detail)

        layout.addWidget(self.banner_frame)

        # EXACTLY TWO VISUAL VERIFICATION PANELS
        matrix_title = QLabel("VISUAL VERIFICATION EVIDENCE:")
        matrix_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #2563eb; text-transform: uppercase; margin-top: 4px;")
        layout.addWidget(matrix_title)

        h_matrix = QHBoxLayout()
        h_matrix.setSpacing(12)

        # 1. Live Acquisition Frame with detected hologram ROI
        self.box_live = self._create_evidence_box("1. Live Acquisition Specimen (ROI)")
        h_matrix.addWidget(self.box_live)

        # 2. Extracted Specimen Hologram Feature (cropped hologram from specimen)
        self.box_template = self._create_evidence_box("2. Extracted Specimen Hologram Feature")
        h_matrix.addWidget(self.box_template)

        # In standby, show master template thumbnail so the box is not empty
        if self.master_template is not None:
            self._display_box_image(self.box_template.lbl_img, self.master_template)

        layout.addLayout(h_matrix, stretch=1)

        # PDF Report Generation Button
        self.btn_export_pdf = QPushButton("📄 Export Formal PDF Inspection Certificate")
        self.btn_export_pdf.setObjectName("btnPrimary")
        self.btn_export_pdf.clicked.connect(self.export_pdf_certificate)
        layout.addWidget(self.btn_export_pdf)

        return frame

    def _create_evidence_box(self, label_text, compact=False):
        box = QFrame()
        pad = "2px" if compact else "6px"
        box.setStyleSheet(
            f"background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 6px; padding: {pad};"
        )
        v = QVBoxLayout(box)
        v_pad = 4 if compact else 8
        v.setContentsMargins(v_pad, v_pad, v_pad, v_pad)
        v.setSpacing(2 if compact else 6)

        lbl_title = QLabel(label_text)
        f_size = "9px" if compact else "11px"
        lbl_title.setStyleSheet(f"font-size: {f_size}; color: #475569; font-weight: 700; text-align: center;")
        lbl_title.setAlignment(Qt.AlignCenter)
        v.addWidget(lbl_title)

        lbl_img = QLabel()
        lbl_img.setAlignment(Qt.AlignCenter)
        lbl_img.setStyleSheet("background-color: #020617; border-radius: 4px; border: 1px solid #cbd5e1;")
        min_w, min_h = (60, 50) if compact else (120, 110)
        lbl_img.setMinimumSize(min_w, min_h)
        # Critical: Ignored size policy prevents layout jitter
        lbl_img.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        lbl_img.setScaledContents(False)
        v.addWidget(lbl_img)

        box.lbl_img = lbl_img
        return box

    # ------------------------------------------------------------------------
    # Camera Operations (Start, Stop, Capture, IP)
    # ------------------------------------------------------------------------

    def refresh_cameras(self):
        self.combo_cameras.blockSignals(True)
        self.combo_cameras.clear()
        devices = list_system_cameras()
        for d in devices:
            self.combo_cameras.addItem(d["name"], d)
        if self.combo_cameras.count() > 0:
            self.combo_cameras.setCurrentIndex(0)
        self.combo_cameras.blockSignals(False)

    def on_camera_selected(self, index):
        if self.camera_worker.isRunning():
            self.start_camera()

    def start_camera(self):
        idx = self.combo_cameras.currentIndex()
        data = self.combo_cameras.itemData(idx) if idx >= 0 else None

        if data:
            c_type = data.get("type")
            if c_type == "picamera":
                self.camera_worker.set_picamera()
            elif c_type == "network":
                if not self.camera_worker.stream_url:
                    self.configure_ip_stream()
                    return
                self.camera_worker.set_network_stream(self.camera_worker.stream_url)
            else:
                self.camera_worker.set_hardware_camera(data.get("id", 0))

        if not self.camera_worker.isRunning():
            self.camera_worker.start()

        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self._update_status_pill_style("live")

    def stop_camera(self):
        self.camera_worker.stop_capture()
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self._update_status_pill_style("standby")

    def capture_snapshot(self):
        if self.current_frame is not None:
            self.stop_camera()
            # Save Capture.png
            cv2.imwrite("Capture.png", self.current_frame)
            self._update_status_pill_style("captured")
            self.status_bar.showMessage("Snapshot captured and saved as 'Capture.png'! Ready for Authenticity Verification.", 5000)

    def configure_ip_stream(self):
        current_url = getattr(self.camera_worker, 'stream_url', "http://192.168.50.224/html/cam_pic_new.php")
        url, ok = QInputDialog.getText(
            self, "Network / WiFi IP Camera Stream",
            "Enter RTSP or HTTP MJPEG Stream URL:\n(e.g., http://192.168.50.224/html/cam_pic_new.php or rtsp://...):",
            text=current_url
        )
        if ok and url.strip():
            self.camera_worker.set_network_stream(url.strip())
            self.start_camera()

    def load_image_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Hologram Image File", "",
            "Hologram Images (*.png *.bmp *.jpg *.jpeg);;All Files (*)"
        )
        if path and os.path.exists(path):
            img = cv2.imread(path)
            if img is not None:
                self.stop_camera()
                self.current_frame = img
                self.camera_worker.set_static_image(img)
                self.display_frame(img)
                self.status_bar.showMessage(f"Loaded: {os.path.basename(path)}", 4000)

    def on_frame_received(self, frame):
        self.current_frame = frame
        self.display_frame(frame)

    def on_fps_updated(self, fps):
        status_text = f"Live • {fps:.1f} FPS"
        self.lbl_feed_info.setText(status_text)

    def on_camera_status(self, text, color):
        self.lbl_feed_info.setText(text)

    def on_toggle_reticle(self, checked):
        self.show_reticle = checked
        if self.current_frame is not None:
            self.display_frame(self.current_frame)

    def display_frame(self, frame):
        """Displays video frame smoothly scaled to viewport with zero layout oscillation."""
        if frame is None:
            return

        display_img = frame.copy()
        if self.show_reticle:
            self._draw_reticle(display_img)

        h, w = display_img.shape[:2]
        vw = max(10, self.lbl_viewport.width())
        vh = max(10, self.lbl_viewport.height())

        ch = 1 if len(display_img.shape) == 2 else display_img.shape[2]
        fmt = QImage.Format_Grayscale8 if ch == 1 else QImage.Format_BGR888

        q_img = QImage(display_img.data, w, h, ch * w, fmt)
        scaled = q_img.scaled(vw, vh, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.lbl_viewport.setPixmap(QPixmap.fromImage(scaled))

    def _draw_reticle(self, frame):
        h, w = frame.shape[:2]
        cx, cy = w // 2, h // 2
        rw, rh = int(w * 0.44), int(h * 0.52)
        x1, y1 = max(0, cx - rw // 2), max(0, cy - rh // 2)
        x2, y2 = min(w - 1, cx + rw // 2), min(h - 1, cy + rh // 2)

        color = (0, 240, 255)  # Cyan
        thickness = 2
        corner_len = 22

        cv2.line(frame, (x1, y1), (x1 + corner_len, y1), color, thickness)
        cv2.line(frame, (x1, y1), (x1, y1 + corner_len), color, thickness)
        cv2.line(frame, (x2, y1), (x2 - corner_len, y1), color, thickness)
        cv2.line(frame, (x2, y1), (x2, y1 + corner_len), color, thickness)
        cv2.line(frame, (x1, y2), (x1 + corner_len, y2), color, thickness)
        cv2.line(frame, (x1, y2), (x1 + corner_len, y2), color, thickness)
        cv2.line(frame, (x2, y2), (x2 - corner_len, y2), color, thickness)
        cv2.line(frame, (x2, y2), (x2 - corner_len, y2), color, thickness)

        cv2.drawMarker(frame, (cx, cy), color, cv2.MARKER_CROSS, 16, 1)

    # ------------------------------------------------------------------------
    # Authenticity Verification Pipeline (100% Autonomous Spectral Calibration)
    # ------------------------------------------------------------------------

    def run_verification(self):
        if self.current_frame is None:
            QMessageBox.warning(self, "No Specimen", "Please start camera or load an image first.")
            return

        self.btn_verify.setEnabled(False)
        self.btn_verify.setText("Autonomous Optical Spectral Verification in Progress...")
        QApplication.processEvents()

        try:
            # 100% Autonomous Calibration per Hologram Specimen
            result = self.analyzer.analyze(
                self.current_frame,
                self.fast_pipeline,
                auto_calibrate=True
            )

            # Save intermediate outputs for backward compatibility
            cv2.imwrite("nbi.bmp", result["nbi_bgr"])
            cv2.imwrite("cropped.png", result["crop_bgr"])

            outcome = result["outcome"]
            if "Original" in outcome:
                verdict_text = "THE HOLOGRAM IS ORIGINAL"
            elif "Counterfeit" in outcome:
                verdict_text = "THE HOLOGRAM IS COUNTERFEIT"
            else:
                verdict_text = outcome.upper()

            # Update Autonomous Calibration Status Label
            wl_used = result.get("wavelength", 500)
            gain_used = result.get("gain", 15.0)
            self.lbl_calib_status.setText(
                f"Wavelength: Calibrated {wl_used} nm (VIS-HSI) • Optical Gain: {gain_used}× Adaptive Exposure"
            )

            # Update UI Verdict Banner with Clean Theme Styles
            self.lbl_verdict_badge.setText(verdict_text)
            self.lbl_verdict_detail.setText(result["outcome_reason"])
            self._update_verdict_styles(outcome)

            # Update Status Pill
            self.lbl_status_pill.setText(f"● {verdict_text}")

            # Update EXACTLY TWO Visual Evidence Displays
            # Visual 1: Live Frame with detected ROI box
            self._display_box_image(self.box_live.lbl_img, result["annotated_frame"])
            # Visual 2: The actual extracted specimen hologram feature (cropped.png)
            if result.get("crop_bgr") is not None:
                self._display_box_image(self.box_template.lbl_img, result["crop_bgr"])
            elif self.master_template is not None:
                self._display_box_image(self.box_template.lbl_img, self.master_template)

            # Store result for PDF certificate export
            self.last_analysis_result = result
            self.last_analysis_result["verdict_display"] = verdict_text

            self.status_bar.showMessage(f"Verification Complete: {verdict_text}", 6000)

        except Exception as e:
            QMessageBox.critical(self, "Analysis Error", f"An error occurred during verification:\n{str(e)}")
        finally:
            self.btn_verify.setEnabled(True)
            self.btn_verify.setText("⚡ VERIFY HOLOGRAM AUTHENTICITY")

    def _update_verdict_styles(self, outcome):
        is_dark = (self.current_theme == "dark")
        is_pitft = getattr(self, 'pitft_mode', False)

        if "Original" in outcome:
            text_color = "#10b981" if is_dark else "#047857"
            bg = "#064e3b" if is_dark else "#ecfdf5"
            border = "#059669" if is_dark else "#10b981"
        elif "Counterfeit" in outcome:
            text_color = "#ef4444" if is_dark else "#b91c1c"
            bg = "#450a0a" if is_dark else "#fef2f2"
            border = "#dc2626" if is_dark else "#ef4444"
        else:
            text_color = "#f59e0b" if is_dark else "#b45309"
            bg = "#451a03" if is_dark else "#fffbeb"
            border = "#d97706" if is_dark else "#f59e0b"

        badge_font = "13px" if is_pitft else "19px"
        pad = "6px" if is_pitft else "12px"
        pill_font = "9px" if is_pitft else "12px"
        pill_pad = "2px 6px" if is_pitft else "6px 14px"

        self.lbl_verdict_badge.setStyleSheet(f"font-size: {badge_font}; font-weight: 800; color: {text_color};")
        self.banner_frame.setStyleSheet(
            f"background-color: {bg}; border: 2px solid {border}; border-radius: 6px; padding: {pad};"
        )
        if hasattr(self, 'lbl_status_pill'):
            self.lbl_status_pill.setStyleSheet(
                f"color: {text_color}; font-weight: 800; font-size: {pill_font}; background: {bg}; "
                f"padding: {pill_pad}; border-radius: 4px; border: 1px solid {border};"
            )

    def _display_box_image(self, label, cv_img):
        """Displays static evidence thumbnail with zero layout feedback."""
        if cv_img is None:
            return
        cv_img = np.ascontiguousarray(cv_img)
        h, w = cv_img.shape[:2]
        vw = max(10, label.width())
        vh = max(10, label.height())

        ch = 1 if len(cv_img.shape) == 2 else cv_img.shape[2]
        fmt = QImage.Format_Grayscale8 if ch == 1 else QImage.Format_BGR888

        q_img = QImage(cv_img.data, w, h, ch * w, fmt)
        scaled = q_img.scaled(vw, vh, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        label.setPixmap(QPixmap.fromImage(scaled))

    # ------------------------------------------------------------------------
    # Export PDF Verification Certificate (Two Visual Verifications)
    # ------------------------------------------------------------------------

    def export_pdf_certificate(self):
        if not self.last_analysis_result:
            QMessageBox.warning(self, "No Verification Data", "Please verify a hologram specimen first before exporting a certificate.")
            return

        if not HAS_REPORTLAB:
            QMessageBox.information(
                self, "ReportLab Not Installed",
                "ReportLab is not installed on this system.\nInstall with: pip install reportlab\nto enable PDF certificate export."
            )
            return

        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"Hologram_Certificate_{ts}.pdf"

        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save Verification Certificate", default_filename, "PDF Documents (*.pdf)"
        )
        if not save_path:
            return

        try:
            self._create_pdf_document(save_path, self.last_analysis_result)
            self.status_bar.showMessage(f"Certificate exported: {os.path.basename(save_path)}", 5000)
            QMessageBox.information(
                self, "Certificate Generated",
                f"Formal Verification Certificate saved successfully:\n\n{save_path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Could not create PDF report:\n{str(e)}")

    def _create_pdf_document(self, output_path, data):
        # Temp image files for PDF embedding (ONLY TWO comparison images: Live ROI and Extracted Hologram Feature)
        prefix = f"tmp_cert_{int(time.time())}_"
        temp_dir = os.path.dirname(os.path.abspath(output_path))
        p_annot = os.path.join(temp_dir, f"{prefix}annot.png")
        p_crop = os.path.join(temp_dir, f"{prefix}crop.png")

        cv2.imwrite(p_annot, data["annotated_frame"])
        if data.get("crop_bgr") is not None:
            cv2.imwrite(p_crop, data["crop_bgr"])
        elif self.master_template is not None:
            cv2.imwrite(p_crop, self.master_template)

        doc = SimpleDocTemplate(output_path, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        story = []
        styles = getSampleStyleSheet()

        # Document Header
        title_style = ParagraphStyle(
            'CertTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#0f172a'),
            spaceAfter=4,
            alignment=1
        )
        sub_style = ParagraphStyle(
            'CertSub',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#475569'),
            spaceAfter=14,
            alignment=1
        )

        story.append(Paragraph("<b>AI-POWERED OPTICAL SECURITY VERIFICATION CERTIFICATE</b>", title_style))
        story.append(Paragraph(f"Official Inspection Certificate • Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} • Raspberry Pi Engine", sub_style))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2563eb'), spaceAfter=14))

        # Verdict Callout Box
        verdict = data.get("verdict_display", data.get("outcome", "INSPECTION RESULT"))
        is_orig = "ORIGINAL" in verdict
        v_color = colors.HexColor('#065f46') if is_orig else colors.HexColor('#991b1b')
        v_bg = colors.HexColor('#ecfdf5') if is_orig else colors.HexColor('#fef2f2')

        reason = data.get("outcome_reason", "").replace(chr(10), '<br/>')
        verdict_p = Paragraph(f"<b>VERDICT: {verdict}</b><br/><font size='9'>{reason}</font>", ParagraphStyle('V', fontSize=14, textColor=v_color, alignment=1))
        verdict_table = Table([[verdict_p]], colWidths=[540])
        verdict_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), v_bg),
            ('BOX', (0, 0), (-1, -1), 1.5, v_color),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 14),
            ('RIGHTPADDING', (0, 0), (-1, -1), 14),
        ]))
        story.append(verdict_table)
        story.append(Spacer(1, 14))

        # Metrics Table
        metrics_data = [
            ["Metric Parameter", "Measured Value", "Requirement / Calibrated Reference"],
            ["Calibrated Wavelength", f"{data.get('wavelength', 500)} nm", "VIS-HSI Standard Narrow-Band (Autonomous)"],
            ["Optical Sensor Gain", f"{data.get('gain', 15.0)}×", "Autonomous Dynamic Luminance Exposure"],
            ["Mean Feature Intensity", f"{data.get('mgv', 0):.2f}", f"> {data.get('threshold', 58):.2f} (Required Threshold)"],
            ["System Architecture", "Raspberry Pi & Desktop VIS-HSI Core", "CIE 1931 D65 Calibrated"]
        ]
        m_table = Table(metrics_data, colWidths=[180, 160, 200])
        m_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('FONTSIZE', (0, 0), (-1, -1), 9)
        ]))
        story.append(m_table)
        story.append(Spacer(1, 14))

        # ONLY TWO Embedded Comparison Images Side-by-Side
        img_table_data = [
            [
                Paragraph("<b>1. Live Acquisition Specimen (ROI)</b>", styles['Normal']),
                Paragraph("<b>2. Extracted Specimen Hologram Feature</b>", styles['Normal'])
            ],
            [
                RLImage(p_annot, width=260, height=195),
                RLImage(p_crop, width=260, height=195)
            ]
        ]
        img_table = Table(img_table_data, colWidths=[270, 270])
        img_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('PADDING', (0, 0), (-1, -1), 6)
        ]))
        story.append(img_table)
        story.append(Spacer(1, 14))

        # Footer
        story.append(Paragraph(
            "<font size='8' color='#64748b'>Certified by AI Hologram Authenticity Verification Engine • 100% Offline Cryptographic & VIS-HSI Optical Security</font>",
            ParagraphStyle('F', alignment=1)
        ))

        doc.build(story)

        # Clean temp images
        for p in [p_annot, p_crop]:
            try:
                if os.path.exists(p): os.remove(p)
            except: pass

    def closeEvent(self, event):
        self.camera_worker.stop_capture()
        event.accept()


# ============================================================================
# Application Entry Point
# ============================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="AI Hologram Authenticity Detector - Raspberry Pi Edition")
    parser.add_argument("--pitft", "--adafruit", "--touch", dest="pitft", action="store_true",
                        help="Force Adafruit 2.8\" PiTFT Touchscreen mode (320x240)")
    parser.add_argument("--desktop", dest="desktop", action="store_true",
                        help="Force standard desktop layout regardless of screen size")
    parser.add_argument("--fullscreen", action="store_true", help="Launch in fullscreen mode")
    parser.add_argument("--windowed", action="store_true", help="Launch in windowed mode (no fullscreen)")
    parser.add_argument("--auto-camera", "--autostart-camera", dest="auto_camera", action="store_true",
                        help="Automatically start camera stream upon launch")
    args, unknown = parser.parse_known_args()

    # ── Pre-QApplication: read real framebuffer resolution when available ──
    # This lets us set the correct DPI flags BEFORE QApplication is created.
    is_pitft_cli = (
        args.pitft
        or any(arg in sys.argv for arg in ["--pitft", "--adafruit", "--touch", "--small-screen"])
        or os.environ.get("PITFT_MODE", "") in ("1", "true", "yes")
    )

    # Try to read screen size from framebuffer / environment without Qt
    detected_small = False
    if not args.desktop and not is_pitft_cli:
        # /sys/class/graphics/fb0/virtual_size  →  "320,240"
        for fb in ["/sys/class/graphics/fb1/virtual_size",
                   "/sys/class/graphics/fb0/virtual_size"]:
            try:
                with open(fb) as fh:
                    parts = fh.read().strip().split(",")
                    fb_w, fb_h = int(parts[0]), int(parts[1])
                    if min(fb_w, fb_h) <= 320:
                        detected_small = True
                    break
            except Exception:
                pass

        # Also honour DISPLAY_WIDTH / DISPLAY_HEIGHT env vars set by installer
        try:
            env_w = int(os.environ.get("DISPLAY_WIDTH", "0"))
            env_h = int(os.environ.get("DISPLAY_HEIGHT", "0"))
            if env_w > 0 and env_h > 0 and min(env_w, env_h) <= 320:
                detected_small = True
        except Exception:
            pass

    use_small_screen = is_pitft_cli or detected_small

    # ── Qt DPI / scaling attributes (must be set before QApplication()) ────
    if use_small_screen:
        # Strict 1:1 pixel mapping — no scaling on tiny 320×240 displays
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, False)
        os.environ["QT_SCALE_FACTOR"] = "1"
        os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"
    else:
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)

    # ── Decide pitft_mode for the window ───────────────────────────────────
    pitft_choice = None
    if args.pitft or use_small_screen:
        pitft_choice = True
    elif args.desktop:
        pitft_choice = False
    # else → None → auto-detected inside RaspberryHologramApp.__init__()

    window = RaspberryHologramApp(pitft_mode=pitft_choice)

    # ── Apply stylesheet ───────────────────────────────────────────────────
    if window.pitft_mode:
        app.setStyleSheet(PITFT_LIGHT_QSS)
        if args.fullscreen or (is_raspberry_pi() and not args.windowed):
            window.showFullScreen()
        else:
            window.show()
    else:
        app.setStyleSheet(LIGHT_THEME_QSS)
        if args.fullscreen:
            window.showFullScreen()
        else:
            window.show()

    # ── Auto-start camera if requested or enabled via environment ──────────
    auto_cam = args.auto_camera or os.environ.get("AUTOSTART_CAMERA", "").lower() in ("1", "true", "yes")
    if auto_cam:
        QtCore.QTimer.singleShot(700, window.start_camera)

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
