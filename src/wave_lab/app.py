"""Minimal desktop shell for exploring the real-time wave canvas."""

from __future__ import annotations

import sys
from time import perf_counter

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QKeySequence, QShortcut
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
from .design_system import apply_design_system, set_accessible_tooltip
from .explanation_panel import ExplanationPanel
from .runtime import AppConfig, RuntimeController
from .simulation import WaveSimulation
from .visualization import WaveCanvas


class MainWindow(QMainWindow):
    """Desktop preview focused on profile visualization and playback."""

    RENDER_INTERVAL_MS = 33
    BASE_SOLVER_STEPS_PER_FRAME = 3

    def __init__(self) -> None:
        super().__init__()
        application = QApplication.instance()
        if application is not None:
            apply_design_system(application)
        self.setWindowTitle("Viscous Wave Lab")
        self.resize(1320, 820)

        self.controls = ControlPanel()
        self.runtime = RuntimeController(
            self.controls.settings,
            AppConfig(
                render_interval_ms=self.RENDER_INTERVAL_MS,
                base_solver_steps_per_frame=self.BASE_SOLVER_STEPS_PER_FRAME,
            ),
        )
        self.canvas = WaveCanvas()
        self.explanation = ExplanationPanel()
        self.compare = ComparePanel()
        self.diagnostics = DiagnosticsPanel()
        self._render_frames = 0
        self._render_rate_started = perf_counter()

        self.state_label = QLabel()
        self.state_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.controls.settings_changed.connect(self._apply_settings)
        self.controls.concept_selected.connect(self._show_concept)
        self.controls.preset_selected.connect(self.explanation.show_preset)
        self.controls.play_pause_requested.connect(self._toggle_playback)
        self.controls.step_requested.connect(self._step)
        self.controls.reset_requested.connect(self._reset)
        self.controls.advanced_toggle.toggled.connect(self._set_advanced_mode)
        self.compare.enabled_changed.connect(self._toggle_compare)
        self.compare.duplicate_requested.connect(self._duplicate_compare)
        self.compare.settings_changed.connect(self._apply_compare_settings)
        self.diagnostics.expanded_changed.connect(self.runtime.set_diagnostics_expanded)

        timer = QTimer(self)
        timer.setInterval(self.runtime.config.render_interval_ms)
        timer.timeout.connect(self._advance_frame)
        timer.start()
        self._timer = timer

        self._build_layout()
        self._install_shortcuts()
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

        self.statusBar().showMessage(
            "Ready. Space: play or pause   Right arrow: step   Ctrl+R: reset",
        )
        set_accessible_tooltip(self.canvas, "Wave profile. Hover to inspect position and height.")

    def _install_shortcuts(self) -> None:
        shortcuts = (
            ("Space", self._toggle_playback),
            ("Right", self._step),
            ("Ctrl+R", self._reset),
            ("Ctrl+D", self._duplicate_compare),
            ("Ctrl+G", self.diagnostics._toggle_graphs),
        )
        self._shortcuts = []
        for key, callback in shortcuts:
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.activated.connect(callback)
            self._shortcuts.append(shortcut)

    def _toggle_playback(self) -> None:
        self.controls.set_running(self.runtime.toggle_playback())
        self._refresh_status()

    def _advance_frame(self) -> None:
        if self.runtime.advance_frame():
            self._refresh_canvas()
            self._record_render_frame()

    def _step(self) -> None:
        self.runtime.step()
        self._refresh_canvas()

    def _reset(self) -> None:
        self.runtime.reset()
        self.controls.set_running(False)
        self._refresh_canvas()

    def _apply_settings(self, settings: LabSettings) -> None:
        update = self.runtime.apply_a_settings(settings)
        self.explanation.update_stability(update.report)
        self.controls.set_running(False)
        self.controls.set_playback_available(update.report.is_stable)
        if update.compare_cleared:
            self.compare.clear("A changed. Duplicate A into B again to start a new comparison.")
        if update.simulation_rebuilt:
            self._refresh_canvas()
        elif update.report.is_stable:
            self._refresh_status()
        else:
            self._refresh_status(update.report.messages[0])

    def _refresh_canvas(self) -> None:
        initial = self.simulation.initial_condition
        self.canvas.set_wave_data(
            self.runtime.render_state.positions_a,
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
            self.runtime.clear_compare()
            self.canvas.set_comparison_data(None)
            self.controls.set_playback_available(self.simulation.stability.is_stable)
            self._refresh_canvas()
            self._refresh_status()

    def _duplicate_compare(self) -> None:
        self.compare.set_duplicate(self.controls.settings)

    def _apply_compare_settings(self, settings: LabSettings) -> None:
        update = self.runtime.apply_b_settings(settings)
        self.compare.update_stability(update.report)
        self.controls.set_running(False)
        self.controls.set_playback_available(update.report.is_stable)
        if not update.report.is_stable:
            self.canvas.set_comparison_data(None)
            self._refresh_status(update.report.messages[0])
            return
        self._refresh_canvas()

    def _disable_compare(self, message: str) -> None:
        if self.compare.settings is None and self.compare_simulation is None:
            return
        self.runtime.clear_compare()
        self.canvas.set_comparison_data(None)
        self.compare.clear(message)

    def _show_concept(self, concept: str, settings: LabSettings) -> None:
        self.runtime.set_selected_concept(concept)
        self.explanation.show_concept(concept, settings)

    def _set_advanced_mode(self, enabled: bool) -> None:
        self.runtime.set_advanced_mode(enabled)
        self.diagnostics.set_advanced_visible(enabled)

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

    @property
    def simulation(self) -> WaveSimulation:
        """Compatibility alias for the primary solver used by existing views."""

        return self.runtime.simulation_a

    @property
    def compare_simulation(self) -> WaveSimulation | None:
        """Compatibility alias for the optional synchronized B solver."""

        return self.runtime.simulation_b


def main() -> int:
    app = QApplication(sys.argv)
    apply_design_system(app)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
