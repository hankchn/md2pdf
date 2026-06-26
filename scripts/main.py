#!/usr/bin/env python3
"""End-to-end md2pdf pipeline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from build_html import build_html, skill_root
from parse_md import parse_markdown_file
from qa_pdf import check_pdf, format_report
from render_pdf import render_pdf


def parse_bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    return value.strip().lower() not in {"false", "0", "no", "off"}


def choose_template(document: dict, requested: str) -> str:
    if requested != "auto":
        return requested
    suggested = document.get("template_suggestion") or "elegant-report"
    template_dir = skill_root() / "templates" / suggested
    return suggested if template_dir.exists() else "elegant-report"


def write_render_log(path: Path, result: dict) -> Path | None:
    log_parts = []
    if result.get("fallback_errors"):
        log_parts.append("Fallback errors:\n" + "\n".join(result["fallback_errors"]))
    if result.get("stdout"):
        log_parts.append("STDOUT:\n" + result["stdout"])
    if result.get("stderr"):
        log_parts.append("STDERR:\n" + result["stderr"])
    if not log_parts:
        return None
    log_path = path.with_suffix(".render.log")
    log_path.write_text("\n\n".join(log_parts), encoding="utf-8")
    return log_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Redesign a Markdown document into a polished, print-ready PDF."
    )
    parser.add_argument("--input", required=True, help="Input Markdown file")
    parser.add_argument("--output", required=True, help="Output PDF file")
    parser.add_argument(
        "--template",
        default="elegant-report",
        help="Template name, or 'auto'. Default: elegant-report",
    )
    parser.add_argument("--title", help="Override document title")
    parser.add_argument("--author", help="Override author")
    parser.add_argument("--date", help="Override date")
    parser.add_argument("--toc", default="true", help="Generate table of contents: true/false")
    parser.add_argument("--debug", action="store_true", help="Keep intermediate HTML and logs")
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    html_path = output_path.with_suffix(".html")

    document = parse_markdown_file(
        input_path,
        title=args.title,
        author=args.author,
        date=args.date,
    )
    template_name = choose_template(document, args.template)
    html_text = build_html(
        document,
        template_name=template_name,
        toc=parse_bool(args.toc),
        source_dir=input_path.parent,
    )
    html_path.write_text(html_text, encoding="utf-8")

    render_result = render_pdf(html_path, output_path)
    log_path = write_render_log(output_path, render_result)
    qa_report = check_pdf(output_path, html_path=html_path, render_log_path=log_path)

    summary = {
        "input": str(input_path),
        "output": str(output_path),
        "html": str(html_path),
        "template": template_name,
        "document_type": document.get("document_type"),
        "render_method": render_result.get("method"),
        "qa_passed": qa_report["passed"],
        "page_count": qa_report["page_count"],
        "debug": args.debug,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(format_report(qa_report))

    if qa_report["passed"] and not args.debug:
        html_path.unlink(missing_ok=True)
        if log_path:
            log_path.unlink(missing_ok=True)
    return 0 if qa_report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
