"""
AI-Powered Hologram Authenticity Detection System - Professional Styling System
Features:
- LIGHT_THEME_QSS: Crisp executive daylight white theme (clean slate #f8fafc, pure white #ffffff cards, royal blue #2563eb, emerald #059669)
- MODERN_CYBER_DARK_QSS: High-contrast cyber-security dark theme (deep slate/navy #070c18, electric cyan #00f0ff, emerald #10b981, crimson #ef4444)
"""

LIGHT_THEME_QSS = """
/* ========================================================================= */
/* Crisp Executive Daylight White Theme                                      */
/* ========================================================================= */
QMainWindow, QDialog {
    background-color: #f1f5f9;
    color: #0f172a;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', sans-serif;
}

QWidget {
    color: #1e293b;
    font-size: 13px;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
}

/* Crisp Clean Panels & Frames */
QFrame#cardFrame, QFrame#previewFrame, QFrame#controlFrame, QFrame#sidebarFrame {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 10px;
}

QFrame#statusBanner {
    border-radius: 8px;
    padding: 10px;
}

/* Typography & Headers */
QLabel#headerTitle {
    font-size: 19px;
    font-weight: 800;
    color: #0f172a;
    letter-spacing: 0.6px;
}

QLabel#headerSubtitle {
    font-size: 11px;
    color: #64748b;
    font-weight: 500;
}

QLabel#sectionTitle {
    font-size: 12px;
    font-weight: 800;
    color: #2563eb;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    padding-bottom: 2px;
}

QLabel#metricLabel {
    font-size: 11px;
    color: #64748b;
    text-transform: uppercase;
    font-weight: 600;
}

QLabel#metricValue {
    font-size: 15px;
    font-weight: 700;
    color: #0f172a;
}

/* Push Buttons */
QPushButton {
    background-color: #ffffff;
    color: #1e293b;
    border: 1px solid #cbd5e1;
    border-radius: 7px;
    padding: 8px 14px;
    font-weight: 600;
    font-size: 12px;
}

QPushButton:hover {
    background-color: #f8fafc;
    border-color: #94a3b8;
    color: #0f172a;
}

QPushButton:pressed {
    background-color: #e2e8f0;
}

QPushButton:disabled {
    background-color: #f8fafc;
    color: #94a3b8;
    border-color: #e2e8f0;
}

/* Primary Action Buttons */
QPushButton#btnPrimary {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563eb, stop:1 #1d4ed8);
    color: #ffffff;
    border: 1px solid #1d4ed8;
    font-weight: 700;
    font-size: 13px;
    padding: 9px 18px;
    border-radius: 7px;
}

QPushButton#btnPrimary:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1d4ed8, stop:1 #1e40af);
    border-color: #1e40af;
}

/* Start Camera Button (Emerald Green) */
QPushButton#btnStartCam {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #10b981);
    color: #ffffff;
    border: 1px solid #047857;
    font-weight: 700;
    font-size: 13px;
    padding: 9px 16px;
    border-radius: 7px;
}

QPushButton#btnStartCam:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #047857, stop:1 #059669);
    border-color: #065f46;
}

/* Stop Camera Button (Soft Coral Red) */
QPushButton#btnStopCam {
    background-color: #fee2e2;
    color: #dc2626;
    border: 1px solid #fca5a5;
    font-weight: 700;
    font-size: 13px;
    padding: 9px 16px;
    border-radius: 7px;
}

QPushButton#btnStopCam:hover {
    background-color: #fecaca;
    color: #b91c1c;
    border-color: #f87171;
}

/* Snapshot Capture Button (Teal) */
QPushButton#btnCapture {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0d9488, stop:1 #0f766e);
    color: #ffffff;
    border: 1px solid #0f766e;
    font-weight: 700;
    font-size: 13px;
    padding: 9px 16px;
    border-radius: 7px;
}

QPushButton#btnCapture:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0f766e, stop:1 #115e59);
}

/* Prominent Verify Button */
QPushButton#btnAnalyze {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:0.5 #2563eb, stop:1 #1d4ed8);
    color: #ffffff;
    border: 1px solid #0284c7;
    font-weight: 800;
    font-size: 14px;
    border-radius: 7px;
    padding: 12px 24px;
    letter-spacing: 0.6px;
}

QPushButton#btnAnalyze:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0369a1, stop:0.5 #1d4ed8, stop:1 #1e40af);
}

/* Theme Switcher Button */
QPushButton#btnTheme {
    background-color: #f1f5f9;
    color: #334155;
    border: 1px solid #cbd5e1;
    font-weight: 600;
    font-size: 12px;
    padding: 6px 12px;
    border-radius: 6px;
}

QPushButton#btnTheme:hover {
    background-color: #e2e8f0;
    color: #0f172a;
}

/* ComboBox & Inputs */
QComboBox {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 6px 12px;
    color: #0f172a;
    font-weight: 500;
}

QComboBox:hover {
    border-color: #94a3b8;
}

QComboBox:focus {
    border-color: #2563eb;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    color: #0f172a;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
    padding: 4px;
}

QLineEdit, QSpinBox {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 6px 10px;
    color: #0f172a;
}

QCheckBox {
    spacing: 8px;
    color: #334155;
    font-weight: 500;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    background: #ffffff;
}

QCheckBox::indicator:checked {
    background: #2563eb;
    border-color: #2563eb;
}

QStatusBar {
    background-color: #ffffff;
    color: #64748b;
    border-top: 1px solid #e2e8f0;
    font-size: 11px;
}

QToolTip {
    background-color: #0f172a;
    color: #ffffff;
    border: 1px solid #334155;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 12px;
}
"""

