# -*- mode: python ; coding: utf-8 -*-
# PyInstaller Spec for AI-Powered Hologram Authenticity Detection System

import sys
import os

block_cipher = None

repo_dir = os.path.abspath(SPECPATH)
sub_repo = os.path.join(repo_dir, 'Counterfeit-Hologram-Detector-main')
if os.path.exists(sub_repo):
    src_dir = os.path.join(sub_repo, 'SRC')
else:
    src_dir = os.path.join(repo_dir, 'SRC')

added_datas = [
    (os.path.join(src_dir, 'weight.npz'), '.'),
    (os.path.join(src_dir, 'Template.png'), '.'),
    (os.path.join(src_dir, 'icon.ico'), '.'),
    (os.path.join(src_dir, 'icon.png'), '.'),
    (os.path.join(src_dir, 'FormMain.ui'), '.'),
    (os.path.join(src_dir, 'cr_weights'), 'cr_weights'),
    (os.path.join(src_dir, 'templates'), 'templates'),
    (os.path.join(src_dir, 'static'), 'static'),
    (os.path.join(src_dir, 'weight.npz'), 'SRC'),
    (os.path.join(src_dir, 'Template.png'), 'SRC'),
    (os.path.join(src_dir, 'icon.ico'), 'SRC'),
    (os.path.join(src_dir, 'icon.png'), 'SRC'),
    (os.path.join(src_dir, 'FormMain.ui'), 'SRC'),
    (os.path.join(src_dir, 'cr_weights'), 'SRC/cr_weights'),
    (os.path.join(src_dir, 'templates'), 'SRC/templates'),
    (os.path.join(src_dir, 'static'), 'SRC/static'),
]

icon_path = os.path.join(src_dir, 'icon.ico')

a = Analysis(
    ['final.app.py'],
    pathex=[repo_dir, sub_repo, src_dir],
    binaries=[],
    datas=added_datas,
    hiddenimports=[
        'Final_app',
        'web_app',
        'camera_manager',
        'hologram_core',
        'report_generator',
        'styles',
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'PyQt5.sip',
        'flask',
        'jinja2',
        'werkzeug',
        'cv2',
        'numpy',
        'scipy',
        'scipy.signal',
        'scipy.ndimage',
        'reportlab',
        'reportlab.lib',
        'reportlab.platypus',
        'reportlab.lib.colors',
        'reportlab.lib.pagesizes',
        'reportlab.lib.styles',
        'reportlab.pdfgen',
        'PIL',
        'PIL.Image',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', 'matplotlib', 'torch', 'torchvision', 'transformers',
        'notebook', 'jupyter', 'jupyterlab', 'IPython', 'pandas', 'polars'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='HologramAuthenticity',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
)
