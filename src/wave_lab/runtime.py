"""Runtime coordination for simulation, comparison, rendering, and UI state."""

from __future__ import annotations

from dataclasses import dataclass, replace

from .settings import LabSettings
from .simulation import BoundaryCondition, StabilityReport, WaveSimulation, check_stability


@dataclass(frozen=True)
class AppConfig:
    """Static desktop-loop settings that are not part of the wave physics."""

    render_interval_ms: int = 33
    base_solver_steps_per_frame: int = 3


@dataclass(frozen=True)
class UIState:
    """Small set of interaction choices owned by the shell, not the solver."""

    selected_concept: str = "overview"
    advanced_mode: bool = False
    compare_mode: bool = False
    diagnostics_expanded: bool = True


@dataclass(frozen=True)
class RenderState:
    """Cached values consumed by renderers without rebuilding spatial arrays."""

    positions_a: tuple[float, ...]
    positions_b: tuple[float, ...] | None = None
    revision: int = 0


@dataclass(frozen=True)
class SettingsUpdate:
    """Result of validating and applying one parameter update."""

    report: StabilityReport
    simulation_rebuilt: bool
    compare_cleared: bool = False


class RuntimeController:
    """Coordinate solver instances without owning any PySide6 widgets."""

    def __init__(
        self,
        settings_a: LabSettings | None = None,
        config: AppConfig | None = None,
    ) -> None:
        self.config = config or AppConfig()
        self.settings_a = settings_a or LabSettings()
        self.settings_b: LabSettings | None = None
        self.simulation_a = WaveSimulation(
            self.settings_a.simulation_parameters(),
            self.settings_a.initial_condition(),
        )
        self.simulation_b: WaveSimulation | None = None
        self.ui_state = UIState()
        self._positions_cache: dict[tuple[float, int, BoundaryCondition], tuple[float, ...]] = {}
        self.render_state = RenderState(self._positions_for(self.simulation_a))

    @property
    def playback_speed(self) -> float:
        return self.settings_a.playback_speed

    @property
    def steps_per_frame(self) -> int:
        return max(1, round(self.config.base_solver_steps_per_frame * self.playback_speed))

    def set_selected_concept(self, concept: str) -> None:
        self.ui_state = replace(self.ui_state, selected_concept=concept)

    def set_advanced_mode(self, enabled: bool) -> None:
        self.ui_state = replace(self.ui_state, advanced_mode=enabled)

    def set_diagnostics_expanded(self, expanded: bool) -> None:
        self.ui_state = replace(self.ui_state, diagnostics_expanded=expanded)

    def apply_a_settings(self, settings: LabSettings) -> SettingsUpdate:
        """Apply A settings atomically; retain the last valid solver if invalid."""

        parameters = settings.simulation_parameters()
        report = check_stability(parameters)
        physical_change = (
            parameters != self.simulation_a.parameters
            or settings.initial_condition() != self.simulation_a.initial_condition
        )
        self.settings_a = settings
        compare_cleared = False
        if physical_change:
            compare_cleared = self.simulation_b is not None or self.settings_b is not None
            self.pause()
            self.clear_compare()
        if not report.is_stable:
            return SettingsUpdate(report, simulation_rebuilt=False, compare_cleared=compare_cleared)
        if not physical_change:
            return SettingsUpdate(report, simulation_rebuilt=False)

        self.simulation_a = WaveSimulation(parameters, settings.initial_condition())
        self._refresh_render_state()
        return SettingsUpdate(report, simulation_rebuilt=True, compare_cleared=compare_cleared)

    def duplicate_a_into_b(self) -> SettingsUpdate:
        return self.apply_b_settings(self.settings_a)

    def apply_b_settings(self, settings: LabSettings) -> SettingsUpdate:
        """Restart both runs from t=0 so B contrasts remain honest."""

        parameters = settings.simulation_parameters()
        report = check_stability(parameters)
        self.pause()
        self.settings_b = settings
        if not report.is_stable:
            self.simulation_b = None
            self.ui_state = replace(self.ui_state, compare_mode=True)
            self._refresh_render_state()
            return SettingsUpdate(report, simulation_rebuilt=False)

        self.simulation_a.reset()
        self.simulation_a.pause()
        self.simulation_b = WaveSimulation(parameters, settings.initial_condition())
        self.simulation_b.pause()
        self.ui_state = replace(self.ui_state, compare_mode=True)
        self._refresh_render_state()
        return SettingsUpdate(report, simulation_rebuilt=True)

    def clear_compare(self) -> None:
        self.settings_b = None
        self.simulation_b = None
        self.ui_state = replace(self.ui_state, compare_mode=False)
        self._refresh_render_state()

    def toggle_playback(self) -> bool:
        if self.simulation_a.state.paused:
            self.simulation_a.resume()
            if self.simulation_b is not None:
                self.simulation_b.resume()
        else:
            self.pause()
        return not self.simulation_a.state.paused

    def pause(self) -> None:
        self.simulation_a.pause()
        if self.simulation_b is not None:
            self.simulation_b.pause()

    def reset(self) -> None:
        self.simulation_a.reset()
        self.simulation_a.pause()
        if self.simulation_b is not None:
            self.simulation_b.reset()
            self.simulation_b.pause()

    def step(self) -> None:
        self.simulation_a.step()
        if self.simulation_b is not None:
            self.simulation_b.step()

    def advance_frame(self) -> bool:
        """Advance solver state only while playback is active."""

        if self.simulation_a.state.paused:
            return False
        self.simulation_a.run(self.steps_per_frame)
        if self.simulation_b is not None:
            self.simulation_b.run(self.steps_per_frame)
        return True

    def _refresh_render_state(self) -> None:
        positions_b = (
            self._positions_for(self.simulation_b)
            if self.simulation_b is not None
            else None
        )
        self.render_state = RenderState(
            positions_a=self._positions_for(self.simulation_a),
            positions_b=positions_b,
            revision=self.render_state.revision + 1,
        )

    def _positions_for(self, simulation: WaveSimulation) -> tuple[float, ...]:
        parameters = simulation.parameters
        key = (parameters.domain_length, parameters.grid_points, parameters.boundary)
        positions = self._positions_cache.get(key)
        if positions is None:
            positions = tuple(parameters.positions)
            self._positions_cache[key] = positions
        return positions
