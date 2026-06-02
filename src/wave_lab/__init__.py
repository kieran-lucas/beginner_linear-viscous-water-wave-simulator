"""Numerical core for the Viscous Wave Lab educational simulator."""

from .simulation import (
    BoundaryCondition,
    DiagnosticSample,
    InitialCondition,
    SimulationParameters,
    SimulationState,
    StabilityReport,
    WaveSimulation,
    check_stability,
)

__all__ = [
    "BoundaryCondition",
    "DiagnosticSample",
    "InitialCondition",
    "SimulationParameters",
    "SimulationState",
    "StabilityReport",
    "WaveSimulation",
    "check_stability",
]

