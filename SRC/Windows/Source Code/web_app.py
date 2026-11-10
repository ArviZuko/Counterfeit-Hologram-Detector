"""
AI-Powered Hologram Authenticity Detection System - Production Web Application
Runs on Windows Laptops and Raspberry Pi (accessible locally or over WiFi).

Key Capabilities:
- Formal, executive, uncluttered dark-mode web interface
- Universal camera support:
  * Laptop integrated & external USB webcams
  * Raspberry Pi CSI camera (Picamera2 / libcamera & V4L2)
  * In-browser laptop webcam (zero latency via HTML5 getUserMedia)
  * WiFi / IP network cameras (RTSP / HTTP MJPEG streams)
  * Dataset banknote samples & uploaded images/videos
- Real-time Visible Hyperspectral Reconstruction (VIS-HSI 380-780nm)
- Multi-metric authenticity assessment (MGV, NCC template match, microstructures, halftone print detection)
- Instant generation & download of formal PDF verification certificates
- Collapsible inspection audit log with CSV export
"""

import os
import sys
import time
import base64
import json
import datetime
import io
import cv2
import numpy as np
from flask import Flask, render_template, Response, request, jsonify, send_file

# Add SRC directory to sys.path
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from camera_manager import (
    UniversalCameraEngine, enumerate_available_cameras,
    get_local_ip_addresses, is_raspberry_pi
)
from hologram_core import (
    SpectrumTransfer, ColorReproducer, FastHologramPipeline,
    HologramAnalyzer, resolve_resource_path
)
from report_generator import generate_pdf_report

# Initialize Flask App
app = Flask(__name__,
            template_folder=os.path.join(SRC_DIR, "templates"),
            static_folder=os.path.join(SRC_DIR, "static"))

# Initialize Core AI Models
transfer = SpectrumTransfer()
try:
    transfer.load("weight.npz")
except Exception as e:
    print(f"[Warning] Failed loading weight.npz: {e}")

reproducer = ColorReproducer()
try:
    reproducer.load("cr_weights")
except Exception as e:
    print(f"[Warning] Failed loading cr_weights: {e}")

fast_pipeline = FastHologramPipeline(transfer, reproducer)
analyzer = HologramAnalyzer("Template.png")

# Initialize Camera Engine
camera_engine = UniversalCameraEngine()

# State
last_analysis_result = {}
inspection_history = []