MODERN_CYBER_DARK_QSS = """
/* ========================================================================= */
/* Global Window & High-Contrast Cyber Dark Palette                          */
/* ========================================================================= */
QMainWindow, QDialog {
    background-color: #070c18;
    color: #e2e8f0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', sans-serif;
}

QWidget {
    color: #cbd5e1;
    font-size: 13px;
    selection-background-color: #0284c7;
    selection-color: #ffffff;
}

QFrame#cardFrame, QFrame#previewFrame, QFrame#controlFrame, QFrame#sidebarFrame {
    background-color: #0d1527;
    border: 1px solid #1e293b;
    border-radius: 10px;
}

QFrame#statusBanner {
    border-radius: 8px;
    padding: 10px;
}

QLabel#headerTitle {
    font-size: 19px;
    font-weight: 800;
    color: #f8fafc;
    letter-spacing: 0.6px;
}

QLabel#headerSubtitle {
    font-size: 11px;
    color: #94a3b8;
    font-weight: 500;
}

QLabel#sectionTitle {
    font-size: 12px;
    font-weight: 800;
    color: #00f0ff;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    padding-bottom: 2px;
}

QPushButton {
    background-color: #1e293b;
    color: #f1f5f9;
    border: 1px solid #334155;
    border-radius: 7px;
    padding: 8px 14px;
    font-weight: 600;
    font-size: 12px;
}

QPushButton:hover {
    background-color: #273549;
    border-color: #475569;
    color: #ffffff;
}

QPushButton#btnPrimary {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #2563eb);
    color: #ffffff;
    border: 1px solid #38bdf8;
    font-weight: 700;
    font-size: 13px;
    padding: 9px 18px;
    border-radius: 7px;
}

QPushButton#btnStartCam {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #10b981);
    color: #ffffff;
    border: 1px solid #34d399;
    font-weight: 700;
    font-size: 13px;
    padding: 9px 16px;
    border-radius: 7px;
}

QPushButton#btnStopCam {
    background-color: #1e293b;
    color: #f87171;
    border: 1px solid #ef4444;
    font-weight: 700;
    font-size: 13px;
    padding: 9px 16px;
    border-radius: 7px;
}

QPushButton#btnCapture {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0891b2, stop:1 #06b6d4);
    color: #ffffff;
    border: 1px solid #22d3ee;
    font-weight: 700;
    font-size: 13px;
    padding: 9px 16px;
    border-radius: 7px;
}

QPushButton#btnAnalyze {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:0.5 #2563eb, stop:1 #4f46e5);
    color: #ffffff;
    border: 1px solid #60a5fa;
    font-weight: 800;
    font-size: 14px;
    border-radius: 7px;
    padding: 12px 24px;
    letter-spacing: 0.6px;
}

QPushButton#btnTheme {
    background-color: #1e293b;
    color: #cbd5e1;
    border: 1px solid #334155;
    font-weight: 600;
    font-size: 12px;
    padding: 6px 12px;
    border-radius: 6px;
}

QPushButton#btnTheme:hover {
    background-color: #334155;
    color: #f8fafc;
}

QComboBox {
    background-color: #0f172a;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px 12px;
    color: #f1f5f9;
}

QComboBox QAbstractItemView {
    background-color: #0f172a;
    border: 1px solid #334155;
    color: #f1f5f9;
    selection-background-color: #0284c7;
    selection-color: #ffffff;
}

QLineEdit, QSpinBox {
    background-color: #0f172a;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px 10px;
    color: #f1f5f9;
}

QCheckBox {
    spacing: 8px;
    color: #cbd5e1;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #334155;
    border-radius: 4px;
    background: #0f172a;
}

QCheckBox::indicator:checked {
    background: #0284c7;
    border-color: #00f0ff;
}

QStatusBar {
    background-color: #070c18;
    color: #94a3b8;
    border-top: 1px solid #1e293b;
    font-size: 11px;
}

QToolTip {
    background-color: #0f172a;
    color: #f8fafc;
    border: 1px solid #38bdf8;
    border-radius: 6px;
    padding: 4px 8px;
}
"""

# Default theme is the Clean Executive White Theme
DEFAULT_THEME_QSS = LIGHT_THEME_QSS
DARK_THEME_QSS = MODERN_CYBER_DARK_QSS

# =============================================================================
# Adafruit 2.8" PiTFT Touchscreen Specialized Ultra-Compact Themes (320x240)
# =============================================================================

