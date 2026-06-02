"""Beginner-friendly controls and presets for the Viscous Wave Lab desktop app."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from .simulation import BoundaryCondition, InitialCondition, SimulationParameters, check_stability


@dataclass(frozen=True)
class LabSettings:
    """Values selected in the control panel, including playback speed."""

    wave_shape: str = "sinusoidal"
    amplitude: float = 0.6
    wavelength: float = 16.0
    pulse_width: float = 8.0
    wave_speed: float = 3.0
    damping_rate: float = 0.08
    playback_speed: float = 1.0
    domain_length: float = 100.0
    grid_points: int = 401
    time_step: float = 0.01
    boundary: BoundaryCondition = BoundaryCondition.FIXED

    def simulation_parameters(self) -> SimulationParameters:
        return SimulationParameters(
            domain_length=self.domain_length,
            grid_points=self.grid_points,
            wave_speed=self.wave_speed,
            damping_rate=self.damping_rate,
            time_step=self.time_step,
            boundary=self.boundary,
        )

    def initial_condition(self) -> InitialCondition:
        return InitialCondition(
            kind=self.wave_shape,
            amplitude=self.amplitude,
            wavelength=self.wavelength,
            width=self.pulse_width,
        )


@dataclass(frozen=True)
class Preset:
    """A meaningful starting experiment and its teaching purpose."""

    name: str
    description: str
    settings: LabSettings
    stability_demo: bool = False


PRESETS = (
    Preset(
        "Gentle ripple",
        "A small repeating wave with light damping. Start here.",
        LabSettings(),
    ),
    Preset(
        "Long smooth wave",
        "A broad repeating wave makes wavelength easy to see.",
        LabSettings(amplitude=0.8, wavelength=32.0, wave_speed=3.0, damping_rate=0.06),
    ),
    Preset(
        "Strong damping",
        "The wave loses amplitude quickly as damping removes energy.",
        LabSettings(amplitude=1.0, wavelength=20.0, wave_speed=3.0, damping_rate=0.8),
    ),
    Preset(
        "Almost no damping",
        "The wave keeps most of its amplitude over the same time interval.",
        LabSettings(amplitude=0.8, wavelength=20.0, wave_speed=3.0, damping_rate=0.005),
    ),
    Preset(
        "Fast propagation",
        "A higher wave speed moves peaks across the domain more quickly.",
        LabSettings(amplitude=0.7, wavelength=20.0, wave_speed=8.0, damping_rate=0.08),
    ),
    Preset(
        "Stability risk demo",
        "Advanced demonstration only: the time step is intentionally too large.",
        LabSettings(
            amplitude=0.7,
            wavelength=20.0,
            wave_speed=8.0,
            damping_rate=0.08,
            time_step=0.08,
        ),
        stability_demo=True,
    ),
)


class ControlPanel(QWidget):
    """Left-side controls with simple defaults and advanced numerical disclosure."""

    settings_changed = Signal(object)
    play_pause_requested = Signal()
    reset_requested = Signal()
    step_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("controlPanel")
        self.setFixedWidth(300)
        self._loading_values = False
        self._playback_available = True

        self.preset_combo = QComboBox()
        for preset in PRESETS:
            suffix = " - advanced warning" if preset.stability_demo else ""
            self.preset_combo.addItem(preset.name + suffix, preset)
        self.preset_description = self._helper("")

        self.shape_combo = QComboBox()
        self.shape_combo.addItem("Repeating wave", "sinusoidal")
        self.shape_combo.addItem("Gaussian pulse", "gaussian")
        self.amplitude_spin = self._double_spin(0.1, 2.0, 0.1, " m")
        self.wavelength_spin = self._double_spin(5.0, 50.0, 1.0, " m")
        self.pulse_width_spin = self._double_spin(2.0, 24.0, 1.0, " m")
        self.wave_speed_spin = self._double_spin(0.5, 10.0, 0.5, " m/s")
        self.damping_spin = self._double_spin(0.0, 1.5, 0.02, " 1/s", decimals=3)
        self.playback_combo = QComboBox()
        for label, multiplier in (("0.5x", 0.5), ("1x", 1.0), ("2x", 2.0)):
            self.playback_combo.addItem(label, multiplier)

        self.advanced_toggle = QCheckBox("Show advanced numerics")
        self.advanced_frame = QFrame()
        self.grid_points_spin = QSpinBox()
        self.grid_points_spin.setRange(101, 801)
        self.grid_points_spin.setSingleStep(50)
        self.time_step_spin = self._double_spin(0.001, 0.1, 0.001, " s", decimals=3)
        self.boundary_combo = QComboBox()
        self.boundary_combo.addItem("Fixed ends", BoundaryCondition.FIXED)
        self.boundary_combo.addItem("Reflective edges", BoundaryCondition.REFLECTIVE)
        self.boundary_combo.addItem("Periodic wraparound", BoundaryCondition.PERIODIC)
        self.stability_label = QLabel()
        self.stability_label.setWordWrap(True)
        self.stability_label.setObjectName("stability")

        self.play_button = QPushButton("Play")
        self.reset_button = QPushButton("Reset")
        self.step_button = QPushButton("Step")
        self._build_layout()
        self._connect_signals()
        self.load_preset(PRESETS[0])

    @property
    def settings(self) -> LabSettings:
        return LabSettings(
            wave_shape=self.shape_combo.currentData(),
            amplitude=self.amplitude_spin.value(),
            wavelength=self.wavelength_spin.value(),
            pulse_width=self.pulse_width_spin.value(),
            wave_speed=self.wave_speed_spin.value(),
            damping_rate=self.damping_spin.value(),
            playback_speed=self.playback_combo.currentData(),
            grid_points=self.grid_points_spin.value(),
            time_step=self.time_step_spin.value(),
            boundary=self.boundary_combo.currentData(),
        )

    def set_running(self, running: bool) -> None:
        self.play_button.setText("Pause" if running else "Play")

    def set_playback_available(self, available: bool) -> None:
        self._playback_available = available
        self.play_button.setEnabled(available)
        self.step_button.setEnabled(available)

    def load_preset(self, preset: Preset) -> None:
        settings = preset.settings
        self._loading_values = True
        self.shape_combo.setCurrentIndex(self.shape_combo.findData(settings.wave_shape))
        self.amplitude_spin.setValue(settings.amplitude)
        self.wavelength_spin.setValue(settings.wavelength)
        self.pulse_width_spin.setValue(settings.pulse_width)
        self.wave_speed_spin.setValue(settings.wave_speed)
        self.damping_spin.setValue(settings.damping_rate)
        self.playback_combo.setCurrentIndex(
            self.playback_combo.findData(settings.playback_speed)
        )
        self.grid_points_spin.setValue(settings.grid_points)
        self.time_step_spin.setValue(settings.time_step)
        self.boundary_combo.setCurrentIndex(self.boundary_combo.findData(settings.boundary))
        self.advanced_toggle.setChecked(preset.stability_demo)
        self.preset_description.setText(preset.description)
        self._loading_values = False
        self._update_shape_controls()
        self._emit_settings()

    def _build_layout(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        heading = QLabel("Experiment controls")
        heading.setObjectName("panelHeading")
        layout.addWidget(heading)
        layout.addWidget(self._group("Presets", self._preset_layout()))
        layout.addWidget(self._group("Initial wave", self._initial_wave_layout()))
        layout.addWidget(self._group("Medium", self._medium_layout()))
        layout.addWidget(self._group("Playback", self._playback_layout()))
        layout.addWidget(self.advanced_toggle)
        layout.addWidget(self.advanced_frame)
        layout.addStretch(1)
        self.advanced_frame.setVisible(False)

    def _preset_layout(self) -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.addWidget(self.preset_combo)
        layout.addWidget(self.preset_description)
        return layout

    def _initial_wave_layout(self) -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.addWidget(
            self._field("Wave shape", self.shape_combo, "Choose one pulse or repeating peaks.")
        )
        layout.addWidget(
            self._field(
                "Initial height",
                self.amplitude_spin,
                "Taller waves start with more energy.",
            )
        )
        self.wavelength_field = self._field(
            "Wavelength", self.wavelength_spin, "Longer wavelengths place peaks farther apart."
        )
        self.pulse_width_field = self._field(
            "Pulse width",
            self.pulse_width_spin,
            "A wider disturbance spreads across more distance.",
        )
        layout.addWidget(self.wavelength_field)
        layout.addWidget(self.pulse_width_field)
        return layout

    def _medium_layout(self) -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.addWidget(
            self._field("Wave speed", self.wave_speed_spin, "Higher values move peaks faster.")
        )
        layout.addWidget(
            self._field(
                "Damping rate",
                self.damping_spin,
                "Higher damping removes amplitude and energy more quickly. "
                "It represents simplified viscous loss.",
            )
        )
        return layout

    def _playback_layout(self) -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.addWidget(
            self._field(
                "Simulation speed",
                self.playback_combo,
                "Changes playback pace without changing the physics.",
            )
        )
        buttons = QGridLayout()
        buttons.addWidget(self.play_button, 0, 0, 1, 2)
        buttons.addWidget(self.reset_button, 1, 0)
        buttons.addWidget(self.step_button, 1, 1)
        layout.addLayout(buttons)
        return layout

    def _advanced_layout(self) -> QVBoxLayout:
        layout = QVBoxLayout()
        heading = QLabel("Advanced numerics")
        heading.setObjectName("sectionHeading")
        layout.addWidget(heading)
        layout.addWidget(
            self._field(
                "Grid points",
                self.grid_points_spin,
                "More points resolve smaller details but require more work.",
            )
        )
        layout.addWidget(
            self._field(
                "Time step",
                self.time_step_spin,
                "Smaller steps improve reliability but take longer to compute.",
            )
        )
        layout.addWidget(
            self._field(
                "Boundary behavior",
                self.boundary_combo,
                "Controls what happens when a wave reaches an edge.",
            )
        )
        method = QLabel("Numerical method: RK4 with centered spatial differences")
        method.setWordWrap(True)
        method.setObjectName("helper")
        layout.addWidget(method)
        layout.addWidget(self.stability_label)
        return layout

    def _connect_signals(self) -> None:
        self.preset_combo.currentIndexChanged.connect(self._preset_selected)
        self.shape_combo.currentIndexChanged.connect(self._control_changed)
        for spin in (
            self.amplitude_spin,
            self.wavelength_spin,
            self.pulse_width_spin,
            self.wave_speed_spin,
            self.damping_spin,
            self.grid_points_spin,
            self.time_step_spin,
        ):
            spin.valueChanged.connect(self._control_changed)
        self.playback_combo.currentIndexChanged.connect(self._control_changed)
        self.boundary_combo.currentIndexChanged.connect(self._control_changed)
        self.advanced_toggle.toggled.connect(self.advanced_frame.setVisible)
        self.play_button.clicked.connect(self.play_pause_requested)
        self.reset_button.clicked.connect(self.reset_requested)
        self.step_button.clicked.connect(self.step_requested)
        self.advanced_frame.setLayout(self._advanced_layout())

    def _preset_selected(self) -> None:
        if not self._loading_values:
            self.load_preset(self.preset_combo.currentData())

    def _control_changed(self) -> None:
        if self._loading_values:
            return
        self.preset_description.setText(
            "Custom experiment. Adjust one value and observe the effect."
        )
        self._update_shape_controls()
        self._emit_settings()

    def _emit_settings(self) -> None:
        report = check_stability(self.settings.simulation_parameters())
        if report.is_stable:
            qualifier = (
                "Recommended"
                if not report.messages[0].startswith("CFL number is close")
                else "Caution"
            )
            self.stability_label.setProperty("level", qualifier.lower())
            self.stability_label.setText(
                f"{qualifier}: CFL = {report.cfl_number:.2f}. {report.messages[0]}"
            )
        else:
            self.stability_label.setProperty("level", "error")
            self.stability_label.setText(
                f"Playback blocked: CFL = {report.cfl_number:.2f}. {report.messages[0]}"
            )
        self.stability_label.style().unpolish(self.stability_label)
        self.stability_label.style().polish(self.stability_label)
        self.settings_changed.emit(self.settings)

    def _update_shape_controls(self) -> None:
        repeating = self.shape_combo.currentData() == "sinusoidal"
        self.wavelength_field.setVisible(repeating)
        self.pulse_width_field.setVisible(not repeating)

    @staticmethod
    def _double_spin(
        minimum: float,
        maximum: float,
        step: float,
        suffix: str,
        *,
        decimals: int = 1,
    ) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(minimum, maximum)
        spin.setSingleStep(step)
        spin.setDecimals(decimals)
        spin.setSuffix(suffix)
        return spin

    @staticmethod
    def _helper(text: str) -> QLabel:
        label = QLabel(text)
        label.setWordWrap(True)
        label.setObjectName("helper")
        return label

    @classmethod
    def _field(cls, label_text: str, control: QWidget, helper_text: str) -> QWidget:
        field = QWidget()
        layout = QVBoxLayout(field)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)
        label = QLabel(label_text)
        label.setObjectName("fieldLabel")
        layout.addWidget(label)
        layout.addWidget(control)
        layout.addWidget(cls._helper(helper_text))
        return field

    @staticmethod
    def _group(title: str, content: QVBoxLayout) -> QGroupBox:
        group = QGroupBox(title)
        group.setLayout(content)
        return group
