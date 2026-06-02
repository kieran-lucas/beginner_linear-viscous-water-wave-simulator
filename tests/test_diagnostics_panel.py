import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from wave_lab.app import MainWindow
from wave_lab.diagnostics_panel import DiagnosticsPanel, TrendCanvas
from wave_lab.simulation import (
    MAX_DIAGNOSTIC_HISTORY,
    DiagnosticSample,
    SimulationParameters,
    WaveSimulation,
    check_stability,
)


class DiagnosticHistoryTests(unittest.TestCase):
    def test_solver_history_is_bounded(self) -> None:
        simulation = WaveSimulation()

        simulation.step(MAX_DIAGNOSTIC_HISTORY + 25)

        self.assertEqual(len(simulation.state.history), MAX_DIAGNOSTIC_HISTORY)
        self.assertEqual(simulation.state.history[-1], simulation.state.diagnostics)
        self.assertGreater(simulation.state.history[0].time, 0.0)

    def test_graph_downsamples_long_history_for_painting(self) -> None:
        history = [
            DiagnosticSample(float(index), 1.0, 1.0, 1.0)
            for index in range(1000)
        ]

        selected = TrendCanvas._downsample(history, 100)

        self.assertLessEqual(len(selected), 101)
        self.assertEqual(selected[-1], history[-1])


class DiagnosticsPanelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_panel_can_collapse_and_restore_graphs(self) -> None:
        panel = DiagnosticsPanel()

        panel._toggle_graphs()
        self.assertTrue(panel.graph_frame.isHidden())
        self.assertEqual(panel.toggle_button.text(), "Show diagnostics")

        panel._toggle_graphs()
        self.assertFalse(panel.graph_frame.isHidden())

    def test_panel_summary_uses_current_real_sample(self) -> None:
        simulation = WaveSimulation()
        simulation.step(10)
        panel = DiagnosticsPanel()

        panel.update_data(simulation.state.history, simulation.stability)

        self.assertIn("Time 0.10 s", panel.summary_label.text())
        self.assertIn("A: max height", panel.summary_label.text())
        self.assertIn("Stable setup", panel.stability_label.text())

    def test_panel_shows_a_and_b_diagnostics(self) -> None:
        first = WaveSimulation()
        second = WaveSimulation()
        first.step()
        second.step()
        panel = DiagnosticsPanel()

        panel.update_data(first.state.history, first.stability, second.state.history)

        self.assertIn("B: max height", panel.summary_label.text())

    def test_advanced_mode_controls_performance_visibility(self) -> None:
        panel = DiagnosticsPanel()

        panel.set_advanced_visible(True)
        panel.set_render_rate(29.5)

        self.assertFalse(panel.performance_label.isHidden())
        self.assertIn("29.5", panel.performance_label.text())

    def test_window_diagnostics_follow_step_and_compare(self) -> None:
        window = MainWindow()
        window._step()
        self.assertIn("Time 0.01 s", window.diagnostics.summary_label.text())

        window._duplicate_compare()
        window._step()

        self.assertIn("B: max height", window.diagnostics.summary_label.text())
        self.assertEqual(
            window.simulation.state.time,
            window.compare_simulation.state.time,
        )
        window.close()

    def test_unstable_report_is_specific(self) -> None:
        report = check_stability(
            SimulationParameters(
                wave_speed=8.0,
                time_step=0.08,
            )
        )
        panel = DiagnosticsPanel()

        panel.update_data([], report)

        self.assertFalse(report.is_stable)
        self.assertIn("Playback is blocked", panel.stability_label.text())
        self.assertIn("reduce the time step", panel.stability_label.text())


if __name__ == "__main__":
    unittest.main()
