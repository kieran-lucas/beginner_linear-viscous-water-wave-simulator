# Viscous Wave Lab

**A beginner-friendly desktop lab for exploring how linear water waves propagate
and lose energy under simplified viscous damping.**

Viscous Wave Lab turns a numerical model into an interactive learning tool.
Students can change one physical idea at a time, watch the wave profile evolve,
and connect the animation to measured amplitude, approximate energy, and
stability diagnostics.

The project is intentionally educational rather than research-grade. It uses a
readable one-dimensional model so the physics, numerical method, and interface
can all be understood from the repository.

## Demo

> **Screenshot and GIF coming soon.** Demo media will live in
> [`docs/assets/`](docs/assets/README.md). The capture guide describes the
> planned `app-overview.png` and `compare-damping.gif` assets.

A useful first experiment takes less than a minute:

1. Launch the app and press `Play` with the **Gentle ripple** preset.
2. Watch the blue wave move while the diagnostics graphs track amplitude and
   approximate energy.
3. Load **Strong damping**, then compare it with **Almost no damping**.
4. Enable **Compare Mode**, duplicate A into B, and change only B's damping
   rate. The amber dashed curve isolates the effect of stronger damping.

## What It Simulates

The app models a one-dimensional wave profile `u(x, t)` governed by:

```text
u_tt + gamma * u_t = c^2 * u_xx
```

| Symbol | Meaning |
| --- | --- |
| `u(x, t)` | Displacement from the equilibrium surface |
| `c` | Wave speed |
| `gamma` | Effective damping rate |
| `u_xx` | Spatial curvature that drives propagation |

Without damping, the wave continues to exchange kinetic and potential energy.
With positive damping, the `gamma * u_t` term opposes motion and gradually
reduces the visible wave height. This makes a useful teaching model for how
energy loss changes wave behavior.

`gamma` is an effective damping rate, not a direct measurement of fluid
viscosity. Real water-wave decay depends on additional physical assumptions,
including wavelength and fluid properties. See
[`docs/model.md`](docs/model.md) for the model scope.

## Key Features

- Real-time one-dimensional wave canvas with equilibrium line, coordinate grid,
  amplitude marker, wavelength marker, and hover readout.
- Repeating sinusoidal waves and localized Gaussian pulses.
- Guided presets for immediate experiments, including a clearly marked
  stability-risk demonstration.
- Live explanation panel that updates when a parameter changes.
- Compare Mode with synchronized A and B curves on one honest shared scale.
- Amplitude-decay and approximate-energy graphs with bounded history.
- Advanced numerical controls for grid resolution, time step, boundary
  behavior, CFL feedback, and approximate render rate.
- Fixed, reflective, and periodic boundary conditions.
- Export menu for wave images, JSON parameter snapshots, readable clipboard
  settings, and diagnostics CSV data.
- Keyboard shortcuts and visible focus states for desktop use.

## Learning Goals

The app is designed to help a beginner answer concrete questions:

- How is amplitude different from wavelength?
- What changes when a wave travels faster?
- Why does damping make peaks and troughs shrink over time?
- How do boundary conditions change what happens at the edges?
- Why can a numerical time step become unreliable?
- How can two synchronized experiments isolate one cause and effect?

## Numerical Method

The solver stores displacement and velocity on a finite one-dimensional grid.
It uses centered finite differences for the spatial second derivative and
fourth-order Runge-Kutta integration for time updates.

Before running, the app checks the Courant-Friedrichs-Lewy (CFL) number:

```text
CFL = wave speed * time step / grid spacing
```

Playback is blocked when the conservative guardrail is exceeded. Near-limit
settings remain available with a caution message so beginners can see why
numerical settings matter.

The diagnostics are computed from solver state rather than animated
placeholders. They show qualitative trends and internal consistency; they do
not claim complete physical validation of real fluids. The validation strategy
is documented in [`docs/validation.md`](docs/validation.md).

## Controls

| Control | What it changes |
| --- | --- |
| Wave shape | Choose a repeating wave or one localized Gaussian pulse. |
| Initial height | Set the starting displacement from equilibrium. |
| Wavelength | Set the distance between repeating peaks. |
| Pulse width | Set how broadly a Gaussian pulse spreads across space. |
| Wave speed | Set how quickly disturbances move across the domain. |
| Damping rate | Set how quickly simplified viscous loss removes energy. |
| Simulation speed | Change animation pace without changing the physics. |

**Advanced numerics** reveals grid points, time step, boundary behavior, the
numerical method, and CFL stability feedback.

The presets are **Gentle ripple**, **Long smooth wave**, **Strong damping**,
**Almost no damping**, **Fast propagation**, and **Stability risk demo**.

## Export and Reproduce