def bgr_to_base64_jpeg(img_bgr, quality=85):
    """Converts a BGR OpenCV image to a base64 encoded data URI."""
    if img_bgr is None:
        return ""
    ret, buf = cv2.imencode('.jpg', img_bgr, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not ret:
        return ""
    b64_str = base64.b64encode(buf.tobytes()).decode('utf-8')
    return f"data:image/jpeg;base64,{b64_str}"


def base64_to_bgr(b64_str):
    """Decodes a base64 image data URI to BGR numpy array."""
    try:
        if "," in b64_str:
            b64_str = b64_str.split(",", 1)[1]
        raw_bytes = base64.b64decode(b64_str)
        nparr = np.frombuffer(raw_bytes, np.uint8)
        img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return img_bgr
    except Exception as e:
        print(f"[Error] Failed decoding base64 image: {e}")
        return None


@app.route('/')
def index():
    """Serves the main formal verification dashboard."""
    local_ips = get_local_ip_addresses()
    is_rpi = is_raspberry_pi()
    platform_name = "Raspberry Pi" if is_rpi else ("Windows Laptop" if sys.platform.startswith('win') else "Linux / Unix")
    return render_template(
        'index.html',
        local_ips=local_ips,
        is_rpi=is_rpi,
        platform_name=platform_name
    )


@app.route('/video_feed')
def video_feed():
    """MJPEG stream endpoint for live camera feed."""
    def stream_generator():
        while True:
            frame_bytes = camera_engine.get_jpeg_bytes(quality=80)
            if frame_bytes is not None:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            time.sleep(0.04)  # ~25 FPS
    return Response(stream_generator(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/api/status', methods=['GET'])
def get_system_status():
    """Returns system status, active camera info, network addresses, and FPS."""
    return jsonify({
        "status": "online",
        "fps": camera_engine.fps,
        "camera_status": camera_engine.last_status[0],
        "camera_color": camera_engine.last_status[1],
        "source_type": camera_engine.source_type,
        "device_index": camera_engine.device_index,
        "is_raspberry_pi": is_raspberry_pi(),
        "network_ips": get_local_ip_addresses(),
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })


@app.route('/api/camera/devices', methods=['GET'])
def get_camera_devices():
    """Enumerates available system cameras, WiFi streaming options, and client options."""
    devices = enumerate_available_cameras(max_devices=5)
    return jsonify({
        "devices": devices,
        "active_source": camera_engine.source_type,
        "active_device_id": camera_engine.device_index,
        "active_backend": getattr(camera_engine, 'backend_preference', None)
    })


@app.route('/api/camera/select', methods=['POST'])
def select_camera():
    """Selects camera source: hardware device index, Raspberry Pi camera, WiFi RTSP/HTTP, or file."""
    data = request.get_json() or {}
    source_type = data.get('type', 'hardware')
    dev_id = data.get('id', 0)
    url = data.get('url', '')
    backend = data.get('backend', None)

    if source_type == 'hardware':
        try:
            idx = int(dev_id)
            camera_engine.set_hardware_camera(device_index=idx, backend=backend)
            camera_engine.start()
            return jsonify({"success": True, "message": f"Hardware Camera {idx} selected."})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 400

    elif source_type == 'picamera':
        camera_engine.set_picamera()
        camera_engine.start()
        return jsonify({"success": True, "message": "Raspberry Pi Camera Module selected."})

    elif source_type == 'network':
        if not url:
            return jsonify({"success": False, "error": "Stream URL is required."}), 400
        camera_engine.set_network_stream(url)
        camera_engine.start()
        return jsonify({"success": True, "message": f"Network stream connected: {url}"})

    elif source_type == 'browser':
        camera_engine.stop()
        camera_engine.source_type = 'browser'
        camera_engine.set_status("Using Laptop In-Browser Webcam", "#10b981")
        return jsonify({"success": True, "message": "Direct in-browser laptop camera mode activated."})

    return jsonify({"success": False, "error": "Unknown source type"}), 400


@app.route('/api/camera/control', methods=['POST'])
def control_camera():
    """Starts or stops camera capture."""
    data = request.get_json() or {}
    action = data.get('action', 'start')
    source_type = data.get('type', None)
    dev_id = data.get('id', None)
    backend = data.get('backend', None)

    if action == 'start':
        if source_type == 'hardware' and dev_id is not None:
            try:
                camera_engine.set_hardware_camera(device_index=int(dev_id), backend=backend)
            except Exception:
                pass
        camera_engine.start()
        return jsonify({"success": True, "message": "Camera started."})
    elif action == 'stop':
        camera_engine.stop()
        return jsonify({"success": True, "message": "Camera stopped."})
    return jsonify({"success": False, "error": "Invalid action"}), 400


@app.route('/api/camera/upload_frame', methods=['POST'])
def upload_browser_frame():
    """Receives camera frame from browser client webcam via POST."""
    data = request.get_json() or {}
    img_b64 = data.get('image', '')
    if not img_b64:
        return jsonify({"success": False, "error": "No image data"}), 400

    frame_bgr = base64_to_bgr(img_b64)
    if frame_bgr is not None:
        camera_engine.inject_browser_frame(frame_bgr)
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Failed to decode frame"}), 400


@app.route('/api/sample', methods=['POST'])
def load_sample():
    """Loads a sample hologram or banknote from the calibrated dataset."""
    data = request.get_json() or {}
    sample_key = data.get('sample', 'default')

    dataset_dir = os.path.join(os.path.dirname(SRC_DIR), "Dataset", "Currency", "Duplicate", "Files")
    sample_map = {
        'default': resolve_resource_path("nbi.bmp"),
        'banknote1': os.path.join(dataset_dir, "1.jpg"),
        'banknote2': os.path.join(dataset_dir, "2.jpg"),
        'banknote3': os.path.join(dataset_dir, "3.jpg"),
        'template': resolve_resource_path("Template.png")
    }

    target_path = sample_map.get(sample_key, sample_map['default'])
    if not os.path.exists(target_path):
        target_path = resolve_resource_path("nbi.bmp")

    if os.path.exists(target_path):
        img = cv2.imread(target_path)
        if img is not None:
            camera_engine.set_static_image(img)
            camera_engine.start()
            return jsonify({
                "success": True,
                "message": f"Loaded sample: {os.path.basename(target_path)}",
                "preview": bgr_to_base64_jpeg(img)
            })

    return jsonify({"success": False, "error": "Sample file not found"}), 404


@app.route('/api/analyze', methods=['POST'])
def analyze_hologram():
    """
    Executes full scientific authenticity inspection:
    - Narrow-band reconstruction (VIS-HSI)
    - Multi-scale template matching
    - Mean Gray Value (MGV) calculation
    - Thermal anomaly difference mapping
    - Microstructure edge definition
    - 2D-FFT halftone screening artifact detection
    """
    global last_analysis_result, inspection_history
    data = request.get_json() or {}

    wavelength = int(data.get('wavelength', 500))
    gain = float(data.get('gain', 15.0))
    template_key = data.get('template', 'default')
    custom_frame_b64 = data.get('image', None)

    # 1. Acquire inspection frame
    frame_bgr = None
    if custom_frame_b64:
        frame_bgr = base64_to_bgr(custom_frame_b64)

    if frame_bgr is None:
        frame_bgr = camera_engine.get_latest_frame()

    # Fallback to sample image if no camera frame is currently available
    if frame_bgr is None:
        sample_path = resolve_resource_path("nbi.bmp")
        if os.path.exists(sample_path):
            frame_bgr = cv2.imread(sample_path)

    if frame_bgr is None:
        return jsonify({"success": False, "error": "No camera frame or input image available for analysis."}), 400

    # 2. Select Template
    if template_key == 'banknote1':
        t_path = os.path.join(os.path.dirname(SRC_DIR), "Dataset", "Currency", "Duplicate", "Template1", "1nbi.jpg")
    elif template_key == 'banknote2':
        t_path = os.path.join(os.path.dirname(SRC_DIR), "Dataset", "Currency", "Duplicate", "Template2", "1nbi.jpg")
    else:
        t_path = resolve_resource_path("Template.png")

    if os.path.exists(t_path):
        analyzer.load_template(t_path)

    # 3. Perform Analysis with Auto Spectral Calibration
    try:
        result = analyzer.analyze(frame_bgr, fast_pipeline, auto_calibrate=True)
        last_analysis_result = result

        outcome = result.get("outcome", "The Hologram is Original")
        outcome_reason = result.get("outcome_reason", "Analysis complete.")
        is_original = "Original" in outcome

        # 4. Save to history
        record = {
            "id": f"HLG-{int(time.time()) % 100000:05d}",
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "verdict": outcome,
            "status": "ORIGINAL" if is_original else ("COUNTERFEIT" if "Counterfeit" in outcome else "UNDETECTED"),
            "calibration": f"Auto {result.get('wavelength', 500)} nm"
        }
        inspection_history.insert(0, record)
        if len(inspection_history) > 50:
            inspection_history.pop()

        # 5. Prepare Visual Evidence
        response_data = {
            "success": True,
            "verdict": outcome,
            "verdict_reason": outcome_reason,
            "is_original": is_original,
            "metrics": {
                "outcome": outcome,
                "wavelength": result.get("wavelength", 500),
                "gain": result.get("gain", 15.0),
                "auto_calibrated": True,
                "halftone_artifacts": result.get("print_artifacts", {})
            },
            "images": {
                "raw_annotated": bgr_to_base64_jpeg(result.get("annotated_frame")),
                "reference_template": bgr_to_base64_jpeg(result.get("reference_template"))
            },
            "history_record": record
        }
        return jsonify(response_data)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": f"Analysis failed: {str(e)}"}), 500


@app.route('/api/history', methods=['GET', 'DELETE'])
def manage_history():
    """Fetches or clears the audit history."""
    global inspection_history
    if request.method == 'DELETE':
        inspection_history = []
        return jsonify({"success": True, "message": "History cleared."})
    return jsonify({"history": inspection_history})


@app.route('/api/report/download', methods=['GET'])
def download_report():
    """Generates official verification certificate PDF and serves as download."""
    global last_analysis_result
    if not last_analysis_result:
        return "No analysis result available to generate report. Please inspect a hologram first.", 400

    out_pdf = os.path.join(SRC_DIR, f"Hologram_Certificate_{int(time.time())}.pdf")
    try:
        generate_pdf_report(last_analysis_result, output_pdf_path=out_pdf)
        return send_file(out_pdf, as_attachment=True, download_name="Hologram_Verification_Certificate.pdf")
    except Exception as e:
        return f"Failed generating report: {e}", 500


def run_server(host='0.0.0.0', port=5000, debug=False):
    """Starts the Flask web server."""
    # Auto-start default laptop camera 0 if available
    try:
        camera_engine.set_hardware_camera(0)
        camera_engine.start()
    except Exception as e:
        print(f"[Notice] Hardware camera 0 auto-start: {e}")

    ips = get_local_ip_addresses()
    print("=" * 70)
    print("  AI-POWERED HOLOGRAM AUTHENTICITY DETECTION SYSTEM")
    print("=" * 70)
    print(f"  * Local Web Dashboard:   http://localhost:{port}")
    for ip in ips:
        print(f"  * WiFi / Network Access: http://{ip}:{port}")
    print("=" * 70)
    print("  Ready. Open any of the URLs above in your web browser.")
    print("=" * 70)

    app.run(host=host, port=port, debug=debug, threaded=True)


if __name__ == '__main__':
    run_server(host='0.0.0.0', port=5000)
