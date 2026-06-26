# QA Checklist

Run this checklist after generating a PDF.

## Automated Checks

- Output PDF exists.
- PDF starts with `%PDF`.
- Page count is greater than zero.
- File size is not suspiciously small.
- Intermediate HTML was generated during the pipeline.
- Render log does not contain fatal errors.

Command:

```bash
python3 scripts/qa_pdf.py --pdf output.pdf --html output.html
```

## Manual Visual Checks

- Cover title is readable and not clipped.
- Table of contents links and hierarchy look correct.
- H1/H2/H3 hierarchy is visually clear.
- No heading is isolated at the bottom of a page.
- Tables fit page width.
- Code blocks wrap and do not overflow horizontally.
- Callouts are visually distinct and not split awkwardly.
- Images fit page width and captions are readable.
- Chinese punctuation and line height look natural.
- Header, footer, and page number do not overlap body content.
- Footer does not show generator labels such as `md2pdf`.
- Cover bottom does not show generator labels such as `md2pdf`.
- Page numbering uses `current / total` without a `Page` prefix.

## Failure Handling

- If PDF rendering fails, rerun with `--debug` and inspect the HTML.
- If Playwright is missing, confirm local Chrome exists or set `MBPDF_CHROME_PATH`.
- If layout looks wrong, fix the template CSS before changing parser logic.
- If Markdown structure is ambiguous, prefer improving heading normalization over adding manual instructions for the user.
