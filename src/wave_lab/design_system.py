"""Visual tokens and shared Qt stylesheet for the Viscous Wave Lab desktop shell."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtGui import QColor, QFont, QFontDatabase
from PySide6.QtWidgets import QApplication, QPushButton, QWidget


@dataclass(frozen=True)
class ColorTokens:
    app_background: str = "#EEF4F8"
    panel_background: str = "#FBFCFE"
    panel_raised: str = "#FFFFFF"
    canvas_background: str = "#F8FBFF"
    canvas_water: str = "#E8F6FB"
    text_primary: str = "#13202C"
    text_secondary: str = "#536575"
    text_disabled: str = "#91A0AE"
    text_on_primary: str = "#FFFFFF"
    disabled_background: str = "#EDF2F6"
    border: str = "#D7E3EA"
    border_strong: str = "#AFC1CE"
    primary: str = "#0E7C9F"
    primary_hover: str = "#075E7F"
    primary_soft: str = "#E3F4F8"
    primary_glow: str = "#66D5E7"
    comparison: str = "#D97706"
    comparison_soft: str = "#FFF1DB"
    success: str = "#177245"
    success_soft: str = "#E6F6EE"
    warning: str = "#A15C07"
    warning_soft: str = "#FFF4DE"
    error: str = "#B42318"
    error_soft: str = "#FDEBEC"
    focus: str = "#1292B8"


@dataclass(frozen=True)
class SpacingTokens:
    xsmall: int = 4
    small: int = 8
    medium: int = 12
    large: int = 16
    xlarge: int = 20


COLORS = ColorTokens()
SPACING = SpacingTokens()
FONT_FAMILY = "Lexend"
_FONT_LOADED = False


def color(name: str) -> QColor:
    """Return one semantic color for custom-painted canvases."""

    return QColor(getattr(COLORS, name))


def set_button_role(button: QPushButton, role: str) -> None:
    """Assign a semantic visual role consumed by the shared stylesheet."""

    button.setProperty("role", role)


def set_accessible_tooltip(widget: QWidget, text: str) -> None:
    """Use the same concise text for hover and status-bar guidance."""

    widget.setToolTip(text)
    widget.setStatusTip(text)


def apply_design_system(application: QApplication) -> None:
    """Apply the animated lab theme once for the whole application."""

    _load_lexend_font()
    application.setFont(QFont(FONT_FAMILY, 10))
    application.setStyleSheet(STYLESHEET)


def _load_lexend_font() -> None:
    """Register bundled Lexend weights without making startup depend on them."""

    global _FONT_LOADED
    if _FONT_LOADED:
        return
    lexend_dir = Path(__file__).resolve().parents[2] / "lexend"
    for font_file in lexend_dir.glob("Lexend-*.ttf"):
        QFontDatabase.addApplicationFont(str(font_file))
    _FONT_LOADED = True


STYLESHEET = f"""
QMainWindow, QWidget {{
    background: {COLORS.app_background};
    color: {COLORS.text_primary};
    font-family: "{FONT_FAMILY}", "Segoe UI", Arial, sans-serif;
    font-size: 12px;
}}
QLabel#heading {{ font-size: 24px; font-weight: 700; color: {COLORS.text_primary}; }}
QLabel#subtitle {{ color: {COLORS.text_secondary}; font-size: 13px; }}
QLabel#onboardingHint {{
    color: {COLORS.text_primary}; background: {COLORS.primary_soft};
    border: 1px solid {COLORS.border}; border-left: 4px solid {COLORS.primary};
    border-radius: 7px; padding: 9px 11px;
}}
QLabel#panelHeading {{ color: {COLORS.text_primary}; font-size: 16px; font-weight: 700; }}
QLabel#sectionHeading, QLabel#fieldLabel {{ color: {COLORS.text_primary}; font-weight: 600; }}
QLabel#helper {{ color: {COLORS.text_secondary}; font-size: 11px; line-height: 135%; }}
QLabel#explanationText {{ color: {COLORS.text_secondary}; }}
QLabel#equation {{
    background: {COLORS.primary_soft}; color: {COLORS.text_primary}; border-radius: 6px;
    border: 1px solid {COLORS.border}; padding: 11px; font-family: Consolas, monospace;
    font-size: 14px;
}}
QLabel#changedText {{ color: {COLORS.primary}; }}
QLabel#interpretationText, QLabel#diagnosticsSummary {{ color: {COLORS.text_primary}; }}
QLabel#compareDiagnostics {{ color: {COLORS.text_secondary}; }}
QLabel#stability, QLabel#explanationWarning, QLabel#diagnosticsStability,
QLabel#compareWarning {{ padding: 7px 9px; border-radius: 6px; }}
QLabel[level="recommended"] {{ color: {COLORS.success}; background: {COLORS.success_soft}; }}
QLabel[level="caution"] {{ color: {COLORS.warning}; background: {COLORS.warning_soft}; }}
QLabel[level="error"] {{ color: {COLORS.error}; background: {COLORS.error_soft}; }}
QWidget#controlPanel, QWidget#explanationPanel, QWidget#comparePanel,
QWidget#diagnosticsPanel {{
    background: {COLORS.panel_background}; border: 1px solid {COLORS.border};
    border-radius: 8px;
}}
QGroupBox {{
    border: 1px solid {COLORS.border}; border-radius: 7px; margin-top: 8px;
    padding: 9px 7px 7px 7px; font-weight: 650; background: {COLORS.panel_raised};
}}
QGroupBox::title {{ subcontrol-origin: margin; left: 9px; padding: 0 5px; }}
QFrame {{ color: {COLORS.border}; }}
QScrollArea {{ border: none; background: transparent; }}
QPushButton {{
    background: {COLORS.panel_raised}; border: 1px solid {COLORS.border_strong};
    border-radius: 7px; padding: 8px 14px; color: {COLORS.text_primary};
    min-height: 20px;
}}
QPushButton:hover {{ border-color: {COLORS.primary}; background: {COLORS.primary_soft}; }}
QPushButton:pressed {{ background: {COLORS.primary_soft}; }}
QPushButton:focus {{
    border: 2px solid {COLORS.focus}; padding: 7px 13px;
}}
QPushButton:disabled {{
    color: {COLORS.text_disabled}; background: {COLORS.disabled_background};
    border-color: {COLORS.border};
}}
QPushButton[role="primary"] {{
    color: {COLORS.text_on_primary}; background: {COLORS.primary}; border-color: {COLORS.primary};
    font-weight: 700;
}}
QPushButton[role="primary"]:hover {{
    color: {COLORS.text_on_primary}; background: {COLORS.primary_hover};
    border-color: {COLORS.primary_hover};
}}
QPushButton[role="ghost"] {{ border-color: transparent; color: {COLORS.primary}; }}
QPushButton[role="warning"] {{
    color: {COLORS.warning}; background: {COLORS.warning_soft}; border-color: {COLORS.warning};
}}
QComboBox, QSpinBox, QDoubleSpinBox {{
    background: {COLORS.panel_raised}; color: {COLORS.text_primary};
    border: 1px solid {COLORS.border_strong}; border-radius: 6px;
    padding: 6px 8px; min-height: 22px;
}}
QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover {{ border-color: {COLORS.primary}; }}
QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
    border: 2px solid {COLORS.focus}; padding: 5px 7px;
}}
QCheckBox {{ spacing: 6px; }}
QCheckBox::indicator {{
    width: 16px; height: 16px; border: 1px solid {COLORS.border_strong};
    border-radius: 5px; background: {COLORS.panel_raised};
}}
QCheckBox::indicator:checked {{ background: {COLORS.primary}; border-color: {COLORS.primary}; }}
QCheckBox:focus {{ color: {COLORS.primary}; }}
QToolTip {{
    color: {COLORS.text_on_primary}; background: {COLORS.text_primary};
    border: 1px solid {COLORS.text_primary};
    padding: 5px;
}}
QStatusBar {{ color: {COLORS.text_secondary}; background: {COLORS.panel_background}; }}
QMenuBar, QMenu {{
    background: {COLORS.panel_background}; color: {COLORS.text_primary};
}}
QMenu::item:selected {{ background: {COLORS.primary_soft}; color: {COLORS.primary_hover}; }}
"""
