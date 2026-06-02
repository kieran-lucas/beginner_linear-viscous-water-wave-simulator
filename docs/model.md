# Numerical Model

Viscous Wave Lab begins with a deliberately small one-dimensional model:

```text
u_tt + gamma * u_t = c^2 * u_xx
```

- `u(x, t)` is surface displacement.
- `c` is wave speed.
- `gamma` is an effective damping rate.

`gamma` is not a direct measurement of fluid viscosity. Real viscous water-wave
decay depends on wavelength and additional physical assumptions. This reduced
equation is useful for learning because it makes propagation and damping visible
without requiring a research-grade fluid model.

## Numerical Method

The solver stores displacement and velocity on a one-dimensional grid. It uses:

- centered finite differences for the spatial second derivative;
- fourth-order Runge-Kutta integration for time updates;
- fixed, reflective, or periodic boundaries;
- a conservative stability guardrail based on `c * dt / dx <= 1.0`.

The diagnostics report maximum absolute displacement and an approximate discrete
energy. Energy should trend downward when damping is enabled. Small numerical
variations are expected because the model is discretized.

## Limitations

- The simulation is one-dimensional.
- Linear waves do not break, steepen, or interact nonlinearly.
- Damping is an effective rate rather than a complete viscosity model.
- Grid resolution and time-step size affect numerical accuracy.

The module is independent from UI code so a desktop interface can animate it,
pause it, single-step it, and graph its diagnostics without owning the physics.

