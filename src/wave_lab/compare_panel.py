"""Compact Compare Mode controls for learning through one-variable contrasts."""

from __future__ import annotations

from dataclasses import replace

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .control_panel import LabSettings
from .simulation import DiagnosticSample, StabilityReport


COMPARE_PARAMETERS = {
    "amplitude": ("Initial height", 0.1, 2.0, 0.1, " m", 1),
    "wavelength": ("Wavelength", 5.0, 50.0, 1.0, " m", 1),
    "pulse_width": ("Pulse width", 2.0, 24.0, 1.0, " m", 1),
    "wave_speed": ("Wave speed", 0.5, 10.0, 0.5, " m/s", 1),
    "damping_rate": ("Damping rate", 0.0, 1.5, 0.02, " 1/s", 3),
}


class ComparePanel(QWidget):
    """Bottom comparison strip that edits one meaningful B parameter at a time."""

    enabled_changed = Signal(bool)
    duplicate_requested = Signal()
    settings_changed = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("comparePanel")
        self._settings: LabSettings | None = None
        self._loading_value = False

        self.enabled_toggle = QCheckBox("Compare Mode")
        self.duplicate_button = QPushButton("Duplicate A into B")
        self.parameter_combo = QComboBox()
        self._populate_parameters("sinusoidal")
        self.value_spin = QDoubleSpinBox()
        self.description_label = QLabel(
            "Enable Compare Mode to overlay a synchronized B experiment."
        )
        self.description_label.setObjectName("helper")
        self.description_label.setWordWrap(True)
        self.diagnostics_label = QLabel("A is the blue solid line. B is the amber dashed line.")
        self.diagnostics_label.setObjectName("compareDiagnostics")
        self.diagnostics_label.setWordWrap(True)
        self.warning_label = QLabel()
        self.warning_label.setObjectName("compareWarning")
        self.warning_label.setWordWrap(True)
        self._build_layout()
        self._connect_signals()
        self._set_editor_enabled(False)
        self._configure_value_editor()

    @property
    def settings(self) -> LabSettings | None:
        return self._settings

    def set_duplicate(self, settings: LabSettings) -> None:
        """Copy A into B before any deliberate contrast edit."""

        self._settings = settings
        self._loading_value = True
        self._populate_parameters(settings.wave_shape)
        self._configure_value_editor()
        self._loading_value = False
        self.enabled_toggle.setChecked(True)
        self._set_editor_enabled(True)
        self.description_label.setText(
            "B now matches A. Change one B value below to isolate its effect."
        )
        self.settings_changed.emit(self._settings)

    def clear(self, message: str = "Compare Mode is off.") -> None:
        self._settings = None
        self.enabled_toggle.setChecked(False)
        self._set_editor_enabled(False)
        self.description_label.setText(message)
        self.warning_label.clear()
        self.diagnostics_label.setText("A is the blue solid line. B is the amber dashed line.")

    def update_diagnostics(
        self,
        diagnostic_a: DiagnosticSample | None,
        diagnostic_b: DiagnosticSample | None,
    ) -> None:
        if diagnostic_a is None or diagnostic_b is None:
            return
        self.diagnostics_label.setText(
            f"A blue: max |u| {diagnostic_a.maximum_amplitude:.3f} m, "
            f"energy {diagnostic_a.normalized_energy:.0%}.   "
            f"B amber: max |u| {diagnostic_b.maximum_amplitude:.3f} m, "
            f"energy {diagnostic_b.normalized_energy:.0%}."
        )

    def update_stability(self, report: StabilityReport) -> None:
        if report.is_stable:
            self.warning_label.setProperty("level", "recommended")
            self.warning_label.setText(f"Compare B is stable: CFL = {report.cfl_number:.2f}.")
        else:
            self.warning_label.setProperty("level", "error")
            self.warning_label.setText(
                f"Compare B is blocked: CFL = {report.cfl_number:.2f}. {report.messages[0]}"
            )
        self.warning_label.style().unpolish(self.warning_label)
        self.warning_label.style().polish(self.warning_label)

    def _build_layout(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 9, 12, 9)
        layout.setSpacing(6)

        header = QHBoxLayout()
        heading = QLabel("Compare experiments")
        heading.setObjectName("sectionHeading")
        header.addWidget(heading)
        header.addSpacing(8)
        header.addWidget(self.enabled_toggle)
        header.addWidget(self.duplicate_button)
        header.addStretch(1)
        layout.addLayout(header)

        controls = QGridLayout()
        controls.setHorizontalSpacing(8)
        controls.addWidget(QLabel("Change in B only:"), 0, 0)
        controls.addWidget(self.parameter_combo, 0, 1)
        controls.addWidget(self.value_spin, 0, 2)
        controls.addWidget(self.description_label, 0, 3)
        layout.addLayout(controls)
        layout.addWidget(self.diagnostics_label)
        layout.addWidget(self.warning_label)

    def _connect_signals(self) -> None:
        self.enabled_toggle.toggled.connect(self._toggle_changed)
        self.duplicate_button.clicked.connect(self.duplicate_requested)
        self.parameter_combo.currentIndexChanged.connect(self._parameter_changed)
        self.value_spin.valueChanged.connect(self._value_changed)

    def _toggle_changed(self, enabled: bool) -> None:
        if not enabled:
            self._settings = None
            self._set_editor_enabled(False)
            self.description_label.setText("Compare Mode is off.")
        self.enabled_changed.emit(enabled)

    def _parameter_changed(self) -> None:
        if self.parameter_combo.currentData() is None:
            return
        self._loading_value = True
        self._configure_value_editor()
        self._loading_value = False

    def _value_changed(self, value: float) -> None:
        if self._loading_value or self._settings is None:
            return
        parameter = self.parameter_combo.currentData()
        self._settings = replace(self._settings, **{parameter: value})
        label = COMPARE_PARAMETERS[parameter][0]
        self.description_label.setText(
            f"Only B {label.lower()} changed. Both runs restart from t = 0 "
            "for an honest comparison."
        )
        self.settings_changed.emit(self._settings)

    def _configure_value_editor(self) -> None:
        parameter = self.parameter_combo.currentData()
        _label, minimum, maximum, step, suffix, decimals = COMPARE_PARAMETERS[parameter]
        self.value_spin.setRange(minimum, maximum)
        self.value_spin.setSingleStep(step)
        self.value_spin.setSuffix(suffix)
        self.value_spin.setDecimals(decimals)
        if self._settings is not None:
            self.value_spin.setValue(getattr(self._settings, parameter))

    def _populate_parameters(self, wave_shape: str) -> None:
        current = self.parameter_combo.currentData()
        self.parameter_combo.blockSignals(True)
        self.parameter_combo.clear()
        shape_parameter = "wavelength" if wave_shape == "sinusoidal" else "pulse_width"
        for key in ("amplitude", shape_parameter, "wave_speed", "damping_rate"):
            self.parameter_combo.addItem(COMPARE_PARAMETERS[key][0], key)
        if current is not None and self.parameter_combo.findData(current) >= 0:
            self.parameter_combo.setCurrentIndex(self.parameter_combo.findData(current))
        self.parameter_combo.blockSignals(False)

    def _set_editor_enabled(self, enabled: bool) -> None:
        self.parameter_combo.setEnabled(enabled)
        self.value_spin.setEnabled(enabled)
