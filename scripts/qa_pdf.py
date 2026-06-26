#!/usr/bin/env python3
"""Basic QA checks for generated PDFs."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ERROR_PATTERNS = [
    re.compile(pattern, re.I)
    for pattern in [
        r"printtopdf failed",
        r"navigation timeout",
        r"render failed",
        r"traceback",
        r"exception",
    ]
]


def count_pdf_pages(data: bytes) -> int:
    return len(re.findall(rb"/Type\s*/Page\b", data))


def check_pdf(
    pdf_path: str | Path,
    *,
    html_path: str | Path | None = None,
    render_log_path: str | Path | None = None,
    min_size_bytes: int = 8_000,
) -> dict[str, Any]:
    pdf_path = Path(pdf_path)
    checks: list[dict[str, Any]] = []

    def add(name: str, status: str, detail: str) -> None:
        checks.append({"name": name, "status": status, "detail": detail})

    if not pdf_path.exists():
        add("pdf_exists", "fail", f"Missing output PDF: {pdf_path}")
        return {"passed": False, "checks": checks, "page_count": 0, "file_size": 0}

    data = pdf_path.read_bytes()
    size = len(data)
    add("pdf_exists", "pass", str(pdf_path))
    add(
        "pdf_header",
        "pass" if data.startswith(b"%PDF") else "fail",
        "PDF header found" if data.startswith(b"%PDF") else "Output does not start with %PDF",
    )
    page_count = count_pdf_pages(data)
    add(
        "page_count",
        "pass" if page_count > 0 else "fail",
        f"{page_count} page(s)",
    )
    if size < min_size_bytes:
        add("file_size", "warn", f"{size} bytes is unusually small")
    else:
        add("file_size", "pass", f"{size} bytes")

    if html_path:
        html_path = Path(html_path)
        add(
            "intermediate_html",
            "pass" if html_path.exists() and html_path.stat().st_size > 0 else "fail",
            str(html_path) if html_path.exists() else "Intermediate HTML missing",
        )

    if render_log_path:
        log_path = Path(render_log_path)
        if log_path.exists():
            log_text = log_path.read_text(encoding="utf-8", errors="replace")
            has_error = any(pattern.search(log_text) for pattern in ERROR_PATTERNS)
            add(
                "render_log",
                "fail" if has_error else "pass",
                "Fatal render error found" if has_error else f"{log_path} checked",
            )
        else:
            add("render_log", "pass", "No render log was produced")
    else:
        add("render_log", "pass", "No render log was provided")

    failed = any(check["status"] == "fail" for check in checks)
    return {
        "passed": not failed,
        "checks": checks,
        "page_count": page_count,
        "file_size": size,
    }


def format_report(report: dict[str, Any]) -> str:
    lines = ["PDF QA: " + ("PASS" if report["passed"] else "FAIL")]
    for check in report["checks"]:
        lines.append(f"- {check['status'].upper()} {check['name']}: {check['detail']}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run basic QA checks on a generated PDF.")
    parser.add_argument("--pdf", required=True, help="Generated PDF path")
    parser.add_argument("--html", help="Intermediate HTML path")
    parser.add_argument("--render-log", help="Render log path")
    parser.add_argument("--json", action="store_true", help="Print JSON report")
    args = parser.parse_args()

    report = check_pdf(args.pdf, html_path=args.html, render_log_path=args.render_log)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(format_report(report))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
