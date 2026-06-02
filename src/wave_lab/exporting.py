"""File-export helpers kept independent from desktop widgets and solver updates."""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Sequence

from .settings import LabSettings
from .simulation import DiagnosticSample

MODEL_EQUATION = "u_tt + gamma * u_t = c^2 * u_xx"


def timestamp_slug(now: datetime | None = None) -> str:
    """Return a file-system-friendly local timestamp."""

    return (now or datetime.now()).strftime("%Y%m%d-%H%M%S")


def suggested_filename(kind: str, extension: str, now: datetime | None = None) -> str:
    """Build a predictable export name suitable for reports and demo captures."""

    return f"viscous-wave-lab-{kind}-{timestamp_slug(now)}.{extension.lstrip('.')}"


def settings_to_dict(settings: LabSettings) -> dict[str, object]:
    """Represent user-selected values with readable JSON-compatible types."""

    return {
        "wave_shape": settings.wave_shape,
        "amplitude_m": settings.amplitude,
        "wavelength_m": settings.wavelength,
        "pulse_width_m": settings.pulse_width,
        "wave_speed_m_per_s": settings.wave_speed,
        "damping_rate_per_s": settings.damping_rate,
        "playback_speed_multiplier": settings.playback_speed,
        "domain_length_m": settings.domain_length,
        "grid_points": settings.grid_points,
        "time_step_s": settings.time_step,
        "boundary_condition": settings.boundary.value,
    }


def snapshot_payload(
    settings_a: LabSettings,
    diagnostic_a: DiagnosticSample | None = None,
    *,
    settings_b: LabSettings | None = None,
    diagnostic_b: DiagnosticSample | None = None,
    now: datetime | None = None,
) -> dict[str, object]:
    """Create an inspectable experiment snapshot without exposing solver internals."""

    payload: dict[str, object] = {
        "format": "viscous-wave-lab-parameter-snapshot",
        "version": 1,
        "created_at": (now or datetime.now()).astimezone().isoformat(timespec="seconds"),
        "model": {
            "equation": MODEL_EQUATION,
            "note": "Educational one-dimensional damped linear wave model.",
        },
        "simulation_a": {
            "settings": settings_to_dict(settings_a),
            "diagnostics": _diagnostic_to_dict(diagnostic_a),
        },
    }
    if settings_b is not None:
        payload["simulation_b"] = {
            "settings": settings_to_dict(settings_b),
            "diagnostics": _diagnostic_to_dict(diagnostic_b),
        }
    return payload


def readable_snapshot_text(
    settings_a: LabSettings,
    diagnostic_a: DiagnosticSample | None = None,
    *,
    settings_b: LabSettings | None = None,
    diagnostic_b: DiagnosticSample | None = None,
) -> str:
    """Format settings for a report, issue, or clipboard."""

    sections = [_readable_section("Simulation A", settings_a, diagnostic_a)]
    if settings_b is not None:
        sections.append(_readable_section("Simulation B", settings_b, diagnostic_b))
    return "\n\n".join(
        [
            "Viscous Wave Lab parameter snapshot",
            f"Model: {MODEL_EQUATION}",
            *sections,
        ]
    )


def write_snapshot_json(path: str | Path, payload: dict[str, object]) -> Path:
    """Write a human-readable parameter snapshot."""

    target = Path(path)
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return target


def write_diagnostics_csv(
    path: str | Path,
    history_a: Sequence[DiagnosticSample],
    history_b: Sequence[DiagnosticSample] | None = None,
) -> Path:
    """Write bounded diagnostic history for plotting or reproducibility notes."""

    target = Path(path)
    compare_history = history_b or ()
    row_count = max(len(history_a), len(compare_history))
    with target.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            [
                "a_time_s",
                "a_maximum_amplitude_m",
                "a_approximate_energy",
                "a_normalized_energy",
                "b_time_s",
                "b_maximum_amplitude_m",
                "b_approximate_energy",
                "b_normalized_energy",
            ]
        )
        for index in range(row_count):
            writer.writerow(
                _diagnostic_csv_values(history_a, index)
                + _diagnostic_csv_values(compare_history, index)
            )
    return target


def save_image(path: str | Path, image) -> Path:
    """Save a Qt image-like object while surfacing format or file-system failures."""

    target = Path(path)
    if not image.save(str(target)):
        raise OSError(f"Could not save image to {target}")
    return target


def _diagnostic_to_dict(sample: DiagnosticSample | None) -> dict[str, float] | None:
    if sample is None:
        return None
    return {
        "time_s": sample.time,
        "maximum_amplitude_m": sample.maximum_amplitude,
        "approximate_energy": sample.energy,
        "normalized_energy": sample.normalized_energy,
    }


def _diagnostic_csv_values(
    history: Sequence[DiagnosticSample],
    index: int,
) -> list[float | str]:
    if index >= len(history):
        return ["", "", "", ""]
    sample = history[index]
    return [
        sample.time,
        sample.maximum_amplitude,
        sample.energy,
        sample.normalized_energy,
    ]


def _readable_section(
    title: str,
    settings: LabSettings,
    diagnostic: DiagnosticSample | None,
) -> str:
    lines = [
        title,
        f"  Wave shape: {settings.wave_shape}",
        f"  Initial height: {settings.amplitude:g} m",
        f"  Wavelength: {settings.wavelength:g} m",
        f"  Pulse width: {settings.pulse_width:g} m",
        f"  Wave speed: {settings.wave_speed:g} m/s",
        f"  Damping rate: {settings.damping_rate:g} 1/s",
        f"  Playback speed: {settings.playback_speed:g}x",
        f"  Domain length: {settings.domain_length:g} m",
        f"  Grid points: {settings.grid_points}",
        f"  Time step: {settings.time_step:g} s",
        f"  Boundary condition: {settings.boundary.value}",
    ]
    if diagnostic is not None:
        lines.extend(
            [
                f"  Current time: {diagnostic.time:g} s",
                f"  Maximum amplitude: {diagnostic.maximum_amplitude:g} m",
                f"  Approximate normalized energy: {diagnostic.normalized_energy:.1%}",
            ]
        )
    return "\n".join(lines)
