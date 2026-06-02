"""User-controlled experiment settings independent from desktop widgets."""

from __future__ import annotations

from dataclasses import dataclass

from .simulation import BoundaryCondition, InitialCondition, SimulationParameters


@dataclass(frozen=True)
class LabSettings:
    """Physical, numerical, and playback values selected by the user."""

    wave_shape: str = "gaussian"
    amplitude: float = 0.8
    wavelength: float = 20.0
    pulse_width: float = 6.0
    wave_speed: float = 3.0
    damping_rate: float = 0.16
    playback_speed: float = 1.0
    domain_length: float = 100.0
    grid_points: int = 401
    time_step: float = 0.01
    boundary: BoundaryCondition = BoundaryCondition.FIXED

    def simulation_parameters(self) -> SimulationParameters:
        return SimulationParameters(
            domain_length=self.domain_length,
            grid_points=self.grid_points,
            wave_speed=self.wave_speed,
            damping_rate=self.damping_rate,
            time_step=self.time_step,
            boundary=self.boundary,
        )

    def initial_condition(self) -> InitialCondition:
        return InitialCondition(
            kind=self.wave_shape,
            amplitude=self.amplitude,
            wavelength=self.wavelength,
            width=self.pulse_width,
        )
