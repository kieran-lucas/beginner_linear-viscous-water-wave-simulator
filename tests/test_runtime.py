import unittest

from wave_lab.control_panel import LabSettings
from wave_lab.runtime import AppConfig, RuntimeController


class RuntimeControllerTests(unittest.TestCase):
    def test_static_config_and_ui_state_are_explicit(self) -> None:
        runtime = RuntimeController(config=AppConfig(render_interval_ms=40))

        runtime.set_selected_concept("damping_rate")
        runtime.set_advanced_mode(True)
        runtime.set_diagnostics_expanded(False)

        self.assertEqual(runtime.config.render_interval_ms, 40)
        self.assertEqual(runtime.ui_state.selected_concept, "damping_rate")
        self.assertTrue(runtime.ui_state.advanced_mode)
        self.assertFalse(runtime.ui_state.diagnostics_expanded)

    def test_playback_speed_changes_step_count_without_rebuilding_solver(self) -> None:
        runtime = RuntimeController()
        original_simulation = runtime.simulation_a

        update = runtime.apply_a_settings(
            LabSettings(playback_speed=2.0)
        )

        self.assertFalse(update.simulation_rebuilt)
        self.assertIs(runtime.simulation_a, original_simulation)
        self.assertEqual(runtime.steps_per_frame, 6)

    def test_render_positions_are_cached_between_frames(self) -> None:
        runtime = RuntimeController()
        positions = runtime.render_state.positions_a

        runtime.duplicate_a_into_b()
        runtime.toggle_playback()
        runtime.advance_frame()

        self.assertIs(runtime.render_state.positions_a, positions)
        self.assertIs(runtime.render_state.positions_b, positions)

    def test_physical_change_rebuilds_a_and_clears_compare(self) -> None:
        runtime = RuntimeController()
        runtime.duplicate_a_into_b()
        original_simulation = runtime.simulation_a

        update = runtime.apply_a_settings(LabSettings(wave_speed=4.5))

        self.assertTrue(update.simulation_rebuilt)
        self.assertTrue(update.compare_cleared)
        self.assertIsNot(runtime.simulation_a, original_simulation)
        self.assertIsNone(runtime.simulation_b)
        self.assertFalse(runtime.ui_state.compare_mode)

    def test_compare_mode_steps_both_solvers_together(self) -> None:
        runtime = RuntimeController()
        runtime.apply_b_settings(LabSettings(damping_rate=0.8))

        runtime.step()

        self.assertEqual(runtime.simulation_a.state.time, runtime.simulation_b.state.time)

    def test_compare_solvers_keep_independent_state_arrays(self) -> None:
        runtime = RuntimeController()
        runtime.apply_b_settings(LabSettings(damping_rate=0.8))

        runtime.step()

        self.assertIsNot(
            runtime.simulation_a.state.displacement,
            runtime.simulation_b.state.displacement,
        )
        self.assertIsNot(runtime.simulation_a.state.velocity, runtime.simulation_b.state.velocity)
        self.assertNotEqual(
            runtime.simulation_a.state.displacement,
            runtime.simulation_b.state.displacement,
        )

    def test_invalid_update_retains_last_valid_solver(self) -> None:
        runtime = RuntimeController()
        original_simulation = runtime.simulation_a

        update = runtime.apply_a_settings(
            LabSettings(wave_speed=8.0, time_step=0.08)
        )

        self.assertFalse(update.report.is_stable)
        self.assertFalse(update.simulation_rebuilt)
        self.assertIs(runtime.simulation_a, original_simulation)
        self.assertTrue(runtime.simulation_a.state.paused)


if __name__ == "__main__":
    unittest.main()
