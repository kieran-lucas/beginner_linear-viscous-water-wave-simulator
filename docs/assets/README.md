# Demo Assets

This directory is reserved for GitHub-facing demo media.

The repository includes these GitHub-facing captures:

| File | Purpose |
| --- | --- |
| `app-overview.png` | Default traveling-pulse workspace with measured decay. |
| `compare-damping.png` | A/B overlay with different damping rates on one shared scale. |
| `advanced-numerics.png` | Advanced controls with CFL feedback visible. |
| `stability-warning.png` | Blocked playback and actionable unstable-CFL guidance. |

One useful follow-up asset remains:

| File | Purpose |
| --- | --- |
| `compare-damping.gif` | Short A/B loop with different damping rates on the shared plot scale. |

## Capture Checklist

- Use the default light theme at a readable desktop window size.
- Start from the **Traveling pulse** preset for the overview screenshot.
- Keep the explanation panel and diagnostics graphs visible.
- For the GIF, duplicate A into B and change only B's damping rate.
- Capture a short loop that makes decay visible without creating a large file.
- Avoid including unrelated desktop windows, personal paths, or notifications.

The root `README.md` embeds the PNG gallery. Add the GIF beside the compare
screenshot after recording a compact loop.

Use **Export > Export wave image...** to create a clean high-resolution plot
for supporting figures. The main workspace screenshot still needs a desktop
screen capture because it includes controls, explanation, and diagnostics.
