import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from wave_lab.app import MainWindow
from wave_lab.design_system import COLORS, SPACING, STYLESHEET, apply_design_system


class DesignSystemTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_semantic_tokens_define_scientific_theme(self) -> None:
        self.assertEqual(COLORS.primary, "#1769AA")
        self.assertEqual(COLORS.comparison, "#C77C18")
        self.assertEqual(SPACING.medium, 12)

    def test_stylesheet_has_focus_tooltip_and_button_roles(self) -> None:
        self.assertIn('QPushButton[role="primary"]', STYLESHEET)
        self.assertIn("QPushButton:focus", STYLESHEET)
        self.assertIn("QToolTip", STYLESHEET)
        self.assertNotIn("gradient", STYLESHEET.lower())

    def test_application_theme_is_applied(self) -> None:
        apply_design_system(self.app)

        self.assertIn(COLORS.app_background, self.app.styleSheet())

    def test_shell_assigns_roles_tooltips_and_shortcuts(self) -> None:
        window = MainWindow()
        shortcut_names = {shortcut.key().toString() for shortcut in window._shortcuts}

        self.assertEqual(window.controls.play_button.property("role"), "primary")
        self.assertEqual(window.diagnostics.toggle_button.property("role"), "ghost")
        self.assertTrue(window.controls.damping_spin.toolTip())
        self.assertTrue(window.canvas.toolTip())
        self.assertTrue({"Space", "Right", "Ctrl+R", "Ctrl+D", "Ctrl+G"} <= shortcut_names)
        window.close()


if __name__ == "__main__":
    unittest.main()

