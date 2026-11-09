"""
AI-Powered Hologram Authenticity Detection System - Advanced Universal Camera Manager
Supports:
- Laptop integrated webcams & USB cameras (Windows DirectShow/MSMF, Linux V4L2, macOS)
- Raspberry Pi system cameras (native Picamera2 / libcamera & V4L2)
- WiFi / IP network cameras (RTSP, HTTP MJPEG, phone IP webcam)
- Browser webcam client streams via WebSocket / canvas injection
- Video files & static hologram image files
- Multi-threaded non-blocking acquisition for both Flask Web and PyQt5 Desktop
"""

import os
import sys
import time
import socket
import threading
import cv2
import numpy as np

# Optional PyQt5 imports for Desktop GUI compatibility
try:
    from PyQt5.QtCore import QThread, pyqtSignal, QMutex, QWaitCondition
    HAS_PYQT5 = True
except ImportError:
    HAS_PYQT5 = False


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


def get_local_ip_addresses():
    """
    Returns detected local network IP addresses (e.g. WiFi, Ethernet)
    Useful for displaying connection URLs on Raspberry Pi and laptops.
    """
    ip_list = []
    # Primary method: determine outgoing interface
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.2)
        s.connect(('8.8.8.8', 80))
        primary_ip = s.getsockname()[0]
        s.close()
        if primary_ip and primary_ip not in ip_list and not primary_ip.startswith('127.'):
            ip_list.append(primary_ip)
    except Exception:
        pass

    # Secondary method: hostname lookup
    try:
        hostname = socket.gethostname()
        for ip in socket.gethostbyname_ex(hostname)[2]:
            if ip not in ip_list and not ip.startswith('127.'):
                ip_list.append(ip)
    except Exception:
        pass

    if not ip_list:
        ip_list.append("127.0.0.1")
    return ip_list


def enumerate_available_cameras(max_devices=5):
    """
    Probes system video devices to identify active cameras.
    Intelligently tests Windows Media Foundation (MSMF), DirectShow (DSHOW),
    and V4L2 backends to verify that valid non-zero RGB frames can be acquired.
    Returns list of dicts with device indices, names, resolutions, and working backends.
    Works seamlessly on Windows, Raspberry Pi Linux, and macOS.
    """
    devices = []
    is_windows = sys.platform.startswith('win')
    is_rpi = is_raspberry_pi()

    # On Raspberry Pi, check for libcamera / picamera2
    if is_rpi:
        try:
            from picamera2 import Picamera2
            devices.append({
                "id": "picamera2",
                "name": "Raspberry Pi Camera Module (Picamera2 / libcamera)",
                "resolution": "1920x1080 (HD)",
                "type": "picamera",
                "backend": "picamera"
            })
        except Exception:
            pass

    backend_candidates = [
        (cv2.CAP_MSMF, 'msmf', 'MSMF'),
        (cv2.CAP_ANY, 'any', 'Default'),
        (cv2.CAP_DSHOW, 'dshow', 'DirectShow')
    ] if is_windows else (
        [(cv2.CAP_V4L2, 'v4l2', 'V4L2'), (cv2.CAP_ANY, 'any', 'Default')]
        if sys.platform.startswith('linux') else [(cv2.CAP_ANY, 'any', 'Default')]
    )

    for idx in range(max_devices):
        working_backend = None
        working_w = 640
        working_h = 480
        found_active = False

        for b_flag, b_code, b_name in backend_candidates:
            cap = None
            try:
                cap = cv2.VideoCapture(idx, b_flag)
                if not cap.isOpened():
                    continue

                # Read a few frames to allow sensor AGC / auto-exposure to warm up
                for _ in range(4):
                    ret, frame = cap.read()
                    if ret and frame is not None and np.count_nonzero(frame) > 0 and np.mean(frame) > 0.5:
                        found_active = True
                        break

                if found_active:
                    working_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    working_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    working_backend = (b_code, b_name)
                    cap.release()
                    break
                cap.release()
            except Exception:
                if cap is not None:
                    try:
                        cap.release()
                    except Exception:
                        pass

        if found_active and working_backend:
            b_code, b_name = working_backend
            if idx == 0 or idx == 1:
                label = f"Camera {idx} (Laptop Webcam - {working_w}x{working_h} [{b_name}])"
            else:
                label = f"Camera {idx} (Video Device - {working_w}x{working_h} [{b_name}])"
            devices.append({
                "id": idx,
                "name": label,
                "resolution": f"{working_w}x{working_h}",
                "type": "hardware",
                "backend": b_code
            })

    # If no active devices detected with non-zero frames (e.g. camera shutter closed),
    # provide device 0 as fallback so user can still connect
    if not any(d.get("type") == "hardware" for d in devices):
        devices.append({
            "id": 0,
            "name": "Camera 0 (Laptop Webcam - Fallback)",
            "resolution": "1280x720",
            "type": "hardware",
            "backend": "msmf" if is_windows else "any"
        })

    # Client-side browser webcam option (WebRTC / getUserMedia)
    devices.append({
        "id": "browser_webcam",
        "name": "Laptop Webcam (Direct In-Browser WebRTC)",
        "resolution": "Client Native (1280x720)",
        "type": "browser"
    })

    # WiFi / Network IP Camera stream
    devices.append({
        "id": "ip_camera",
        "name": "WiFi / Network Camera (RTSP / HTTP MJPEG)",
        "resolution": "Configurable Stream",
        "type": "network"
    })

    # Video file option
    devices.append({
        "id": "video_file",
        "name": "Pre-recorded Inspection Video (MP4 / AVI)",
        "resolution": "Native",
        "type": "file"
    })

    return devices


