import math
import unittest

from wave_lab import (
    BoundaryCondition,
    InitialCondition,
    SimulationParameters,
    WaveSimulation,
    check_stability,
)


class WaveSimulationTests(unittest.TestCase):
    def test_default_gaussian_pulse_is_deterministic(self) -> None:
        first = WaveSimulation()
        second = WaveSimulation()

        first.step(25)
        second.step(25)

        self.assertEqual(first.state.displacement, second.state.displacement)
        self.assertEqual(first.state.velocity, second.state.velocity)
        self.assertAlmostEqual(first.state.time, 0.25)

    def test_damping_reduces_energy(self) -> None:
        simulation = WaveSimulation(
            SimulationParameters(
                domain_length=20.0,
                grid_points=101,
                wave_speed=2.0,
                damping_rate=0.6,
                time_step=0.01,
                boundary=BoundaryCondition.PERIODIC,
            ),
            InitialCondition(kind="sinusoidal", wavelength=10.0),
        )

        simulation.step(400)

        self.assertLess(simulation.state.diagnostics.normalized_energy, 0.2)

    def test_zero_damping_does_not_remove_energy_from_periodic_sine_mode(self) -> None:
        simulation = WaveSimulation(
            SimulationParameters(
                domain_length=20.0,
                grid_points=100,
                wave_speed=2.0,
                damping_rate=0.0,
                time_step=0.005,
                boundary=BoundaryCondition.PERIODIC,
            ),
            InitialCondition(kind="sinusoidal", wavelength=10.0),
        )

        simulation.step(800)

        self.assertAlmostEqual(simulation.state.diagnostics.normalized_energy, 1.0, places=8)

    def test_periodic_sine_mode_tracks_analytic_damped_amplitude(self) -> None:
        parameters = SimulationParameters(
            domain_length=20.0,
            grid_points=100,
            wave_speed=2.0,
            damping_rate=0.2,
            time_step=0.005,
            boundary=BoundaryCondition.PERIODIC,
        )
        condition = InitialCondition(kind="sinusoidal", amplitude=1.0, wavelength=10.0)
        simulation = WaveSimulation(parameters, condition)

        simulation.step(200)

        wave_number = 2.0 * math.pi / condition.wavelength
        numerical_wave_number = (
            2.0
            * math.sin(wave_number * parameters.grid_spacing / 2.0)
            / parameters.grid_spacing
        )
        angular_frequency = math.sqrt(
            parameters.wave_speed**2 * numerical_wave_number**2 - parameters.damping_rate**2 / 4.0
        )
        expected_factor = math.exp(-parameters.damping_rate * simulation.state.time / 2.0) * (
            math.cos(angular_frequency * simulation.state.time)
            + parameters.damping_rate
            * math.sin(angular_frequency * simulation.state.time)
            / (2.0 * angular_frequency)
        )
        expected = [
            expected_factor * math.sin(wave_number * position)
            for position in parameters.positions
        ]

        maximum_error = max(
            abs(actual - reference)
            for actual, reference in zip(simulation.state.displacement, expected)
        )
        self.assertLess(maximum_error, 1e-8)

    def test_fixed_boundary_keeps_endpoints_at_zero(self) -> None:
        simulation = WaveSimulation(
            SimulationParameters(boundary=BoundaryCondition.FIXED),
            InitialCondition(kind="gaussian", center=10.0),
        )

        simulation.step(50)

        self.assertEqual(simulation.state.displacement[0], 0.0)
        self.assertEqual(simulation.state.displacement[-1], 0.0)
        self.assertEqual(simulation.state.velocity[0], 0.0)
        self.assertEqual(simulation.state.velocity[-1], 0.0)

    def test_reflective_boundary_preserves_uniform_displacement(self) -> None:
        simulation = WaveSimulation(
            SimulationParameters(boundary=BoundaryCondition.REFLECTIVE),
            InitialCondition(kind="sinusoidal", amplitude=0.0, initial_velocity=0.0),
        )
        simulation.state.displacement = [2.0] * simulation.parameters.grid_points

        simulation.step(10)

        self.assertEqual(simulation.state.displacement, [2.0] * simulation.parameters.grid_points)

    def test_pause_blocks_run_but_manual_step_still_advances(self) -> None:
        simulation = WaveSimulation()

        simulation.run(5)
        self.assertEqual(simulation.state.time, 0.0)

        simulation.step()
        self.assertAlmostEqual(simulation.state.time, simulation.parameters.time_step)

        simulation.resume()
        simulation.run(4)
        self.assertAlmostEqual(simulation.state.time, 5 * simulation.parameters.time_step)

    def test_reset_restores_initial_state_and_history(self) -> None:
        simulation = WaveSimulation()
        initial_displacement = simulation.state.displacement.copy()
        initial_velocity = simulation.state.velocity.copy()

        simulation.step(25)
        simulation.reset()

        self.assertEqual(simulation.state.displacement, initial_displacement)
        self.assertEqual(simulation.state.velocity, initial_velocity)
        self.assertEqual(simulation.state.time, 0.0)
        self.assertEqual(len(simulation.state.history), 1)

    def test_near_limit_cfl_number_reports_caution_without_blocking(self) -> None:
        report = check_stability(
            SimulationParameters(
                domain_length=10.0,
                grid_points=101,
                wave_speed=4.0,
                time_step=0.022,
            )
        )

        self.assertTrue(report.is_stable)
        self.assertGreater(report.cfl_number, 0.8)
        self.assertIn("close to the recommended limit", report.messages[0])

    def test_unstable_cfl_number_is_rejected(self) -> None:
        parameters = SimulationParameters(
            domain_length=10.0,
            grid_points=101,
            wave_speed=4.0,
            time_step=0.03,
        )

        report = check_stability(parameters)

        self.assertFalse(report.is_stable)
        with self.assertRaisesRegex(ValueError, "Unstable simulation parameters"):
            WaveSimulation(parameters)

    def test_invalid_physical_parameter_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "damping_rate"):
            SimulationParameters(damping_rate=-0.1)

        with self.assertRaisesRegex(ValueError, "wave_speed"):
            SimulationParameters(wave_speed=0.0)

        with self.assertRaisesRegex(ValueError, "grid_points"):
            SimulationParameters(grid_points=2)


if __name__ == "__main__":
    unittest.main()
