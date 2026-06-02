# Runtime Architecture

Viscous Wave Lab keeps numerical work independent from PySide6 widgets.

## Ownership Boundaries

| Concern | Owner |
| --- | --- |
| Static render interval and base solver steps | `AppConfig` |
| User-selected experiment values | `LabSettings` in `settings.py` |
| Displacement, velocity, clock, and bounded diagnostics | `WaveSimulation` |
| Cached plot positions and render revision | `RenderState` |
| Advanced Mode, Compare Mode, selected concept, diagnostics expansion | `UIState` |
| Play, pause, reset, step, A/B lifecycle | `RuntimeController` |
| Widget wiring and paint requests | `MainWindow` |

`RuntimeController` is UI-framework independent. The desktop shell forwards
events to it and renders the resulting solver state.

## Simulation Loop

The Qt timer requests a frame approximately every `33 ms`. During playback, the
controller advances a small number of solver steps based on the selected
playback speed. Rendering happens once after that batch, rather than after every
numerical update.

Playback-speed changes update the loop policy without rebuilding the solver.
Physical parameter changes pause playback and atomically replace the solver with
a deterministic `t = 0` state. Invalid settings keep the last valid solver but
block playback until corrected.

Compare Mode reuses the same solver class. A and B advance through one
controller method and restart together after a B edit.

## Performance Guardrails

- Plot positions are cached in `RenderState` until physical parameters change.
- Rendering consumes solver snapshots without owning numerical updates.
- Diagnostic history is capped at `4000` real samples.
- Timeline graphs downsample only while painting.
- The default grid is `401` points; Advanced Mode can lower resolution.
- Input controls use bounded numeric editors. A future drag-based slider should
  preview its value locally and commit solver rebuilds on a short debounce.