class UniversalCameraEngine:
    """
    Core thread-safe camera engine supporting all platforms:
    - Windows laptop webcams (DirectShow, MSMF, Auto-negotiation)
    - Raspberry Pi Picamera2 & V4L2
    - WiFi / IP RTSP / HTTP streams
    - Static images and video loops
    - Injected browser frames
    """
    def __init__(self):
        self.lock = threading.Lock()
        self._running = False
        self._thread = None

        self.source_type = "hardware"  # "hardware", "picamera", "network", "file", "image", "browser"
        self.device_index = 0
        self.backend_preference = None  # None (auto), "msmf", "dshow", "any"
        self.stream_url = ""
        self.file_path = ""
        self.static_image = None
        self.latest_frame = None
        self.last_status = ("Initializing...", "#38bdf8")
        self.fps = 0.0

        self.requested_width = 1280
        self.requested_height = 720
        self.picam_instance = None

        # Listeners / Callbacks for signals
        self.frame_callbacks = []
        self.status_callbacks = []
        self.error_callbacks = []

    def set_status(self, text, color="#10b981"):
        self.last_status = (text, color)
        for cb in self.status_callbacks:
            try:
                cb(text, color)
            except Exception:
                pass

    def emit_error(self, message):
        for cb in self.error_callbacks:
            try:
                cb(message)
            except Exception:
                pass

    def set_hardware_camera(self, device_index=0, width=1280, height=720, backend=None):
        self.stop()
        self.source_type = "hardware"
        self.device_index = device_index
        self.requested_width = width
        self.requested_height = height
        self.backend_preference = backend

    def set_picamera(self, width=1280, height=720):
        self.stop()
        self.source_type = "picamera"
        self.requested_width = width
        self.requested_height = height

    def set_network_stream(self, url):
        self.stop()
        self.source_type = "network"
        self.stream_url = url.strip()

    def set_video_file(self, path):
        self.stop()
        self.source_type = "file"
        self.file_path = path

    def set_static_image(self, img_or_path):
        self.stop()
        self.source_type = "image"
        if isinstance(img_or_path, str):
            self.file_path = img_or_path
            self.static_image = cv2.imread(img_or_path)
        else:
            self.static_image = img_or_path

    def inject_browser_frame(self, frame_bgr):
        """Allows direct injection of frames received from browser client via WebSockets or POST."""
        with self.lock:
            self.source_type = "browser"
            self.latest_frame = frame_bgr
            self.set_status("Streaming from Laptop Browser Webcam", "#10b981")
        for cb in self.frame_callbacks:
            try:
                cb(frame_bgr)
            except Exception:
                pass

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.2)
        if self.picam_instance is not None:
            try:
                self.picam_instance.stop()
                self.picam_instance.close()
            except Exception:
                pass
            self.picam_instance = None
        self.set_status("Camera Inactive", "#64748b")

    def get_latest_frame(self):
        with self.lock:
            if self.latest_frame is not None:
                return self.latest_frame.copy()
            return None

    def get_jpeg_bytes(self, quality=85):
        """Encodes current frame as JPEG for MJPEG HTTP streaming."""
        frame = self.get_latest_frame()
        if frame is None:
            # Generate clean formal standby test pattern
            frame = np.full((480, 640, 3), 20, dtype=np.uint8)
            cv2.putText(frame, "CONNECTING TO CAMERA...", (140, 240),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 180, 240), 2)
        ret, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
        if ret:
            return jpeg.tobytes()
        return None

    def capture_snapshot(self, output_path=None):
        frame = self.get_latest_frame()
        if frame is not None:
            if output_path:
                cv2.imwrite(output_path, frame)
            return frame
        return None

    def _worker_loop(self):
        if self.source_type == "image":
            self._loop_static_image()
        elif self.source_type == "file":
            self._loop_video_file()
        elif self.source_type == "picamera":
            self._loop_picamera()
        elif self.source_type in ("hardware", "network"):
            self._loop_cv_capture()
        elif self.source_type == "browser":
            # Handled via inject_browser_frame
            while self._running:
                time.sleep(0.05)

    def _loop_picamera(self):
        """Native Raspberry Pi Camera Module acquisition using Picamera2."""
        try:
            from picamera2 import Picamera2
            self.set_status("Starting Raspberry Pi Camera...", "#38bdf8")
            self.picam_instance = Picamera2()
            config = self.picam_instance.create_video_configuration(
                main={"size": (self.requested_width, self.requested_height), "format": "BGR888"}
            )
            self.picam_instance.configure(config)
            self.picam_instance.start()
            self.set_status(f"Live (Raspberry Pi CSI {self.requested_width}x{self.requested_height})", "#10b981")
        except Exception as e:
            self.emit_error(f"Picamera2 init failed: {e}. Falling back to V4L2...")
            self.source_type = "hardware"
            self.device_index = 0
            self._loop_cv_capture()
            return

        last_time = time.time()
        while self._running:
            try:
                frame_bgr = self.picam_instance.capture_array()
                with self.lock:
                    self.latest_frame = frame_bgr
                for cb in self.frame_callbacks:
                    cb(frame_bgr)

                now = time.time()
                elapsed = now - last_time
                last_time = now
                if elapsed > 0:
                    self.fps = round(1.0 / elapsed, 1)
                time.sleep(0.01)
            except Exception as e:
                self.emit_error(f"Picamera frame error: {e}")
                time.sleep(0.5)

    def _loop_cv_capture(self):
        is_windows = sys.platform.startswith('win')
        cap = None
        backend_name = "Default"

        if self.source_type == "hardware":
            self.set_status(f"Opening Camera {self.device_index}...", "#38bdf8")

            # Determine backend order
            if is_windows:
                pref = getattr(self, 'backend_preference', None)
                if pref == 'dshow':
                    backends = [(cv2.CAP_DSHOW, 'DirectShow'), (cv2.CAP_MSMF, 'MSMF'), (cv2.CAP_ANY, 'Default')]
                elif pref == 'msmf':
                    backends = [(cv2.CAP_MSMF, 'MSMF'), (cv2.CAP_ANY, 'Default'), (cv2.CAP_DSHOW, 'DirectShow')]
                elif pref == 'any':
                    backends = [(cv2.CAP_ANY, 'Default'), (cv2.CAP_MSMF, 'MSMF'), (cv2.CAP_DSHOW, 'DirectShow')]
                else:  # Auto-negotiate: MSMF first (modern Windows), then Default, then DirectShow
                    backends = [(cv2.CAP_MSMF, 'MSMF'), (cv2.CAP_ANY, 'Default'), (cv2.CAP_DSHOW, 'DirectShow')]
            elif sys.platform.startswith('linux'):
                backends = [(cv2.CAP_V4L2, 'V4L2'), (cv2.CAP_ANY, 'Default')]
            else:
                backends = [(cv2.CAP_ANY, 'Default')]

            for b_flag, b_label in backends:
                try:
                    test_cap = cv2.VideoCapture(self.device_index, b_flag)
                    if not test_cap.isOpened():
                        continue

                    # Verify frames are valid and not pitch black zeros
                    has_frame = False
                    for _ in range(4):
                        ret, test_frame = test_cap.read()
                        if ret and test_frame is not None and np.count_nonzero(test_frame) > 0 and np.mean(test_frame) > 0.1:
                            has_frame = True
                            break

                    if has_frame:
                        cap = test_cap
                        backend_name = b_label
                        break
                    else:
                        test_cap.release()
                except Exception:
                    pass

            # Fallback if no backend produced verified non-zero frame
            if cap is None:
                default_backend = cv2.CAP_MSMF if is_windows else cv2.CAP_ANY
                cap = cv2.VideoCapture(self.device_index, default_backend)
                if not cap.isOpened():
                    cap = cv2.VideoCapture(self.device_index)
                backend_name = "Auto"

        else:
            # Network RTSP / HTTP stream
            self.set_status("Connecting to WiFi / IP Camera...", "#38bdf8")
            cap = cv2.VideoCapture(self.stream_url)
            backend_name = "Network"

        if cap is None or not cap.isOpened():
            target = f"Camera {self.device_index}" if self.source_type == "hardware" else self.stream_url
            self.set_status("Connection Failed", "#ef4444")
            self.emit_error(f"Failed to open video source: {target}")
            self._running = False
            return

        # Check hardware resolution safely (without corrupting MSMF stream)
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if self.source_type == "hardware":
            self.set_status(f"Live ({w}x{h} [{backend_name}])", "#10b981")
        else:
            self.set_status("WiFi / Network Stream Active", "#10b981")

        last_time = time.time()
        consecutive_failures = 0
        while self._running:
            try:
                ret, frame = cap.read()
            except cv2.error as e:
                consecutive_failures += 1
                time.sleep(0.04)
                continue
            except Exception as e:
                consecutive_failures += 1
                time.sleep(0.04)
                continue

            if not ret or frame is None:
                consecutive_failures += 1
                if consecutive_failures > 30:
                    self.set_status("Reconnecting...", "#f59e0b")
                time.sleep(0.04)
                continue

            consecutive_failures = 0
            with self.lock:
                self.latest_frame = frame

            for cb in self.frame_callbacks:
                try:
                    cb(frame)
                except Exception:
                    pass

            now = time.time()
            elapsed = now - last_time
            last_time = now
            if elapsed > 0:
                self.fps = round(1.0 / elapsed, 1)

            time.sleep(0.005)

        cap.release()
        self.set_status("Camera Inactive", "#64748b")

    def _loop_video_file(self):
        if not os.path.exists(self.file_path):
            self.emit_error(f"Video file not found: {self.file_path}")
            self._running = False
            return

        cap = cv2.VideoCapture(self.file_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        delay = 1.0 / fps if fps > 0 else 0.033
        self.set_status(f"Playing: {os.path.basename(self.file_path)}", "#10b981")

        while self._running:
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue

            with self.lock:
                self.latest_frame = frame

            for cb in self.frame_callbacks:
                try:
                    cb(frame)
                except Exception:
                    pass

            time.sleep(delay)

        cap.release()

    def _loop_static_image(self):
        if self.static_image is None and os.path.exists(self.file_path):
            self.static_image = cv2.imread(self.file_path)

        if self.static_image is None:
            self.emit_error("No valid static image available.")
            self._running = False
            return

        h, w = self.static_image.shape[:2]
        self.set_status(f"Static Inspection Target ({w}x{h})", "#38bdf8")

        while self._running:
            with self.lock:
                self.latest_frame = self.static_image
            for cb in self.frame_callbacks:
                try:
                    cb(self.static_image)
                except Exception:
                    pass
            time.sleep(0.1)


# ============================================================================
# PyQt5 Desktop Thread Wrapper (Preserves 100% GUI compatibility)
# ============================================================================

if HAS_PYQT5:
    class VideoCaptureThread(QThread):
        """PyQt5 signal-compatible wrapper around UniversalCameraEngine."""
        frame_ready = pyqtSignal(np.ndarray)
        fps_updated = pyqtSignal(float)
        status_changed = pyqtSignal(str, str)
        error_occurred = pyqtSignal(str)

        def __init__(self):
            super().__init__()
            self.engine = UniversalCameraEngine()
            self.engine.frame_callbacks.append(self.on_frame)
            self.engine.status_callbacks.append(self.on_status)
            self.engine.error_callbacks.append(self.on_error)

        def on_frame(self, frame):
            self.frame_ready.emit(frame)
            self.fps_updated.emit(self.engine.fps)

        def on_status(self, text, color):
            self.status_changed.emit(text, color)

        def on_error(self, message):
            self.error_occurred.emit(message)

        @property
        def latest_frame(self):
            return self.engine.latest_frame

        @latest_frame.setter
        def latest_frame(self, val):
            self.engine.latest_frame = val

        @property
        def source_type(self):
            return self.engine.source_type

        @source_type.setter
        def source_type(self, val):
            self.engine.source_type = val

        def set_hardware_camera(self, device_index=0, width=1280, height=720, backend=None):
            self.engine.set_hardware_camera(device_index, width, height, backend=backend)

        def set_picamera(self, width=1280, height=720):
            self.engine.set_picamera(width, height)

        def set_network_stream(self, url):
            self.engine.set_network_stream(url)

        def set_video_file(self, path):
            self.engine.set_video_file(path)

        def set_static_image(self, img_or_path):
            self.engine.set_static_image(img_or_path)

        def start_capture(self):
            """Ensures thread and underlying engine are both active."""
            if not self.isRunning():
                self.start()
            else:
                if not self.engine._running:
                    self.engine.start()

        def run(self):
            self.engine.start()
            while self.engine._running:
                time.sleep(0.05)

        def stop(self):
            self.engine.stop()
            if self.isRunning():
                self.wait(1000)

        def capture_snapshot(self, output_path="Capture.png"):
            return self.engine.capture_snapshot(output_path)
else:
    class VideoCaptureThread:
        pass
