# Packaging and Launch Experience

Viscous Wave Lab is currently distributed as a Python package. This keeps the
development workflow small and transparent while the desktop experience is
still evolving.

## Supported Workflow

Use Python `3.11` or newer:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m wave_lab
```

The installed console entry point is equivalent:

```powershell
viscous-wave-lab
```

## Python Package Build

Install development tools and build both the source archive and wheel:

```powershell
python -m pip install -e ".[dev]"
python -m build
```

Artifacts are written to `dist/`. CI runs the same package-build command after
linting and tests.

## First Launch

The app opens with the **Gentle ripple** preset:

- a visible repeating wave with `0.16 1/s` effective damping;
- an inline **Start here** guide above the workspace;
- a left-side **Damping rate** control in the **Medium** section;
- **Play**, **Reset**, and **Step** controls;
- a right-side explanation panel that updates as parameters change.

This keeps the initial experiment useful for a short classroom or portfolio
demo without requiring a separate tutorial window.

## Desktop Bundle Roadmap

An operating-system installer is not committed yet. A practical next packaging
phase is:

1. Add a PyInstaller build specification for Windows.
2. Build in a clean CI job so bundled Qt plugins are verified explicitly.
3. Smoke-test launch, image export, and file dialogs on a machine without a
   development Python environment.
4. Add an application icon, version metadata, and a signed release archive.
5. Evaluate macOS and Linux bundles only after the Windows classroom path is
   reproducible.

Qt desktop bundling needs platform-specific testing. Treating `python -m build`
as an installer build would be misleading; it creates Python packages only.
