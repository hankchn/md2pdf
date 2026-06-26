# Project Rules

## Purpose

This directory contains the reusable `md2pdf` Codex Skill for redesigning Markdown documents into polished, print-ready PDFs. Treat it as a Skill package, not a one-off converter.

## Structure

- `SKILL.md`: agent-facing invocation rules and workflow. Keep it concise and operational.
- `README.md`: user-facing setup, usage, limitations, and examples.
- `templates/<template-name>/`: HTML and CSS assets for each visual template.
- `scripts/`: Python command-line implementation. Shared logic should stay in small modules here.
- `examples/`: sample Markdown input and expected output notes.
- `docs/`: detailed layout, style, and QA guidance.
- `agents/`: generated Skill UI metadata.

## Naming

- Use lowercase hyphen-case for directories and templates, such as `elegant-report`.
- Use snake_case for Python files and functions.
- Use descriptive class names in templates, prefixed by document role where useful, such as `cover-page` or `toc-list`.
- Keep generated output files out of the source tree unless they are intentional examples.

## Implementation Rules

- Prefer a simple Python pipeline: parse Markdown, build structured document data, render Jinja2 HTML, render PDF through Playwright/Chromium, then run QA.
- Do not implement a naive Markdown-to-PDF pass-through. The pipeline must identify document type, normalize hierarchy, support callouts, and apply a print-first template.
- Keep template logic reusable. A new template should only need its own `template.html`, `style.css`, and `print.css`.
- Do not hardcode user-specific absolute paths except as documented fallbacks for local Chrome discovery.
- Never store secrets or credentials in this package.

## Verification

- After changing scripts or templates, run the sample command from `README.md`.
- Run the QA script on the produced PDF.
- Run the Skill validator from `skill-creator` before considering the package complete.

## Cleanup

- Temporary HTML, logs, and rendered PDFs should go to an explicit output path or `.tmp/`.
- `--debug` may preserve intermediate HTML next to the output PDF; otherwise temporary HTML should be cleaned up.
- Do not remove user-created files without explicit instruction.
