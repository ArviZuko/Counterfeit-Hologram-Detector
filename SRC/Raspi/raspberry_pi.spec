# ==============================================================================
# PyInstaller Spec – AI Hologram Authenticity Detector (Raspberry Pi Edition)
# ==============================================================================
# Build on the Raspberry Pi with:
#   pip install pyinstaller
#   pyinstaller raspberry_pi.spec
#
# Output:
#   dist/HologramDetector          ← single-folder distribution
#   dist/HologramDetector/HologramDetector  ← the executable
# ==============================================================================

import os, sys

block_cipher = None

# ── Collect all data assets that must travel with the executable ───────────
# Each tuple: (source_path, destination_folder_inside_bundle)
datas = []

# Core model / asset files
_assets = [
    "weight.npz",
    "Template.png",
    "icon.png",
]
for _a in _assets:
    if os.path.exists(_a):
        datas.append((_a, "."))

# cr_weights folder (ColorReproducer weights)
if os.path.isdir("cr_weights"):
    datas.append(("cr_weights", "cr_weights"))

# ── Hidden imports needed by PyInstaller (Qt, picamera2, etc.) ────────────
hiddenimports = [
    "PyQt5",
    "PyQt5.QtWidgets",
    "PyQt5.QtGui",
    "PyQt5.QtCore",
    "cv2",
    "numpy",
    "numpy.core._multiarray_umath",
    "numpy.linalg",
    "reportlab",
    "reportlab.platypus",
    "reportlab.lib.pagesizes",
    "reportlab.lib.colors",
    "reportlab.lib.styles",
    "picamera2",          # gracefully absent on non-Pi — no error if missing
]

a = Analysis(
    ["raspberry.py"],
    pathex=[
        ".",
        "SRC",
        os.path.join("Counterfeit-Hologram-Detector-main", "SRC"),
    ],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "scipy", "pandas"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="HologramDetector",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # No terminal window – GUI only
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="icon.png" if os.path.exists("icon.png") else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="HologramDetector",
)

