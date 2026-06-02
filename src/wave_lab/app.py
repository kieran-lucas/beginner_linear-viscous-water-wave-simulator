"""Minimal desktop shell for exploring the real-time wave canvas."""

from __future__ import annotations

import sys
from time import perf_counter

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from .compare_panel import ComparePanel
from .control_panel import ControlPanel, LabSettings
from .diagnostics_panel import DiagnosticsPanel
from .explanation_panel import ExplanationPanel
from .simulation import WaveSimulation, check_stability
from .visualization import WaveCanvas


class MainWindow(QMainWindow):
    """Desktop preview focused on profile visualization and playback."""

    RENDER_INTERVAL_MS = 33
    BASE_SOLVER_STEPS_PER_FRAME = 3

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Viscous Wave Lab")
        self.resize(1320, 820)

        self.controls = ControlPanel()
        self.simulation = WaveSimulation(
            self.controls.settings.simulation_parameters(),
            self.controls.settings.initial_condition(),
        )
        self.canvas = WaveCanvas()
        self.explanation = ExplanationPanel()
        self.compare = ComparePanel()
        self.diagnostics = DiagnosticsPanel()
        self.compare_simulation: WaveSimulation | None = None
        self._render_frames = 0
        self._render_rate_started = perf_counter()

        self.state_label = QLabel()
        self.state_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.controls.settings_changed.connect(self._apply_settings)
        self.controls.concept_selected.connect(self.explanation.show_concept)
        self.controls.preset_selected.connect(self.explanation.show_preset)
        self.controls.play_pause_requested.connect(self._toggle_playback)
        self.controls.step_requested.connect(self._step)
        self.controls.reset_requested.connect(self._reset)
        self.controls.advanced_toggle.toggled.connect(self.diagnostics.set_advanced_visible)
        self.compare.enabled_changed.connect(self._toggle_compare)
        self.compare.duplicate_requested.connect(self._duplicate_compare)
        self.compare.settings_changed.connect(self._apply_compare_settings)

        timer = QTimer(self)
        timer.setInterval(self.RENDER_INTERVAL_MS)
        timer.timeout.connect(self._advance_frame)
        timer.start()
        self._timer = timer

        self._build_layout()
        self._refresh_canvas()

    def _build_layout(self) -> None:
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        heading = QLabel("Viscous Wave Lab")
        heading.setObjectName("heading")
        subtitle = QLabel(
            "Watch a linear wave propagate and lose energy as damping acts over time."
        )
        subtitle.setObjectName("subtitle")
        layout.addWidget(heading)
        layout.addWidget(subtitle)
        content = QHBoxLayout()
        content.setSpacing(14)
        controls_scroll = QScrollArea()
        controls_scroll.setWidget(self.controls)
        controls_scroll.setWidgetResizable(False)
        controls_scroll.setFixedWidth(318)
        controls_scroll.setFrameShape(QFrame.Shape.NoFrame)
        content.addWidget(controls_scroll)
        content.addWidget(self.canvas, stretch=1)
        explanation_scroll = QScrollArea()
        explanation_scroll.setWidget(self.explanation)
        explanation_scroll.setWidgetResizable(False)
        explanation_scroll.setFixedWidth(318)
        explanation_scroll.setFrameShape(QFrame.Shape.NoFrame)
        content.addWidget(explanation_scroll)
        layout.addLayout(content, stretch=1)
        layout.addWidget(self.compare)
        layout.addWidget(self.diagnostics)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(separator)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        toolbar.addStretch(1)
        toolbar.addWidget(self.state_label)
        layout.addLayout(toolbar)
        self.setCentralWidget(central)

        self.setStyleSheet(
            """
            QMainWindow, QWidget { background: #F7F8FA; color: #172033; }
            QLabel#heading { font-size: 20px; font-weight: 650; }
            QLabel#subtitle { color: #5B667A; font-size: 13px; }
            QWidget#controlPanel {
                background: #FFFFFF; border: 1px solid #DCE2EA; border-radius: 5px;
            }
            QWidget#explanationPanel {
                background: #FFFFFF; border: 1px solid #DCE2EA; border-radius: 5px;
            }
            QWidget#comparePanel {
                background: #FFFFFF; border: 1px solid #DCE2EA; border-radius: 5px;
            }
            QWidget#diagnosticsPanel {
                background: #FFFFFF; border: 1px solid #DCE2EA; border-radius: 5px;
            }
            QLabel#panelHeading { font-size: 15px; font-weight: 650; }
            QLabel#sectionHeading, QLabel#fieldLabel { font-weight: 600; }
            QLabel#helper { color: #5B667A; font-size: 11px; }
            QLabel#equation {
                background: #EEF4F8; color: #172033; border-radius: 3px;
                padding: 9px; font-family: Consolas; font-size: 14px;
            }
            QLabel#changedText { color: #1769AA; }
            QLabel#interpretationText { color: #172033; }
            QLabel#explanationWarning { padding: 7px; border-radius: 3px; }
            QLabel#explanationWarning[level="recommended"] {
                color: #26734D; background: #EAF5EF;
            }
            QLabel#explanationWarning[level="caution"] {
                color: #A76500; background: #FFF6E5;
            }
            QLabel#explanationWarning[level="error"] {
                color: #B42318; background: #FDECEA;
            }
            QLabel#compareDiagnostics { color: #5B667A; }
            QLabel#compareWarning { padding: 4px; border-radius: 3px; }
            QLabel#compareWarning[level="recommended"] { color: #26734D; }
            QLabel#compareWarning[level="error"] { color: #B42318; background: #FDECEA; }
            QLabel#diagnosticsSummary { color: #172033; }
            QLabel#diagnosticsStability { padding: 4px; border-radius: 3px; }
            QLabel#diagnosticsStability[level="recommended"] { color: #26734D; }
            QLabel#diagnosticsStability[level="caution"] {
                color: #A76500; background: #FFF6E5;
            }
            QLabel#diagnosticsStability[level="error"] {
                color: #B42318; background: #FDECEA;
            }
            QLabel#stability { padding: 7px; border-radius: 3px; }
            QLabel#stability[level="recommended"] { color: #26734D; background: #EAF5EF; }
            QLabel#stability[level="caution"] { color: #A76500; background: #FFF6E5; }
            QLabel#stability[level="error"] { color: #B42318; background: #FDECEA; }
            QGroupBox {
                border: 1px solid #DCE2EA; border-radius: 4px; margin-top: 7px;
                padding-top: 7px; font-weight: 600;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 7px; padding: 0 3px; }
            QPushButton {
                background: #FFFFFF; border: 1px solid #C9D2DF; border-radius: 4px;
                padding: 7px 14px; color: #172033;
            }
            QPushButton:hover { border-color: #1769AA; }
            QPushButton:pressed { background: #EAF2F8; }
            QFrame { color: #DCE2EA; }
            """
        )

    def _toggle_playback(self) -> None:
        if self.simulation.state.paused:
            self.simulation.resume()
            if self.compare_simulation is not None:
                self.compare_simulation.resume()
        else:
            self.simulation.pause()
            if self.compare_simulation is not None:
                self.compare_simulation.pause()
        self.controls.set_running(not self.simulation.state.paused)
        self._refresh_status()

    def _advance_frame(self) -> None:
        multiplier = self.controls.settings.playback_speed
        steps = max(1, round(self.BASE_SOLVER_STEPS_PER_FRAME * multiplier))
        self.simulation.run(steps)
        if self.compare_simulation is not None:
            self.compare_simulation.run(steps)
        if not self.simulation.state.paused:
            self._refresh_canvas()
            self._record_render_frame()

    def _step(self) -> None:
        self.simulation.step()
        if self.compare_simulation is not None:
            self.compare_simulation.step()
        self._refresh_canvas()

    def _reset(self) -> None:
        self.simulation.reset()
        self.simulation.pause()
        if self.compare_simulation is not None:
            self.compare_simulation.reset()
            self.compare_simulation.pause()
        self.controls.set_running(False)
        self._refresh_canvas()

    def _apply_settings(self, settings: LabSettings) -> None:
        parameters = settings.simulation_parameters()
        report = check_stability(parameters)
        self.explanation.update_stability(report)
        if (
            report.is_stable
            and parameters == self.simulation.parameters
            and settings.initial_condition() == self.simulation.initial_condition
        ):
            self._refresh_status()
            return
        self.simulation.pause()
        self.controls.set_running(False)
        self.controls.set_playback_available(report.is_stable)
        self._disable_compare("A changed. Duplicate A into B again to start a new comparison.")
        if report.is_stable:
            self.simulation = WaveSimulation(parameters, settings.initial_condition())
            self._refresh_canvas()
        else:
            self._refresh_status(report.messages[0])

    def _refresh_canvas(self) -> None:
        initial = self.simulation.initial_condition
        self.canvas.set_wave_data(
            self.simulation.parameters.positions,
            self.simulation.state.displacement,
            self.simulation.state.diagnostics,
            initial_amplitude=initial.amplitude,
            wavelength=initial.wavelength if initial.kind == "sinusoidal" else None,
        )
        if self.compare_simulation is None:
            self.canvas.set_comparison_data(None)
        else:
            compare_initial = self.compare_simulation.initial_condition
            self.canvas.set_comparison_data(
                self.compare_simulation.state.displacement,
                self.compare_simulation.state.diagnostics,
                initial_amplitude=compare_initial.amplitude,
            )
            self.compare.update_diagnostics(
                self.simulation.state.diagnostics,
                self.compare_simulation.state.diagnostics,
            )
        self.explanation.update_interpretation(
            self.simulation.state.diagnostics,
            self.simulation.parameters.damping_rate,
        )
        self.explanation.update_stability(self.simulation.stability)
        compare_history = (
            self.compare_simulation.state.history
            if self.compare_simulation is not None
            else None
        )
        self.diagnostics.update_data(
            self.simulation.state.history,
            self.simulation.stability,
            compare_history,
        )
        self._refresh_status()

    def _toggle_compare(self, enabled: bool) -> None:
        if enabled and self.compare.settings is None:
            self._duplicate_compare()
            return
        if not enabled:
            self.compare_simulation = None
            self.canvas.set_comparison_data(None)
            self.controls.set_playback_available(self.simulation.stability.is_stable)
            self._refresh_status()

    def _duplicate_compare(self) -> None:
        self.compare.set_duplicate(self.controls.settings)

    def _apply_compare_settings(self, settings: LabSettings) -> None:
        parameters = settings.simulation_parameters()
        report = check_stability(parameters)
        self.compare.update_stability(report)
        self.simulation.pause()
        self.controls.set_running(False)
        self.controls.set_playback_available(report.is_stable)
        if not report.is_stable:
            self.compare_simulation = None
            self.canvas.set_comparison_data(None)
            self._refresh_status(report.messages[0])
            return

        self.simulation.reset()
        self.simulation.pause()
        self.compare_simulation = WaveSimulation(parameters, settings.initial_condition())
        self.compare_simulation.pause()
        self._refresh_canvas()

    def _disable_compare(self, message: str) -> None:
        if self.compare.settings is None and self.compare_simulation is None:
            return
        self.compare_simulation = None
        self.canvas.set_comparison_data(None)
        self.compare.clear(message)

    def _refresh_status(self, warning: str | None = None) -> None:
        if warning:
            self.state_label.setText(f"Playback blocked   {warning}")
            return
        state = "Paused" if self.simulation.state.paused else "Running"
        self.state_label.setText(
            f"{state}   damping rate = {self.simulation.parameters.damping_rate:.2f} 1/s   "
            f"CFL = {self.simulation.stability.cfl_number:.2f}"
        )

    def _record_render_frame(self) -> None:
        self._render_frames += 1
        elapsed = perf_counter() - self._render_rate_started
        if elapsed < 1.0:
            return
        self.diagnostics.set_render_rate(self._render_frames / elapsed)
        self._render_frames = 0
        self._render_rate_started = perf_counter()


def main() -> int:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
