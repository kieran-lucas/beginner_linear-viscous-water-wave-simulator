import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from wave_lab.app import MainWindow
from wave_lab.compare_panel import ComparePanel
from wave_lab.control_panel import LabSettings
from wave_lab.visualization import WaveCanvas


class ComparePanelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_duplicate_starts_with_exact_a_settings(self) -> None:
        panel = ComparePanel()
        settings = LabSettings(amplitude=0.8, wavelength=24.0, damping_rate=0.2)

        panel.set_duplicate(settings)

        self.assertEqual(panel.settings, settings)
        self.assertTrue(panel.enabled_toggle.isChecked())

    def test_b_editor_changes_only_selected_parameter(self) -> None:
        panel = ComparePanel()
        settings = LabSettings(amplitude=0.8, wavelength=24.0, damping_rate=0.2)
        panel.set_duplicate(settings)
        panel.parameter_combo.setCurrentIndex(panel.parameter_combo.findData("damping_rate"))

        panel.value_spin.setValue(0.6)

        self.assertEqual(panel.settings.damping_rate, 0.6)
        self.assertEqual(panel.settings.amplitude, settings.amplitude)
        self.assertEqual(panel.settings.wavelength, settings.wavelength)
        self.assertEqual(panel.settings.wave_speed, settings.wave_speed)

    def test_gaussian_compare_edits_pulse_width_instead_of_wavelength(self) -> None:
        panel = ComparePanel()

        panel.set_duplicate(LabSettings(wave_shape="gaussian"))

        self.assertGreaterEqual(panel.parameter_combo.findData("pulse_width"), 0)
        self.assertEqual(panel.parameter_combo.findData("wavelength"), -1)


class CompareModeIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_duplicate_creates_b_with_matching_initial_condition(self) -> None:
        window = MainWindow()

        window._duplicate_compare()

        self.assertIsNotNone(window.compare_simulation)
        self.assertEqual(
            window.compare_simulation.initial_condition,
            window.simulation.initial_condition,
        )
        self.assertEqual(window.compare_simulation.parameters, window.simulation.parameters)
        window.close()

    def test_b_change_resets_and_steps_both_simulations_together(self) -> None:
        window = MainWindow()
        window._step()
        window._duplicate_compare()
        window.compare.parameter_combo.setCurrentIndex(
            window.compare.parameter_combo.findData("damping_rate")
        )

        window.compare.value_spin.setValue(0.7)

        self.assertEqual(window.simulation.state.time, 0.0)
        self.assertEqual(window.compare_simulation.state.time, 0.0)
        self.assertNotEqual(
            window.simulation.parameters.damping_rate,
            window.compare_simulation.parameters.damping_rate,
        )
        window._step()
        self.assertEqual(window.simulation.state.time, window.compare_simulation.state.time)
        window.close()

    def test_changing_a_turns_compare_mode_off(self) -> None:
        window = MainWindow()
        window._duplicate_compare()

        window.controls.wave_speed_spin.setValue(4.5)

        self.assertIsNone(window.compare_simulation)
        self.assertFalse(window.compare.enabled_toggle.isChecked())
        self.assertIn("A changed", window.compare.description_label.text())
        window.close()

    def test_overlay_scale_expands_for_taller_b_wave(self) -> None:
        canvas = WaveCanvas()
        canvas.set_wave_data([0.0, 1.0], [0.0, 1.0], initial_amplitude=1.0)

        canvas.set_comparison_data([0.0, 2.0], initial_amplitude=2.0)

        self.assertAlmostEqual(canvas._vertical_extent, 2.4)


if __name__ == "__main__":
    unittest.main()
