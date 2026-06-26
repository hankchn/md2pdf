---
name: md2pdf
description: Convert Markdown documents into beautifully redesigned, print-ready PDFs. Use when Codex needs to turn a .md file into a polished PDF for reports, PRDs, research briefs, knowledge notes, internal memos, or Chinese/English business documents. This skill should not be used for naive Markdown-to-PDF conversion; it must understand document structure, improve reading hierarchy, select or apply a visual template, generate HTML/CSS, render with Playwright or Chromium, and run PDF QA.
---

# md2pdf

## Purpose

Use this skill to transform Markdown into a designed PDF deliverable. Do not simply preserve Markdown order and default browser styles. Parse the document, infer its type, normalize hierarchy, apply a print-first template, render PDF, and verify the output.

Core path:

```text
Markdown -> document understanding -> layout strategy -> content restructuring -> HTML/CSS -> PDF render -> QA -> final PDF
```

## Inputs And Outputs

Input:

- A UTF-8 Markdown file.
- Optional title, author, date, template, table-of-contents, and debug settings.

Output:

- A print-ready PDF.
- Optional intermediate HTML when `--debug` is used.
- Console QA summary with file existence, page count, file size, intermediate HTML, and render-log checks.

## Default Workflow

1. Read the source Markdown and identify front matter, title, headings, paragraphs, lists, quotes, callouts, tables, code blocks, images, and links.
2. Infer document type: `product-doc`, `research-brief`, `knowledge-note`, or `elegant-report`.
3. Normalize heading hierarchy so the rendered PDF has clear H1/H2/H3 levels and no orphan title-only body.
4. Choose a template. Default to `elegant-report`; use `--template auto` only when the inferred document type should select the template.
5. Build intermediate HTML with inline CSS from `templates/<template>/`.
6. Render PDF with Python Playwright when available, Node Playwright when available, or a local Chromium/Chrome executable as the final fallback.
7. Run QA and keep debug artifacts only when useful.

## CLI

Run from the skill directory:

```bash
python3 scripts/main.py --input examples/input.md --output output.pdf --template elegant-report
```

Useful options:

```bash
python3 scripts/main.py \
  --input examples/input.md \
  --output output.pdf \
  --template elegant-report \
  --title "Quarterly AI Product Report" \
  --author "Hank" \
  --date "2026-06-26" \
  --toc true \
  --debug
```

## Template Selection

- `elegant-report`: default and first fully designed template. Use for Chinese reports, PRDs, knowledge-base exports, research summaries, and business analysis.
- `product-doc`: scaffolded template for PRD/product documents. Currently shares the base layout with product-oriented tokens.
- `research-brief`: scaffolded template for research and analysis. Currently shares the base layout with research-oriented tokens.
- `knowledge-note`: scaffolded template for knowledge notes and memos. Currently shares the base layout with note-oriented tokens.
- `auto`: infer the document type and use the matching template if it exists.

If the user does not specify a style, use `elegant-report` because it is the strongest general-purpose layout.

## Markdown Handling

- Cover page: use `--title`, front matter `title`, first H1, or filename.
- Table of contents: generated from normalized H1/H2/H3 headings when `--toc true`; render H1 as major report chapters, H2 as indented sections, and H3 as lighter local points.
- Headings: shift heading levels upward when a document starts at H2/H3 so the PDF hierarchy is readable.
- Paragraphs and lists: preserve content, improve spacing, and use print-friendly typography.
- Block quotes: render as restrained quote panels.
- Callouts: support this syntax and render as visual cards:

```md
> [!NOTE]
> This is a note.

> [!IMPORTANT]
> This is important.

> [!WARNING]
> This is a risk.

> [!TIP]
> This is a recommendation.
```

- Tables: render with a styled header, borders, alternating rows, and print-safe wrapping.
- Code blocks: render with a dark code panel, optional language label, and wrapping to avoid horizontal overflow.
- Visual diagrams: detect plain fenced ASCII diagrams, flow sketches, matrices, and formula blocks; render them as report-style diagram cards instead of plain code blocks.
- Images: resolve local relative image paths from the Markdown file directory, constrain to page width, and render captions from alt text or title.
- Links: preserve hrefs and style them for reading without cluttering the printed page.

## Print Layout Rules

- Use a full-bleed cover page through a named `cover` page style so the cover background occupies the whole first page.
- Use normal A4 margins for table of contents and body pages so Playwright header/footer content never overlaps document content.
- Keep report chrome minimal: do not show generator names such as `md2pdf` in footers or cover-bottom labels; render page numbering as `current / total` without a `Page` prefix.
- Use a constrained consulting-report palette: one primary accent, one complementary secondary accent, soft tints derived from those accents, and a restrained warm color only for warning/emphasis states.
- Keep cover, table headers, diagrams, headings, and TOC markers on the same palette. Do not introduce unrelated red/blue/green accents inside one report.
- Do not render Markdown horizontal rules as visible long lines in report output; use whitespace instead unless a template intentionally opts into section rules.
- Prefer visual diagram cards for strategic diagrams, funnels, matrices, flywheels, architecture sketches, and formula blocks.

## PDF QA

Always run QA after rendering. The included QA checks:

- Output PDF exists.
- PDF header is valid.
- Page count is greater than zero.
- File size is not suspiciously small.
- Intermediate HTML exists during the pipeline.
- Render log does not contain obvious fatal errors.

For high-stakes deliverables, inspect the intermediate HTML and final PDF visually. See `docs/qa-checklist.md` for the manual checklist.

## Dependencies

The first version is intentionally runnable without Python Markdown/Jinja2 dependencies. It uses a local parser and simple template replacement.

Preferred renderer:

```bash
python3 -m pip install -r requirements.txt
python3 -m playwright install chromium
```

Fallback renderers:

- Node Playwright, when `playwright` is available through local `node_modules`, `NODE_PATH`, or the Codex runtime.
- A local Chromium/Chrome executable as the final fallback.
- On macOS, `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome` is auto-detected.
- Set `MBPDF_CHROME_PATH` when Chrome is elsewhere.
- Set `MBPDF_DISABLE_NODE_PLAYWRIGHT=1` or `MBPDF_DISABLE_PLAYWRIGHT=1` only when debugging renderer selection.

## Resources

- `scripts/main.py`: end-to-end pipeline.
- `scripts/parse_md.py`: Markdown parsing and document classification.
- `scripts/build_html.py`: HTML/CSS generation.
- `scripts/render_pdf.py`: Playwright/Chromium rendering.
- `scripts/render_pdf_node.cjs`: Node Playwright fallback used when Python Playwright is unavailable.
- `scripts/qa_pdf.py`: PDF QA checks.
- `templates/elegant-report/`: default polished template.
- `docs/style-guide.md`: visual rules.
- `docs/layout-rules.md`: content restructuring and pagination rules.
- `docs/qa-checklist.md`: QA checklist.
