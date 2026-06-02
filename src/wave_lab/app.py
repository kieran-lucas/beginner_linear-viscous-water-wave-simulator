"""Minimal desktop shell for exploring the real-time wave canvas."""

from __future__ import annotations

import sys

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .simulation import InitialCondition, SimulationParameters, WaveSimulation
from .visualization import WaveCanvas


class MainWindow(QMainWindow):
    """Desktop preview focused on profile visualization and playback."""

    RENDER_INTERVAL_MS = 33
    SOLVER_STEPS_PER_FRAME = 3

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Viscous Wave Lab")
        self.resize(1120, 720)

        self.simulation = WaveSimulation(
            SimulationParameters(damping_rate=0.24),
            InitialCondition(kind="gaussian", amplitude=1.0, width=8.0),
        )
        self.canvas = WaveCanvas()
        self.canvas.set_snapshot(self.simulation.state.displacement)

        self.play_button = QPushButton("Play")
        self.step_button = QPushButton("Step")
        self.reset_button = QPushButton("Reset")
        self.snapshot_button = QPushButton("Update snapshot")
        self.state_label = QLabel()
        self.state_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.play_button.clicked.connect(self._toggle_playback)
        self.step_button.clicked.connect(self._step)
        self.reset_button.clicked.connect(self._reset)
        self.snapshot_button.clicked.connect(self._update_snapshot)

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
        layout.addWidget(self.canvas, stretch=1)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(separator)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        toolbar.addWidget(self.reset_button)
        toolbar.addWidget(self.play_button)
        toolbar.addWidget(self.step_button)
        toolbar.addSpacing(12)
        toolbar.addWidget(self.snapshot_button)
        toolbar.addStretch(1)
        toolbar.addWidget(self.state_label)
        layout.addLayout(toolbar)
        self.setCentralWidget(central)

        self.setStyleSheet(
            """
            QMainWindow, QWidget { background: #F7F8FA; color: #172033; }
            QLabel#heading { font-size: 20px; font-weight: 650; }
            QLabel#subtitle { color: #5B667A; font-size: 13px; }
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
            self.play_button.setText("Pause")
        else:
            self.simulation.pause()
            self.play_button.setText("Play")
        self._refresh_status()

    def _advance_frame(self) -> None:
        self.simulation.run(self.SOLVER_STEPS_PER_FRAME)
        if not self.simulation.state.paused:
            self._refresh_canvas()

    def _step(self) -> None:
        self.simulation.step()
        self._refresh_canvas()

    def _reset(self) -> None:
        self.simulation.reset()
        self.simulation.pause()
        self.play_button.setText("Play")
        self._refresh_canvas()

    def _update_snapshot(self) -> None:
        self.canvas.set_snapshot(self.simulation.state.displacement)

    def _refresh_canvas(self) -> None:
        initial = self.simulation.initial_condition
        self.canvas.set_wave_data(
            self.simulation.parameters.positions,
            self.simulation.state.displacement,
            self.simulation.state.diagnostics,
            initial_amplitude=initial.amplitude,
            wavelength=initial.wavelength if initial.kind == "sinusoidal" else None,
        )
        self._refresh_status()

    def _refresh_status(self) -> None:
        state = "Paused" if self.simulation.state.paused else "Running"
        self.state_label.setText(
            f"{state}   damping rate = {self.simulation.parameters.damping_rate:.2f} 1/s   "
            f"CFL = {self.simulation.stability.cfl_number:.2f}"
        )


def main() -> int:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
