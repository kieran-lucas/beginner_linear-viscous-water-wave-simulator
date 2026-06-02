# Validation Strategy

Viscous Wave Lab is an educational simulator. Its automated checks establish
internal consistency and trustworthy beginner-facing behavior. They do not
claim that the reduced one-dimensional equation reproduces every property of
real viscous water waves.

## Numerical Checks

The suite validates:

- deterministic evolution from identical initial conditions;
- near-conservation of discrete energy for an undamped periodic sine mode;
- energy decay when positive damping is enabled;
- agreement with the analytic damped evolution of a discretized periodic sine
  mode within a numerical tolerance;
- fixed, reflective, and periodic boundary handling;
- exact reset to the selected initial state;
- rejection of invalid physical and numerical parameters;
- caution and blocking behavior around the conservative CFL guardrail;
- bounded diagnostic history during long sessions.

The analytic sine-mode test uses the discrete spatial wave number produced by
the finite-difference stencil. This verifies the implemented numerical method
without pretending that a finite grid is identical to a continuous fluid.

## Runtime and UI Checks

The suite also checks:

- pause, resume, reset, and single-step behavior;
- stable handling of parameter changes;
- cached spatial positions across render frames;
- synchronized but independent A and B solver state in Compare Mode;
- honest shared visual scaling for comparison overlays;
- offscreen rendering of the wave canvas;
- diagnostics synchronization, progressive disclosure, warnings, educational
  copy, keyboard shortcuts, and semantic design-system roles.

## Quality Gates

Run the same gates used by CI:

```powershell
$env:PYTHONPATH = "src"
$env:QT_QPA_PLATFORM = "offscreen"
python -m ruff check .
python -m unittest discover -s tests -v
python -m build
```

CI runs these commands on Python `3.12`. The desktop app itself supports Python
`3.11` and newer.

