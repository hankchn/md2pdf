# Style Guide

## Typography

- Body: system sans stack optimized for Chinese and English.
- Cover title: serif stack for report-like authority.
- Code: monospace stack.
- Do not scale fonts by viewport width.
- Keep letter spacing at `0` for readable Chinese text, except small uppercase labels.

## Hierarchy

- Cover title: largest text, used once.
- Body H1: major section.
- Body H2: scan-level subsection with a small accent mark.
- Body H3: compact local heading.
- Paragraphs: comfortable line height and restrained width.
- Table of contents: use consulting-report hierarchy. H1 entries should read as major chapter bands, H2 entries as indented section rows, and H3 entries as lighter local points.

## Color Tokens

- `--ink`: primary text.
- `--muted`: metadata and captions.
- `--faint`: borders and separators.
- `--soft`: quote and table background.
- `--accent`: primary report color used by cover, H1, TOC chapter markers, table headers, and diagram titles.
- `--accent-2`: complementary report color used with `--accent` in gradients, hubs, and high-emphasis table headers.
- `--accent-3`: restrained warm emphasis color for warnings only; do not use it as a competing theme color.
- `--accent-soft`, `--accent-softer`, and `--accent-border`: tints derived from the main palette for cards, tables, diagrams, and TOC surfaces.
- `--note`, `--important`, `--warning`, `--tip`: semantic colors derived from the same report palette.

Do not mix unrelated color families in one report. If the cover uses a blue-green palette, tables, diagrams, headings, and callouts should stay in that family, with warm color reserved only for risk/emphasis semantics.

## Tables

- Use a tinted header row from the report palette.
- Use light borders.
- Use alternating row backgrounds for scanability.
- Allow wrapping inside cells.
- Avoid page splitting when possible.

## Callouts

- `NOTE`: neutral information.
- `IMPORTANT`: key decision or must-read point.
- `WARNING`: risk, blocker, or caveat.
- `TIP`: recommendation or next action.

Callouts should be visible but not loud. Use a soft background and a colored left border.

## Code Blocks

- Use dark panels for multi-line code blocks.
- Show language labels when provided by the Markdown fence.
- Wrap long lines to avoid horizontal overflow in PDF.
- When a fenced block is an ASCII diagram, matrix, flow sketch, or formula, convert it into a visual diagram card instead of using the dark code style.

## Diagrams

- Use light report cards with soft accent backgrounds.
- Convert arrows and box-drawing sketches into readable node flows where possible.
- Use palette-derived hubs, nodes, and matrix cards to communicate relationships.
- Keep diagrams on one page when possible; avoid splitting a diagram across pages.

## Print

- A4 portrait.
- Use a full-bleed named `cover` page with zero margin.
- Use normal CSS `@page` margins for table-of-contents and body pages.
- Enable exact color printing with `print-color-adjust`.
- Keep headers and page numbers subtle.
- Keep report chrome minimal: omit generator labels from footers and cover-bottom labels, and render page numbers as `current / total`, not `Page current / total`.
