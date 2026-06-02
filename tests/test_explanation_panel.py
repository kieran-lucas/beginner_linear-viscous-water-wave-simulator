import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from wave_lab.app import MainWindow, startup_error_message
from wave_lab.control_panel import PRESETS, LabSettings
from wave_lab.education import CONCEPTS, format_change, interpretation, stability_message
from wave_lab.explanation_panel import ExplanationPanel
from wave_lab.simulation import DiagnosticSample, SimulationParameters, check_stability


class EducationCopyTests(unittest.TestCase):
    def test_required_concepts_have_structured_copy(self) -> None:
        required = {
            "amplitude",
            "wavelength",
            "wave_speed",
            "damping_rate",
            "time_step",
            "boundary",
        }

        self.assertTrue(required.issubset(CONCEPTS))
        for concept in required:
            with self.subTest(concept=concept):
                copy = CONCEPTS[concept]
                self.assertTrue(copy.title)
                self.assertTrue(copy.plain_english)
                self.assertTrue(copy.equation_note)

    def test_change_message_includes_value_and_units(self) -> None:
        message = format_change("damping_rate", LabSettings(damping_rate=0.42))

        self.assertEqual(message, "Damping rate changed to 0.420 1/s.")

    def test_damping_interpretation_reports_energy_loss(self) -> None:
        diagnostic = DiagnosticSample(2.0, 0.4, 1.0, 0.35)

        message = interpretation(diagnostic, damping_rate=0.2)

        self.assertIn("35%", message)
        self.assertIn("Damping is removing energy", message)

    def test_unstable_message_is_actionable(self) -> None:
        report = check_stability(
            SimulationParameters(wave_speed=8.0, time_step=0.08)
        )

        level, message = stability_message(report)

        self.assertEqual(level, "error")
        self.assertIn("Playback is blocked", message)
        self.assertIn("reduce the time step", message)

    def test_startup_error_message_contains_retry_commands(self) -> None:
        message = startup_error_message(RuntimeError("Qt plugin missing"))

        self.assertIn("Qt plugin missing", message)
        self.assertIn('python -m pip install -e "."', message)
        self.assertIn("python -m wave_lab", message)


class ExplanationPanelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_panel_shows_compact_equation_and_selected_concept(self) -> None:
        panel = ExplanationPanel()

        panel.show_concept("wavelength", LabSettings(wavelength=24.0))

        self.assertEqual(panel.concept_title.text(), "Wavelength")
        self.assertIn("24.0 m", panel.changed_label.text())

    def test_window_updates_explanation_when_damping_changes(self) -> None:
        window = MainWindow()

        window.controls.damping_spin.setValue(0.42)

        self.assertEqual(window.explanation.concept_title.text(), "Damping rate")
        self.assertIn("0.420 1/s", window.explanation.changed_label.text())
        self.assertIn("simplified viscous loss", window.explanation.explanation_label.text())
        window.close()

    def test_window_shows_inline_first_launch_guidance(self) -> None:
        window = MainWindow()
        hint = window.onboarding_hint.text()

        self.assertIn("press Play", hint)
        self.assertIn("Damping rate", hint)
        self.assertIn("Reset", hint)
        self.assertIn("right panel", hint)
        window.close()

    def test_window_reports_stability_demo_in_explanation(self) -> None:
        window = MainWindow()
        preset = next(preset for preset in PRESETS if preset.stability_demo)

        window.controls.load_preset(preset)

        self.assertIn("Preset loaded: Stability risk demo", window.explanation.changed_label.text())
        self.assertIn("Playback is blocked", window.explanation.warning_label.text())
        window.close()


if __name__ == "__main__":
    unittest.main()
