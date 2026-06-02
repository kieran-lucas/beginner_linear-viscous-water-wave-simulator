"""Structured beginner-facing copy for the live explanation panel.

Keeping these records separate from widgets makes copy review straightforward
and leaves a clear path for replacing text with translation keys later.
"""

from __future__ import annotations

from dataclasses import dataclass

from .control_panel import LabSettings, Preset
from .simulation import BoundaryCondition, DiagnosticSample, StabilityReport


@dataclass(frozen=True)
class ConceptCopy:
    """Short educational blocks for one selectable concept."""

    title: str
    plain_english: str
    equation_note: str
    try_this: str


CONCEPTS = {
    "overview": ConceptCopy(
        "Linear damped waves",
        "The blue line is surface displacement from equilibrium. The starting pulse "
        "separates into moving waves while damping gradually removes energy.",
        "The equation balances motion, damping, and spatial curvature.",
        "Press Play to watch the pulse move, then compare Strong damping with Almost no damping.",
    ),
    "wave_shape": ConceptCopy(
        "Starting wave shape",
        "A repeating wave shows a regular sequence of peaks. A Gaussian pulse starts "
        "as one disturbance and spreads into traveling waves.",
        "The equation is unchanged; only the starting displacement changes.",
        "Switch shapes and watch how the initial pattern changes.",
    ),
    "amplitude": ConceptCopy(
        "Initial height",
        "Amplitude is the wave height measured from the equilibrium line. A larger "
        "initial height makes taller peaks and troughs.",
        "Amplitude changes the starting displacement u(x, 0), not the wave speed.",
        "Double the initial height and compare the vertical scale at t = 0.",
    ),
    "wavelength": ConceptCopy(
        "Wavelength",
        "Wavelength is the distance between repeating peaks. A longer wavelength "
        "places peaks farther apart across the same domain.",
        "Wavelength changes the spatial pattern u(x, 0).",
        "Compare 10 m and 30 m wavelengths while keeping wave speed fixed.",
    ),
    "pulse_width": ConceptCopy(
        "Pulse width",
        "Pulse width controls how much space the starting disturbance occupies. "
        "It applies to a Gaussian pulse instead of a repeating wavelength.",
        "Pulse width changes the starting displacement u(x, 0).",
        "Use a narrow pulse, then a wide pulse, and compare how they spread.",
    ),
    "wave_speed": ConceptCopy(
        "Wave speed",
        "Wave speed controls how quickly the disturbance travels. It does not set "
        "the initial height or directly remove energy.",
        "The c^2 u_xx term controls propagation.",
        "Compare Gentle ripple with Fast propagation.",
    ),
    "damping_rate": ConceptCopy(
        "Damping rate",
        "Damping represents simplified viscous loss. It removes energy from the "
        "wave, so peaks and troughs become smaller over time.",
        "The gamma u_t term opposes motion. Larger gamma means faster decay.",
        "Duplicate A into B, increase B damping, and compare the two decay rates.",
    ),
    "playback_speed": ConceptCopy(
        "Simulation speed",
        "Simulation speed changes how quickly the animation advances on screen. "
        "It does not change the modeled water or the numerical time step.",
        "Playback speed is a viewing control, so it does not appear in the equation.",
        "Try 0.5x and 2x playback while keeping the experiment unchanged.",
    ),
    "grid_points": ConceptCopy(
        "Grid points",
        "The solver stores displacement at a finite set of positions. More grid "
        "points can resolve smaller details but require more computation.",
        "The continuous u_xx term is approximated on this spatial grid.",
        "Increase grid points and notice how the CFL stability value changes.",
    ),
    "time_step": ConceptCopy(
        "Time step",
        "The time step is the simulated time covered by one numerical update. Large "
        "steps are faster to compute but can make an explicit solver unreliable.",
        "The equation is continuous; the app approximates it through small updates.",
        "Open the Stability risk demo, then reduce the time step until playback unlocks.",
    ),
    "boundary": ConceptCopy(
        "Boundary behavior",
        "Boundary behavior determines what happens when a wave reaches an edge. "
        "Fixed ends stay at equilibrium, reflective edges bounce waves back, and "
        "periodic edges wrap one side of the domain to the other. A repeating wave "
        "that does not meet a fixed end may adjust sharply near that edge.",
        "Boundary conditions complete the equation by defining the domain edges.",
        "Try the same pulse with fixed ends and reflective edges.",
    ),
}


def format_change(concept: str, settings: LabSettings) -> str:
    """Describe the most recent user adjustment with units."""

    values = {
        "wave_shape": (
            "Starting wave shape changed to "
            + ("repeating wave." if settings.wave_shape == "sinusoidal" else "Gaussian pulse.")
        ),
        "amplitude": f"Initial height changed to {settings.amplitude:.1f} m.",
        "wavelength": f"Wavelength changed to {settings.wavelength:.1f} m.",
        "pulse_width": f"Pulse width changed to {settings.pulse_width:.1f} m.",
        "wave_speed": f"Wave speed changed to {settings.wave_speed:.1f} m/s.",
        "damping_rate": f"Damping rate changed to {settings.damping_rate:.3f} 1/s.",
        "playback_speed": f"Simulation speed changed to {settings.playback_speed:g}x.",
        "grid_points": f"Grid resolution changed to {settings.grid_points} points.",
        "time_step": f"Time step changed to {settings.time_step:.3f} s.",
        "boundary": f"Boundary behavior changed to {boundary_name(settings.boundary)}.",
    }
    return values.get(concept, "Experiment settings changed.")


def preset_message(preset: Preset) -> str:
    return f"Preset loaded: {preset.name}. {preset.description}"


def interpretation(diagnostic: DiagnosticSample | None, damping_rate: float) -> str:
    """Summarize the current run without overstating the reduced model."""

    if diagnostic is None:
        return "The simulation is ready. Press Play to watch the wave evolve."
    if diagnostic.time == 0.0:
        return (
            f"The experiment starts with a maximum displacement of "
            f"{diagnostic.maximum_amplitude:.2f} m. Press Play to observe propagation "
            "and decay."
        )
    if damping_rate == 0.0:
        return (
            f"At t = {diagnostic.time:.2f} s, maximum displacement is "
            f"{diagnostic.maximum_amplitude:.2f} m. Damping is zero, so the model does "
            "not intentionally remove energy."
        )
    return (
        f"At t = {diagnostic.time:.2f} s, maximum displacement is "
        f"{diagnostic.maximum_amplitude:.2f} m and approximate energy is "
        f"{diagnostic.normalized_energy:.0%} of its initial value. Damping is removing "
        "energy as the wave moves."
    )


def stability_message(report: StabilityReport) -> tuple[str, str]:
    """Return visual severity and concise actionable copy."""

    if not report.is_stable:
        return (
            "error",
            f"Playback is blocked because CFL = {report.cfl_number:.2f}. "
            f"{report.messages[0]}",
        )
    if report.cfl_number > 0.8 or report.damping_number > 0.5:
        return (
            "caution",
            f"Use caution: CFL = {report.cfl_number:.2f}. {report.messages[0]}",
        )
    return (
        "recommended",
        f"Stable setup: CFL = {report.cfl_number:.2f}. "
        "The time step is within the recommended range.",
    )


def boundary_name(boundary: BoundaryCondition) -> str:
    return {
        BoundaryCondition.FIXED: "fixed ends",
        BoundaryCondition.REFLECTIVE: "reflective edges",
        BoundaryCondition.PERIODIC: "periodic wraparound",
    }[boundary]
