# Viscous Wave Lab

A beginner-friendly desktop learning tool for simulating linear water waves with
viscous damping. The first desktop visualization animates the one-dimensional
surface profile with restrained scientific styling and a reusable rendering
component.

The educational model is:

```text
u_tt + gamma * u_t = c^2 * u_xx
```

Here, `u` is displacement, `c` is wave speed, and `gamma` is an effective
damping rate. The solver supports Gaussian and sinusoidal initial profiles,
fixed, reflective, and periodic boundaries, stability checks, pause/run/step
controls, and amplitude and energy diagnostics.

## Run the desktop preview

Create a virtual environment and install the package:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .
python -m wave_lab
```

The canvas shows the current wave, equilibrium line, coordinate grid, amplitude
marker, hover readout, energy status, and an optional live comparison overlay.
Playback uses a capped render timer while the solver performs multiple small
updates per frame.

The left panel provides beginner-oriented controls for initial height,
wavelength or pulse width, wave speed, simplified damping rate, and playback
speed. Presets provide immediate experiments. Advanced numerics reveal grid
resolution, time step, boundary behavior, RK4 method details, and CFL stability
feedback. Unsafe settings remain visible for teaching but cannot run.

The right-side explanation panel acts as a compact interactive textbook. It
connects the visible equation to the selected control, reports what changed,
interprets live amplitude and approximate energy values, and elevates specific
stability guidance. Educational copy is centralized in
[`src/wave_lab/education.py`](src/wave_lab/education.py) so concepts can be
reviewed or localized without searching through widget code.

Compare Mode overlays a synchronized B experiment as an amber dashed line over
the blue A experiment. `Duplicate A into B` copies every setting and the initial
condition, then a focused B editor changes one physical value: initial height,
wavelength, wave speed, or damping rate. Both clocks restart and advance
together after a B edit. The shared plot scale and paired amplitude and energy
readouts keep the comparison honest.

The collapsible diagnostics area turns the animation into a measurable
experiment. It shows simulation time, maximum wave height, approximate energy,
CFL stability guidance, and clean amplitude-decay and energy-trend timelines.
Compare Mode adds an amber dashed B timeline. Historical samples are capped to
avoid memory growth during long sessions, and the graphs downsample only while
drawing. Advanced numerics also reveals an approximate rendered-frame rate.

The desktop shell uses a centralized light scientific design system with calm
ocean-blue actions, keyboard-visible focus states, concise tooltips, and no
decorative gradients or heavy effects. See
[`docs/design-system.md`](docs/design-system.md) for tokens, typography,
spacing, interaction states, and keyboard shortcuts.

## Run the tests

The validation suite uses Python's standard library. PySide6 rendering tests run
with Qt's offscreen platform:

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
```

For the model assumptions and numerical-method notes, see
[`docs/model.md`](docs/model.md).
