<p align="center"><a href="./README.md">简体中文</a> | <b>English</b></p>

# md2pdf

One-line summary: this Skill understands, redesigns, and renders Markdown documents into polished delivery-ready PDFs instead of applying default browser styles.

## What this version can do

- Parse Markdown headings, paragraphs, lists, tables, block quotes, code blocks, images, and links.
- Infer the document type and choose layouts for reports, PRDs, research briefs, or knowledge notes.
- Generate cover pages, table of contents, headers, footers, page numbers, and A4 print-friendly pages.
- Encode `diagram`, Mermaid, and ASCII-arrow code blocks as generic flows, layer stacks, matrices, or structure cards.
- Convert Markdown to intermediate HTML/CSS, then render PDF with Playwright or Chromium/Chrome.
- Run basic PDF QA for file existence, page count, file size, and render logs.

## Who it is for

- Users who need to deliver Markdown reports, PRDs, research notes, or knowledge-base content as PDFs.
- Users who do not want to tune Word or slide layouts manually, but need better results than default Markdown export.
- Codex Skill users who want reusable templates and automatic QA.

## Usage example

The repository includes a sample input:

```bash
python3 scripts/main.py --input examples/input.md --output output.pdf --template elegant-report
```

With title, author, date, and table of contents:

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

Sample visual asset:

![Sample flow](./examples/sample-flow.svg)

## Quick start

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
python3 -m playwright install chromium
```

If Python Playwright is unavailable, the script tries Node Playwright, then falls back to a local Chromium/Chrome executable. On macOS it checks:

```text
/Applications/Google Chrome.app/Contents/MacOS/Google Chrome
```

If Chrome is elsewhere:

```bash
export MBPDF_CHROME_PATH="/path/to/chrome"
```

## Common uses

- Use `elegant-report` for Chinese reports, PRDs, research analysis, and knowledge-base documents.
- Use `--template auto` to infer the document type from the content.
- Use `--debug` to keep intermediate HTML for layout inspection.
- Run QA separately:

```bash
python3 scripts/qa_pdf.py --pdf output.pdf --html output.html
```

## Current limitations

- The Markdown parser is lightweight and does not cover every CommonMark edge case.
- Page numbers depend on Chromium CSS page-counter support, which can vary by browser version.
- Current QA is file-level and does not fully replace human visual review.
- `product-doc`, `research-brief`, and `knowledge-note` are first-version template scaffolds; dedicated layout systems are still expanding.

## Security and privacy

- Do not commit Markdown or PDF files that contain internal company materials, customer data, personal information, or credentials.
- This tool does not require tokens, Cookies, API keys, or remote service credentials.
- Debug artifacts and generated PDFs should be written to explicit output paths so they do not enter source commits accidentally.

## Technical notes

```text
Markdown -> document understanding -> layout strategy -> content restructuring -> HTML/CSS -> PDF render -> QA -> final PDF
```

- `scripts/main.py` is the end-to-end entrypoint.
- `scripts/parse_md.py` handles Markdown parsing and document classification.
- `scripts/build_html.py` generates print-ready HTML/CSS.
- `scripts/render_pdf.py` renders through Playwright or Chromium/Chrome.
- `scripts/qa_pdf.py` runs basic PDF QA.
- `templates/elegant-report/` is the current primary template.

## Roadmap

- Add PDF image re-render checks for blank pages, wide tables, and code overflow.
- Expand dedicated layouts for PRDs, research briefs, and knowledge notes.
- Add a fuller Markdown parser or optional `markdown-it-py` support.
- Add font embedding and brand theme configuration.

## License

[MIT](./LICENSE)

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
      <a href="https://openai.com/codex">
        <img src="https://github.com/openai.png" width="64" height="64" style="border-radius:50%;" alt="Codex" />
        <br />
        <sub><b>Codex</b></sub>
      </a>
      <br />
      <sub>OpenAI Codex</sub>
    </td>
  </tr>
</table>
