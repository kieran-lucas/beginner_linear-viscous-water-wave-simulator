# Final Product Polish Review

Viscous Wave Lab is intentionally a small scientific learning workspace rather
than a general-purpose simulation dashboard. Its identity comes from connecting
one readable wave profile to live explanation, measurable decay, stability
feedback, and controlled A/B experiments.

## Review Perspectives

### Beginner Learner

The first screen answers what to do without a modal tutorial: press **Play**,
change **Damping rate**, use **Reset**, and read the explanation panel. Guided
presets give meaningful experiments without requiring numerical guesses.

### Developer

The numerical solver remains independent from PySide6. Runtime coordination,
rendering, educational copy, exports, and widgets have separate modules. Tests
cover qualitative physics, stability guardrails, Compare Mode, diagnostics,
exports, and offscreen UI behavior.

### Teacher or Evaluator

The interface pairs visible behavior with amplitude and approximate-energy
graphs. It labels damping as an effective simplified rate and documents that the
model is one-dimensional and linear. The stability-risk preset is deliberately
blocked until the numerical settings are corrected.

### Portfolio Reviewer

The repository presents a coherent desktop product: calm scientific styling,
purposeful beginner copy, deterministic numerical behavior, export support,
CI quality gates, packaging notes, and an honest scope statement.

## Polish Changes

- Beginner repeating-wave presets now meet their fixed-end boundaries. This
  prevents an artificial edge discontinuity from distracting from damping.
- The first launch now uses a localized **Traveling pulse** experiment. With
  zero starting velocity it separates into visible moving disturbances, making
  propagation clearer than a standing sinusoidal mode.
- Compare Mode stays compact until enabled, keeping the default hierarchy
  focused on the wave canvas and explanation.
- The canvas and diagnostics minimum sizes were tightened for normal laptop
  screens without shrinking labels or removing measured output.

## Prioritized TODO

1. Add a short damping-comparison GIF beside the completed screenshot gallery.
2. Produce and smoke-test a Windows desktop bundle for classroom machines.
3. Import exported JSON snapshots to restore experiments in one action.
4. Add optional classroom exercise cards with expected observations.
5. Evaluate side-by-side Compare Mode and a 2D view only if they preserve the
   clarity and performance of the default 1D lab.
