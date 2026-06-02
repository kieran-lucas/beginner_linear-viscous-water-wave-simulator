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
marker, hover readout, energy status, and an optional comparison snapshot.
Playback uses a capped render timer while the solver performs multiple small
updates per frame.

The left panel provides beginner-oriented controls for initial height,
wavelength or pulse width, wave speed, simplified damping rate, and playback
speed. Presets provide immediate experiments. Advanced numerics reveal grid
resolution, time step, boundary behavior, RK4 method details, and CFL stability
feedback. Unsafe settings remain visible for teaching but cannot run.

## Run the tests

The validation suite uses Python's standard library. PySide6 rendering tests run
with Qt's offscreen platform:

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
```

For the model assumptions and numerical-method notes, see
[`docs/model.md`](docs/model.md).