The desktop **Export** menu keeps report and demo capture actions available
without crowding the learning workspace:

| Action | Output |
| --- | --- |
| Export wave image | A high-resolution PNG of the current scientific wave plot. |
| Save parameter snapshot | Human-readable JSON with model, settings, and current diagnostics. |
| Copy settings as text | A report-friendly parameter summary placed on the clipboard. |
| Export diagnostics CSV | Bounded amplitude and approximate-energy history for A and optional B. |

Exports use timestamped filenames by default. JSON and CSV files are intended
for inspection, classroom reports, debugging, and reproducing parameter sets
manually in the app.

| Shortcut | Action |
| --- | --- |
| `Space` | Play or pause |
| `Right arrow` | Advance one numerical step |
| `Ctrl+R` | Reset the experiment |
| `Ctrl+D` | Duplicate A into Compare B |
| `Ctrl+G` | Hide or show diagnostics graphs |

## Run Locally

Viscous Wave Lab requires Python `3.11` or newer and uses
[PySide6](https://doc.qt.io/qtforpython-6/) for its desktop interface.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m wave_lab
```

On macOS or Linux, activate the environment with:

```bash
source .venv/bin/activate
```

After installation, the console entry point is also available:

```powershell
viscous-wave-lab
```

The first screen opens with a visible repeating wave, light but noticeable
damping, and an inline **Start here** guide. Press **Play**, adjust **Damping
rate** in the left-side **Medium** section, and use **Reset** to restart. The
right-side explanation panel updates as controls change.

If startup fails during Python initialization, the app reports the error and
shows the install and launch commands to retry. Native Qt platform errors may
still require reinstalling PySide6 or checking the local desktop environment.

## Build the Python Package

The current repository supports Python source and wheel packages. It does not
yet ship an operating-system installer.

```powershell
python -m pip install -e ".[dev]"
python -m build
```

Build artifacts are written to `dist/`. See
[`docs/packaging.md`](docs/packaging.md) for the current scope and a practical
desktop-bundling roadmap.

## Project Structure

```text
.
|-- .github/workflows/quality.yml  # CI lint, test, and package-build gates
|-- docs/                          # Model, validation, architecture, and UI notes
|-- src/wave_lab/
|   |-- simulation.py              # UI-independent damped-wave solver
|   |-- runtime.py                 # Playback, render state, and Compare Mode
|   |-- app.py                     # PySide6 desktop shell
|   |-- visualization.py           # Main wave-profile canvas
|   |-- diagnostics_panel.py       # Timeline graphs and numerical feedback
|   |-- control_panel.py           # Parameters, presets, and advanced controls
|   `-- education.py               # Structured beginner-facing copy
`-- tests/                         # Numerical, runtime, and offscreen UI checks
```

The solver does not import PySide6. This keeps the numerical core testable and
makes future visualization or export work possible without rewriting the
physics layer.

## Quality Gates

Install the development tools:

```powershell
python -m pip install -e ".[dev]"
```

Run the same lint, test, and package-build commands used by CI:

```powershell
$env:PYTHONPATH = "src"
$env:QT_QPA_PLATFORM = "offscreen"
python -m ruff check .
python -m unittest discover -s tests -v
python -m build
```

On macOS or Linux, set the environment variables with `export`:

```bash
export PYTHONPATH=src
export QT_QPA_PLATFORM=offscreen
```

The automated checks cover numerical consistency, stability guardrails,
bounded diagnostic history, Compare Mode independence, and core offscreen UI
behavior.

## Roadmap

- Add the overview screenshot and damping-comparison GIF.
- Add tested desktop bundles for classroom machines that do not have Python.
- Add parameter-snapshot import for one-click experiment restoration.
- Add optional side-by-side Compare Mode for users who prefer separate plots.
- Explore a lightweight two-dimensional surface view while keeping the 1D
  teaching mode as the default.
- Add classroom exercise cards for wavelength, damping, boundaries, and
  numerical stability.

## Limitations

- The simulation is one-dimensional.
- The damped linear wave equation is a simplified educational model.
- The damping rate is not a complete fluid-viscosity calculation.
- Linear waves do not break, steepen, or model nonlinear interactions.
- Grid resolution and time-step size affect numerical accuracy.
- Approximate energy is a discrete diagnostic for learning and regression
  testing, not a laboratory measurement.

## Further Reading

- [`docs/model.md`](docs/model.md): equation, numerical method, and assumptions.
- [`docs/validation.md`](docs/validation.md): test scope and quality gates.
- [`docs/runtime-architecture.md`](docs/runtime-architecture.md): simulation
  loop and ownership boundaries.
- [`docs/design-system.md`](docs/design-system.md): scientific desktop visual
  language and accessibility states.
