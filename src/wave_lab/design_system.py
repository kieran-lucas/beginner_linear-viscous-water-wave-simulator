"""Visual tokens and shared Qt stylesheet for the Viscous Wave Lab desktop shell."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication, QPushButton, QWidget


@dataclass(frozen=True)
class ColorTokens:
    app_background: str = "#F4F7FA"
    panel_background: str = "#FFFFFF"
    canvas_background: str = "#FFFFFF"
    text_primary: str = "#172033"
    text_secondary: str = "#5B667A"
    text_disabled: str = "#8C97A8"
    text_on_primary: str = "#FFFFFF"
    disabled_background: str = "#EEF1F5"
    border: str = "#DCE2EA"
    border_strong: str = "#B8C4D3"
    primary: str = "#1769AA"
    primary_hover: str = "#12588F"
    primary_soft: str = "#EAF2F8"
    comparison: str = "#C77C18"
    success: str = "#26734D"
    success_soft: str = "#EAF5EF"
    warning: str = "#A76500"
    warning_soft: str = "#FFF6E5"
    error: str = "#B42318"
    error_soft: str = "#FDECEA"
    focus: str = "#0B75C9"


@dataclass(frozen=True)
class SpacingTokens:
    xsmall: int = 4
    small: int = 8
    medium: int = 12
    large: int = 16
    xlarge: int = 20


COLORS = ColorTokens()
SPACING = SpacingTokens()


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
    """Apply the calm scientific desktop theme once for the whole application."""

    application.setStyleSheet(STYLESHEET)


STYLESHEET = f"""
QMainWindow, QWidget {{
    background: {COLORS.app_background};
    color: {COLORS.text_primary};
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 12px;
}}
QLabel#heading {{ font-size: 20px; font-weight: 650; color: {COLORS.text_primary}; }}
QLabel#subtitle {{ color: {COLORS.text_secondary}; font-size: 13px; }}
QLabel#panelHeading {{ font-size: 15px; font-weight: 650; }}
QLabel#sectionHeading, QLabel#fieldLabel {{ font-weight: 600; }}
QLabel#helper {{ color: {COLORS.text_secondary}; font-size: 11px; }}
QLabel#equation {{
    background: {COLORS.primary_soft}; color: {COLORS.text_primary}; border-radius: 3px;
    padding: 9px; font-family: Consolas, monospace; font-size: 14px;
}}
QLabel#changedText {{ color: {COLORS.primary}; }}
QLabel#interpretationText, QLabel#diagnosticsSummary {{ color: {COLORS.text_primary}; }}
QLabel#compareDiagnostics {{ color: {COLORS.text_secondary}; }}
QLabel#stability, QLabel#explanationWarning, QLabel#diagnosticsStability,
QLabel#compareWarning {{ padding: 5px; border-radius: 3px; }}
QLabel[level="recommended"] {{ color: {COLORS.success}; background: {COLORS.success_soft}; }}
QLabel[level="caution"] {{ color: {COLORS.warning}; background: {COLORS.warning_soft}; }}
QLabel[level="error"] {{ color: {COLORS.error}; background: {COLORS.error_soft}; }}
QWidget#controlPanel, QWidget#explanationPanel, QWidget#comparePanel,
QWidget#diagnosticsPanel {{
    background: {COLORS.panel_background}; border: 1px solid {COLORS.border};
    border-radius: 5px;
}}
QGroupBox {{
    border: 1px solid {COLORS.border}; border-radius: 4px; margin-top: 7px;
    padding-top: 7px; font-weight: 600; background: {COLORS.panel_background};
}}
QGroupBox::title {{ subcontrol-origin: margin; left: 7px; padding: 0 3px; }}
QFrame {{ color: {COLORS.border}; }}
QScrollArea {{ border: none; background: transparent; }}
QPushButton {{
    background: {COLORS.panel_background}; border: 1px solid {COLORS.border_strong};
    border-radius: 4px; padding: 7px 14px; color: {COLORS.text_primary};
}}
QPushButton:hover {{ border-color: {COLORS.primary}; background: {COLORS.primary_soft}; }}
QPushButton:pressed {{ background: {COLORS.primary_soft}; }}
QPushButton:focus {{
    border: 2px solid {COLORS.focus}; padding: 6px 13px;
}}
QPushButton:disabled {{
    color: {COLORS.text_disabled}; background: {COLORS.disabled_background};
    border-color: {COLORS.border};
}}
QPushButton[role="primary"] {{
    color: {COLORS.text_on_primary}; background: {COLORS.primary}; border-color: {COLORS.primary};
    font-weight: 600;
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
    background: {COLORS.panel_background}; color: {COLORS.text_primary};
    border: 1px solid {COLORS.border_strong}; border-radius: 3px;
    padding: 5px 7px; min-height: 18px;
}}
QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover {{ border-color: {COLORS.primary}; }}
QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
    border: 2px solid {COLORS.focus}; padding: 4px 6px;
}}
QCheckBox {{ spacing: 6px; }}
QCheckBox::indicator {{
    width: 15px; height: 15px; border: 1px solid {COLORS.border_strong};
    border-radius: 3px; background: {COLORS.panel_background};
}}
QCheckBox::indicator:checked {{ background: {COLORS.primary}; border-color: {COLORS.primary}; }}
QCheckBox:focus {{ color: {COLORS.primary}; }}
QToolTip {{
    color: {COLORS.text_on_primary}; background: {COLORS.text_primary};
    border: 1px solid {COLORS.text_primary};
    padding: 5px;
}}
QStatusBar {{ color: {COLORS.text_secondary}; background: {COLORS.panel_background}; }}
"""
