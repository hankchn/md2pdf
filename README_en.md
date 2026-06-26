<p align="center"><a href="./README.md">简体中文</a> | <b>English</b></p>

# md2pdf Skill

md2pdf is a Codex Skill that turns Markdown documents into polished, print-ready PDFs. It is not a plain Markdown-to-PDF pass-through: the pipeline parses the document structure, normalizes the reading hierarchy, applies a print-first template, renders HTML/CSS to PDF, and runs basic QA.

Core pipeline:

```text
Markdown -> document understanding -> layout strategy -> content restructuring -> HTML/CSS -> PDF render -> QA -> final PDF
```

## Installation

The first version does not require third-party Python Markdown or Jinja2 packages. It needs Python 3 and a usable Chromium or Chrome executable.

For the most reliable renderer, install Playwright:

```bash
python3 -m pip install -r requirements.txt
python3 -m playwright install chromium
```

If Python Playwright is not available, md2pdf tries Node Playwright. In Codex Desktop, it can often reuse shared Node dependencies from the runtime. As a final fallback, it uses local Chrome CLI. On macOS, the default Chrome path is:

```text
/Applications/Google Chrome.app/Contents/MacOS/Google Chrome
```

If Chrome is installed elsewhere:

```bash
export MBPDF_CHROME_PATH="/path/to/chrome"
```

Renderer debugging flags:

```bash
export MBPDF_DISABLE_PLAYWRIGHT=1
export MBPDF_DISABLE_NODE_PLAYWRIGHT=1
```

## Usage

Run from the `md2pdf` directory:

```bash
python3 scripts/main.py --input examples/input.md --output output.pdf --template elegant-report
```

Keep the intermediate HTML for layout inspection:

```bash
python3 scripts/main.py \
  --input examples/input.md \
  --output output.pdf \
  --template elegant-report \
  --title "AI Product Analysis Report" \
  --author "Hank" \
  --date "2026-06-26" \
  --toc true \
  --debug
```

Run QA separately:

```bash
python3 scripts/qa_pdf.py --pdf output.pdf --html output.html
```

To run the official Skill structure validator from `skill-creator`, install `PyYAML` first:

```bash
python3 -m pip install PyYAML
python3 /Users/yanghuan/.codex/skills/.system/skill-creator/scripts/quick_validate.py .
```

## Templates

- `elegant-report`: the primary template for Chinese reports, PRDs, research analysis, and knowledge-base documents.
- `product-doc`: a product-document template scaffold that currently reuses the base layout with product-oriented color tokens.
- `research-brief`: a research-brief template scaffold that currently reuses the base layout with research-oriented color tokens.
- `knowledge-note`: a knowledge-note template scaffold that currently reuses the base layout with note-oriented color tokens.
- `auto`: infers the template from document keywords.

Use `elegant-report` by default unless a more specific template is needed.

## Current Capabilities

- Parses headings, paragraphs, ordered and unordered lists, block quotes, code blocks, tables, links, and images.
- Supports `> [!NOTE]`, `> [!IMPORTANT]`, `> [!WARNING]`, and `> [!TIP]` callouts.
- Generates cover pages, table of contents, headers, minimal footers, CSS page numbers, and A4 portrait pages.
- Identifies document type and normalizes heading hierarchy for consulting-style chapters, sections, and local points.
- Uses a consistent report color system across covers, tables, diagrams, and headings.
- Keeps footers minimal: only `current / total`, with no tool name or `Page` prefix.
- Generates intermediate HTML/CSS.
- Renders PDFs through Playwright or Chromium/Chrome with background printing enabled.
- Runs basic PDF QA.

## Limitations

- The Markdown parser is lightweight and does not cover every CommonMark edge case.
- Page numbering depends on Chromium CSS page counter behavior and may vary by Chrome version.
- QA is currently file-level only. It does not yet automatically detect text overflow or large blank areas.
- `product-doc`, `research-brief`, and `knowledge-note` are runnable template scaffolds, not fully independent layout systems yet.

## Roadmap

- Add PDF-to-image visual checks for blank pages, overly wide tables, and code block overflow.
- Expand independent layouts for PRDs, research briefs, and knowledge notes.
- Add a more complete Markdown parser or optional `markdown-it-py` support.
- Add font embedding and brand theme configuration.

## Contributors

<table>
  <tr>
    <td align="center">
      <a href="https://github.com/hankchn">
        <img src="https://github.com/hankchn.png" width="64" height="64" style="border-radius:50%;" alt="hankchn" />
        <br />
        <sub><b>hankchn</b></sub>
      </a>
      <br />
      <sub>Hank Yang</sub>
    </td>
    <td align="center">
      <a href="https://claude.ai">
        <img src="https://avatars.githubusercontent.com/u/76263028?s=200" width="64" height="64" style="border-radius:50%;" alt="Claude" />
        <br />
        <sub><b>Claude</b></sub>
      </a>
      <br />
      <sub>Anthropic AI</sub>
    </td>
  </tr>
</table>
