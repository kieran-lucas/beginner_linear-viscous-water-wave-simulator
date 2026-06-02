"""Readable one-dimensional solver for the damped wave equation.

The educational model is:

    u_tt + gamma * u_t = c^2 * u_xx

This is a reduced model. ``gamma`` is an effective damping rate, not a direct
fluid-viscosity input. The solver uses centered spatial differences and RK4
time integration. It is intentionally small enough to explain in a classroom
or README and independent from any rendering framework.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from math import exp, isfinite, pi, sin


class BoundaryCondition(str, Enum):
    """Supported behavior at the left and right edges of the domain."""

    FIXED = "fixed"
    REFLECTIVE = "reflective"
    PERIODIC = "periodic"


@dataclass(frozen=True)
class SimulationParameters:
    """Physical and numerical settings, using seconds and meter-like units."""

    domain_length: float = 100.0
    grid_points: int = 401
    wave_speed: float = 4.0
    damping_rate: float = 0.08
    time_step: float = 0.01
    boundary: BoundaryCondition = BoundaryCondition.FIXED

    def __post_init__(self) -> None:
        if not isinstance(self.boundary, BoundaryCondition):
            try:
                object.__setattr__(self, "boundary", BoundaryCondition(self.boundary))
            except ValueError as error:
                raise ValueError(f"Unsupported boundary condition: {self.boundary!r}") from error

        numeric_values = {
            "domain_length": self.domain_length,
            "wave_speed": self.wave_speed,
            "damping_rate": self.damping_rate,
            "time_step": self.time_step,
        }
        for name, value in numeric_values.items():
            if not isfinite(value):
                raise ValueError(f"{name} must be finite")

        if self.domain_length <= 0:
            raise ValueError("domain_length must be greater than zero")
        if self.grid_points < 3:
            raise ValueError("grid_points must be at least 3")
        if self.wave_speed <= 0:
            raise ValueError("wave_speed must be greater than zero")
        if self.damping_rate < 0:
            raise ValueError("damping_rate must be zero or greater")
        if self.time_step <= 0:
            raise ValueError("time_step must be greater than zero")

    @property
    def grid_spacing(self) -> float:
        """Distance between samples.

        A periodic grid excludes the duplicated right endpoint so its stencil
        wraps evenly. Fixed and reflective grids include both endpoints.
        """

        intervals = (
            self.grid_points
            if self.boundary is BoundaryCondition.PERIODIC
            else self.grid_points - 1
        )
        return self.domain_length / intervals

    @property
    def positions(self) -> list[float]:
        dx = self.grid_spacing
        return [index * dx for index in range(self.grid_points)]


@dataclass(frozen=True)
class InitialCondition:
    """Initial displacement profile and velocity shared by all presets."""

    kind: str = "gaussian"
    amplitude: float = 1.0
    width: float = 8.0
    wavelength: float = 20.0
    center: float | None = None
    initial_velocity: float = 0.0

    def __post_init__(self) -> None:
        if self.kind not in {"gaussian", "sinusoidal"}:
            raise ValueError("kind must be 'gaussian' or 'sinusoidal'")
        for name in ("amplitude", "width", "wavelength", "initial_velocity"):
            if not isfinite(getattr(self, name)):
                raise ValueError(f"{name} must be finite")
        if self.center is not None and not isfinite(self.center):
            raise ValueError("center must be finite when provided")
        if self.kind == "gaussian" and self.width <= 0:
            raise ValueError("width must be greater than zero for a Gaussian pulse")
        if self.kind == "sinusoidal" and self.wavelength <= 0:
            raise ValueError("wavelength must be greater than zero for a sinusoidal wave")


@dataclass(frozen=True)
class DiagnosticSample:
    """Values suitable for a timeline or status display."""

    time: float
    maximum_amplitude: float
    energy: float
    normalized_energy: float


@dataclass
class SimulationState:
    """Current displacement, velocity, clock, and latest diagnostics."""

    displacement: list[float]
    velocity: list[float]
    time: float = 0.0
    paused: bool = True
    diagnostics: DiagnosticSample | None = None
    history: list[DiagnosticSample] = field(default_factory=list)


@dataclass(frozen=True)
class StabilityReport:
    """Result of checking whether explicit integration settings are sensible."""

    is_stable: bool
    cfl_number: float
    damping_number: float
    messages: tuple[str, ...]


def check_stability(parameters: SimulationParameters) -> StabilityReport:
    """Check conservative guardrails for this educational explicit solver."""

    cfl_number = parameters.wave_speed * parameters.time_step / parameters.grid_spacing
    damping_number = parameters.damping_rate * parameters.time_step
    messages: list[str] = []
    is_stable = True

    # RK4 permits a somewhat larger CFL number for this problem. A limit of
    # 1.0 is deliberately conservative and easier for beginners to reason about.
    if cfl_number > 1.0:
        is_stable = False
        messages.append("CFL number exceeds 1.0; reduce the time step or increase grid spacing.")
    elif cfl_number > 0.8:
        messages.append("CFL number is close to the recommended limit of 0.8.")

    # Strong damping can also make an explicit update unstable even when the
    # wave-speed CFL number is acceptable.
    if damping_number > 2.0:
        is_stable = False
        messages.append("Damping rate multiplied by time step exceeds 2.0; reduce the time step.")
    elif damping_number > 0.5:
        messages.append("Damping update is large; use a smaller time step for better accuracy.")

    if not messages:
        messages.append("Time step is within the recommended stability limits.")

    return StabilityReport(is_stable, cfl_number, damping_number, tuple(messages))


class WaveSimulation:
    """Deterministic 1D damped-wave simulation with UI-friendly controls."""

    def __init__(
        self,
        parameters: SimulationParameters | None = None,
        initial_condition: InitialCondition | None = None,
    ) -> None:
        self.parameters = parameters or SimulationParameters()
        self.initial_condition = initial_condition or InitialCondition()
        self.stability = check_stability(self.parameters)
        if not self.stability.is_stable:
            raise ValueError("Unstable simulation parameters: " + " ".join(self.stability.messages))
        self.state = SimulationState([], [])
        self._initial_energy = 0.0
        self.reset()

    def reset(self, initial_condition: InitialCondition | None = None) -> SimulationState:
        """Return to t=0 using the selected deterministic initial profile."""

        if initial_condition is not None:
            self.initial_condition = initial_condition

        displacement = self._initial_displacement()
        velocity = [self.initial_condition.initial_velocity] * self.parameters.grid_points
        self._apply_fixed_boundary(displacement, velocity)
        self.state = SimulationState(displacement=displacement, velocity=velocity)
        self._initial_energy = self._energy(displacement, velocity)
        self._record_diagnostics()
        return self.state

    def pause(self) -> None:
        self.state.paused = True

    def resume(self) -> None:
        self.state.paused = False

    def run(self, steps: int = 1) -> SimulationState:
        """Advance during animation playback; do nothing while paused."""

        if not self.state.paused:
            self.step(steps)
        return self.state

    def step(self, steps: int = 1) -> SimulationState:
        """Advance a fixed number of updates, including while paused."""

        if not isinstance(steps, int) or isinstance(steps, bool) or steps < 1:
            raise ValueError("steps must be a positive integer")
        for _ in range(steps):
            self._rk4_step()
            self.state.time += self.parameters.time_step
            self._record_diagnostics()
        return self.state

    def _initial_displacement(self) -> list[float]:
        condition = self.initial_condition
        positions = self.parameters.positions
        if condition.kind == "sinusoidal":
            return [
                condition.amplitude * sin(2.0 * pi * position / condition.wavelength)
                for position in positions
            ]

        center = condition.center
        if center is None:
            center = self.parameters.domain_length / 2.0
        return [
            condition.amplitude * exp(-((position - center) ** 2) / (2.0 * condition.width**2))
            for position in positions
        ]

    def _rk4_step(self) -> None:
        dt = self.parameters.time_step
        displacement = self.state.displacement
        velocity = self.state.velocity

        k1_u, k1_v = self._derivatives(displacement, velocity)
        k2_u, k2_v = self._derivatives(
            self._offset(displacement, k1_u, dt / 2.0),
            self._offset(velocity, k1_v, dt / 2.0),
        )
        k3_u, k3_v = self._derivatives(
            self._offset(displacement, k2_u, dt / 2.0),
            self._offset(velocity, k2_v, dt / 2.0),
        )
        k4_u, k4_v = self._derivatives(
            self._offset(displacement, k3_u, dt),
            self._offset(velocity, k3_v, dt),
        )

        self.state.displacement = [
            value + dt * (a + 2.0 * b + 2.0 * c + d) / 6.0
            for value, a, b, c, d in zip(displacement, k1_u, k2_u, k3_u, k4_u)
        ]
        self.state.velocity = [
            value + dt * (a + 2.0 * b + 2.0 * c + d) / 6.0
            for value, a, b, c, d in zip(velocity, k1_v, k2_v, k3_v, k4_v)
        ]
        self._apply_fixed_boundary(self.state.displacement, self.state.velocity)

    def _derivatives(
        self, displacement: list[float], velocity: list[float]
    ) -> tuple[list[float], list[float]]:
        laplacian = self._laplacian(displacement)
        acceleration = [
            self.parameters.wave_speed**2 * curvature - self.parameters.damping_rate * speed
            for curvature, speed in zip(laplacian, velocity)
        ]
        displacement_rate = velocity.copy()
        self._apply_fixed_boundary(displacement_rate, acceleration)
        return displacement_rate, acceleration

    def _laplacian(self, values: list[float]) -> list[float]:
        count = len(values)
        inverse_dx_squared = 1.0 / self.parameters.grid_spacing**2
        curvature = [0.0] * count

        for index in range(1, count - 1):
            curvature[index] = (
                values[index - 1] - 2.0 * values[index] + values[index + 1]
            ) * inverse_dx_squared

        if self.parameters.boundary is BoundaryCondition.PERIODIC:
            curvature[0] = (values[-1] - 2.0 * values[0] + values[1]) * inverse_dx_squared
            curvature[-1] = (values[-2] - 2.0 * values[-1] + values[0]) * inverse_dx_squared
        elif self.parameters.boundary is BoundaryCondition.REFLECTIVE:
            curvature[0] = 2.0 * (values[1] - values[0]) * inverse_dx_squared
            curvature[-1] = 2.0 * (values[-2] - values[-1]) * inverse_dx_squared

        return curvature

    def _energy(self, displacement: list[float], velocity: list[float]) -> float:
        dx = self.parameters.grid_spacing
        kinetic = sum(speed**2 for speed in velocity)
        if self.parameters.boundary is BoundaryCondition.PERIODIC:
            differences = [
                displacement[(index + 1) % len(displacement)] - value
                for index, value in enumerate(displacement)
            ]
        else:
            differences = [
                right - left for left, right in zip(displacement[:-1], displacement[1:])
            ]
        potential = self.parameters.wave_speed**2 * sum(
            (difference / dx) ** 2 for difference in differences
        )
        return 0.5 * dx * (kinetic + potential)

    def _record_diagnostics(self) -> None:
        energy = self._energy(self.state.displacement, self.state.velocity)
        normalized_energy = energy / self._initial_energy if self._initial_energy else 0.0
        sample = DiagnosticSample(
            time=self.state.time,
            maximum_amplitude=max(abs(value) for value in self.state.displacement),
            energy=energy,
            normalized_energy=normalized_energy,
        )
        self.state.diagnostics = sample
        self.state.history.append(sample)

    def _apply_fixed_boundary(self, displacement: list[float], velocity: list[float]) -> None:
        if self.parameters.boundary is BoundaryCondition.FIXED:
            displacement[0] = displacement[-1] = 0.0
            velocity[0] = velocity[-1] = 0.0

    @staticmethod
    def _offset(values: list[float], derivative: list[float], scale: float) -> list[float]:
        return [value + scale * change for value, change in zip(values, derivative)]
