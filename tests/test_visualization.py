import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QRectF
from PySide6.QtWidgets import QApplication

from wave_lab.app import MainWindow
from wave_lab.visualization import PlotTransform, WaveCanvas


class PlotTransformTests(unittest.TestCase):
    def test_maps_equilibrium_to_vertical_center(self) -> None:
        transform = PlotTransform(QRectF(10.0, 20.0, 200.0, 100.0), 0.0, 10.0, 2.0)

        point = transform.to_canvas(5.0, 0.0)

        self.assertAlmostEqual(point.x(), 110.0)
        self.assertAlmostEqual(point.y(), 70.0)
        self.assertAlmostEqual(transform.x_from_canvas(point.x()), 5.0)


class WaveCanvasTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_canvas_renders_supplied_profile_to_image(self) -> None:
        canvas = WaveCanvas()
        canvas.set_wave_data([0.0, 1.0, 2.0], [0.0, 1.0, 0.0], initial_amplitude=1.0)

        image = canvas.render_to_image(640, 360)

        self.assertFalse(image.isNull())
        self.assertEqual(image.width(), 640)
        self.assertEqual(image.height(), 360)

    def test_snapshot_must_match_current_grid(self) -> None:
        canvas = WaveCanvas()
        canvas.set_wave_data([0.0, 1.0, 2.0], [0.0, 1.0, 0.0])

        with self.assertRaisesRegex(ValueError, "snapshot"):
            canvas.set_snapshot([0.0, 1.0])

    def test_window_controls_advance_and_reset_simulation(self) -> None:
        window = MainWindow()

        window._step()
        self.assertGreater(window.simulation.state.time, 0.0)

        window._reset()
        self.assertEqual(window.simulation.state.time, 0.0)
        self.assertTrue(window.simulation.state.paused)
        window.close()


if __name__ == "__main__":
    unittest.main()