PITFT_LIGHT_QSS = """
QMainWindow, QDialog {
    background-color: #f1f5f9;
    color: #0f172a;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Arial', sans-serif;
}

QWidget {
    color: #1e293b;
    font-size: 10px;
}

QTabWidget::pane {
    border: 1px solid #cbd5e1;
    background: #ffffff;
    border-radius: 4px;
    top: -1px;
}

QTabBar::tab {
    background: #e2e8f0;
    color: #334155;
    padding: 3px 8px;
    font-size: 10px;
    font-weight: 700;
    border: 1px solid #cbd5e1;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    min-height: 20px;
}

QTabBar::tab:selected {
    background: #2563eb;
    color: #ffffff;
    border-color: #2563eb;
}

QFrame#cardFrame, QFrame#previewFrame {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
}

QPushButton {
    background-color: #ffffff;
    color: #1e293b;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    padding: 3px 6px;
    font-weight: 700;
    font-size: 10px;
    min-height: 22px;
}

QPushButton:hover {
    background-color: #f8fafc;
    border-color: #94a3b8;
}

QPushButton:pressed {
    background-color: #e2e8f0;
}

QPushButton:disabled {
    background-color: #f1f5f9;
    color: #94a3b8;
    border-color: #e2e8f0;
}

QPushButton#btnPrimary {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563eb, stop:1 #1d4ed8);
    color: #ffffff;
    border: 1px solid #1d4ed8;
    font-weight: 700;
    font-size: 10px;
}

QPushButton#btnStartCam {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #10b981);
    color: #ffffff;
    border: 1px solid #047857;
    font-weight: 700;
}

QPushButton#btnStopCam {
    background-color: #fee2e2;
    color: #dc2626;
    border: 1px solid #fca5a5;
    font-weight: 700;
}

QPushButton#btnCapture {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0891b2, stop:1 #06b6d4);
    color: #ffffff;
    border: 1px solid #0e7490;
    font-weight: 700;
}

QPushButton#btnAnalyze {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1d4ed8, stop:1 #2563eb);
    color: #ffffff;
    border: 1px solid #1e40af;
    font-weight: 800;
    font-size: 11px;
}

QComboBox {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    padding: 2px 4px;
    color: #0f172a;
    font-size: 9px;
    min-height: 20px;
}

QCheckBox {
    spacing: 4px;
    font-size: 9px;
    color: #334155;
}

QCheckBox::indicator {
    width: 13px;
    height: 13px;
}

QStatusBar {
    background-color: #f1f5f9;
    color: #64748b;
    border-top: 1px solid #cbd5e1;
    font-size: 9px;
    max-height: 16px;
}
"""

PITFT_DARK_QSS = """
QMainWindow, QDialog {
    background-color: #070c18;
    color: #f8fafc;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Arial', sans-serif;
}

QWidget {
    color: #e2e8f0;
    font-size: 10px;
}

QTabWidget::pane {
    border: 1px solid #1e293b;
    background: #0f172a;
    border-radius: 4px;
    top: -1px;
}

QTabBar::tab {
    background: #1e293b;
    color: #94a3b8;
    padding: 3px 8px;
    font-size: 10px;
    font-weight: 700;
    border: 1px solid #334155;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    min-height: 20px;
}

QTabBar::tab:selected {
    background: #0284c7;
    color: #ffffff;
    border-color: #00f0ff;
}

QFrame#cardFrame, QFrame#previewFrame {
    background-color: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 4px;
}

QPushButton {
    background-color: #1e293b;
    color: #f8fafc;
    border: 1px solid #334155;
    border-radius: 4px;
    padding: 3px 6px;
    font-weight: 700;
    font-size: 10px;
    min-height: 22px;
}

QPushButton:hover {
    background-color: #334155;
    border-color: #00f0ff;
}

QPushButton:pressed {
    background-color: #0f172a;
}

QPushButton:disabled {
    background-color: #0b1120;
    color: #475569;
    border-color: #1e293b;
}

QPushButton#btnPrimary {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #0369a1);
    color: #ffffff;
    border: 1px solid #38bdf8;
    font-weight: 700;
}

QPushButton#btnStartCam {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #10b981);
    color: #ffffff;
    border: 1px solid #34d399;
    font-weight: 700;
}

QPushButton#btnStopCam {
    background-color: #450a0a;
    color: #f87171;
    border: 1px solid #dc2626;
    font-weight: 700;
}

QPushButton#btnCapture {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0891b2, stop:1 #06b6d4);
    color: #ffffff;
    border: 1px solid #22d3ee;
    font-weight: 700;
}

QPushButton#btnAnalyze {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #00f0ff);
    color: #070c18;
    border: 1px solid #38bdf8;
    font-weight: 800;
    font-size: 11px;
}

QComboBox {
    background-color: #0f172a;
    border: 1px solid #334155;
    border-radius: 4px;
    padding: 2px 4px;
    color: #f1f5f9;
    font-size: 9px;
    min-height: 20px;
}

QCheckBox {
    spacing: 4px;
    font-size: 9px;
    color: #cbd5e1;
}

QCheckBox::indicator {
    width: 13px;
    height: 13px;
}

QStatusBar {
    background-color: #070c18;
    color: #94a3b8;
    border-top: 1px solid #1e293b;
    font-size: 9px;
    max-height: 16px;
}
"""
