import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from wave_lab.app import MainWindow
from wave_lab.control_panel import PRESETS, ControlPanel
from wave_lab.simulation import check_stability


class ControlPanelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_beginner_presets_are_stable_except_labeled_demo(self) -> None:
        for preset in PRESETS:
            with self.subTest(preset=preset.name):
                report = check_stability(preset.settings.simulation_parameters())
                self.assertEqual(report.is_stable, not preset.stability_demo)

    def test_default_preset_has_visible_but_gentle_damping(self) -> None:
        default = PRESETS[0]

        self.assertEqual(default.name, "Gentle ripple")
        self.assertGreaterEqual(default.settings.damping_rate, 0.1)
        self.assertLessEqual(default.settings.damping_rate, 0.3)

    def test_advanced_controls_use_progressive_disclosure(self) -> None:
        panel = ControlPanel()

        self.assertTrue(panel.advanced_frame.isHidden())
        panel.advanced_toggle.setChecked(True)

        self.assertFalse(panel.advanced_frame.isHidden())

    def test_gaussian_shape_replaces_wavelength_with_pulse_width(self) -> None:
        panel = ControlPanel()

        panel.shape_combo.setCurrentIndex(panel.shape_combo.findData("gaussian"))

        self.assertTrue(panel.wavelength_field.isHidden())
        self.assertFalse(panel.pulse_width_field.isHidden())

    def test_playback_speed_does_not_reset_running_experiment(self) -> None:
        window = MainWindow()
        window._step()
        elapsed = window.simulation.state.time

        window.controls.playback_combo.setCurrentIndex(
            window.controls.playback_combo.findData(2.0)
        )

        self.assertEqual(window.simulation.state.time, elapsed)
        window.close()

    def test_stability_demo_blocks_playback(self) -> None:
        window = MainWindow()
        preset = next(preset for preset in PRESETS if preset.stability_demo)

        window.controls.load_preset(preset)

        self.assertFalse(window.controls.play_button.isEnabled())
        self.assertFalse(window.controls.step_button.isEnabled())
        self.assertIn("Playback blocked", window.state_label.text())
        window.close()


if __name__ == "__main__":
    unittest.main()
