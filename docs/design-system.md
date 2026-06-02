# Visual Design System

Viscous Wave Lab uses a light scientific theme. Visual polish should reinforce
measurement, comparison, and explanation rather than decorate the interface.
The source of truth is `src/wave_lab/design_system.py`.

## Color Tokens

| Role | Token | Value |
| --- | --- | --- |
| App background | `app_background` | `#F4F7FA` |
| Panel and canvas surface | `panel_background`, `canvas_background` | `#FFFFFF` |
| Primary text | `text_primary` | `#172033` |
| Secondary text | `text_secondary` | `#5B667A` |
| Disabled text | `text_disabled` | `#8C97A8` |
| Border | `border` | `#DCE2EA` |
| Strong border | `border_strong` | `#B8C4D3` |
| Primary action and A wave | `primary` | `#1769AA` |
| Compare B wave | `comparison` | `#C77C18` |
| Stable state | `success` | `#26734D` |
| Warning state | `warning` | `#A76500` |
| Error state | `error` | `#B42318` |
| Keyboard focus | `focus` | `#0B75C9` |

Color is never the only carrier of meaning. Stability states include text, and
Compare Mode uses both color and line style.

## Typography

Use the system sans-serif stack for interface text and Consolas or another
monospace font for equations.

| Role | Size |
| --- | --- |
| App title | `20 px` |
| Panel heading | `15 px` |
| Subtitle | `13 px` |
| Standard control and diagnostic text | `12 px` |
| Helper text | `11 px` |
| Equation text | `14 px` monospace |

## Spacing

The reusable spacing scale is `4`, `8`, `12`, `16`, and `20 px`. Panels use
compact borders with `4-5 px` corner radii. Group boxes, diagnostics, and graph
regions use spacing and alignment instead of shadows, blur, or gradients.

## Controls

- Primary buttons: ocean blue fill for the main playback action.
- Secondary buttons: white surface with a visible border.
- Ghost buttons: minimal treatment for low-priority actions such as collapsing
  diagnostics or stepping once.
- Warning buttons: amber treatment, reserved for actions that intentionally
  demonstrate risk.
- Inputs: white surfaces, clear border hover state, and a `2 px` keyboard focus
  ring.
- Tooltips: dark, high-contrast, concise, and paired with status-bar guidance.

## Application States

- Empty or preparing: keep the canvas visible and show `Preparing wave profile...`.
- Stable: green text and a concrete CFL value.
- Caution: amber text explaining why the setting is near a recommended limit.
- Error: red text with an actionable correction; unstable playback is blocked.
- Loading: retain existing chart content where possible. Long-running export
  work should add an inline progress message rather than a full-screen overlay.

## Keyboard Shortcuts

| Shortcut | Action |
| --- | --- |
| `Space` | Play or pause |
| `Right arrow` | Advance one numerical step |
| `Ctrl+R` | Reset experiment |
| `Ctrl+D` | Duplicate A into Compare B |
| `Ctrl+G` | Hide or show diagnostics graphs |
