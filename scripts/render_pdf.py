#!/usr/bin/env python3
"""Render print-ready HTML into PDF through Playwright or local Chromium."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any


class RenderError(RuntimeError):
    pass


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def find_chromium() -> str | None:
    env_candidates = [
        os.environ.get("MBPDF_CHROME_PATH"),
        os.environ.get("CHROME_PATH"),
        os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH"),
    ]
    path_candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
    ]
    command_candidates = ["google-chrome", "chrome", "chromium", "chromium-browser"]

    for candidate in env_candidates + path_candidates:
        if candidate and Path(candidate).exists():
            return candidate
    for command in command_candidates:
        resolved = shutil.which(command)
        if resolved:
            return resolved
    return None


def node_module_candidates() -> list[str]:
    paths: list[str] = []
    for raw in os.environ.get("NODE_PATH", "").split(os.pathsep):
        if raw and Path(raw).exists():
            paths.append(raw)

    local_node_modules = skill_root() / "node_modules"
    if local_node_modules.exists():
        paths.append(str(local_node_modules))

    codex_runtime = (
        Path.home()
        / ".cache"
        / "codex-runtimes"
        / "codex-primary-runtime"
        / "dependencies"
        / "node"
        / "node_modules"
    )
    if codex_runtime.exists():
        paths.append(str(codex_runtime))

    seen: set[str] = set()
    deduped = []
    for path in paths:
        if path not in seen:
            deduped.append(path)
            seen.add(path)
    return deduped


def render_with_playwright(html_path: Path, output_path: Path, timeout_ms: int) -> dict[str, Any]:
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:  # pragma: no cover - depends on local environment
        raise RenderError("Playwright is not installed") from exc

    executable = find_chromium()
    with sync_playwright() as playwright:
        launch_options: dict[str, Any] = {"headless": True}
        if executable:
            launch_options["executable_path"] = executable
        browser = playwright.chromium.launch(**launch_options)
        try:
            page = browser.new_page(viewport={"width": 1240, "height": 1754})
            page.set_default_timeout(timeout_ms)
            page.goto(html_path.resolve().as_uri(), wait_until="networkidle")
            page.emulate_media(media="print")
            title = page.title() or "md2pdf"
            doc_type = page.locator(".print-header span").nth(1).text_content() or ""
            page.add_style_tag(
                content=".print-header,.print-footer{display:none!important;}"
            )
            page.pdf(
                path=str(output_path),
                format="A4",
                print_background=True,
                prefer_css_page_size=True,
                display_header_footer=True,
                header_template=header_template(title, doc_type),
                footer_template=footer_template(),
            )
        finally:
            browser.close()
    return {"method": "playwright", "stdout": "", "stderr": ""}


def html_escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def header_template(title: str, doc_type: str) -> str:
    return f"""
<div style="width:100%; padding:0 17mm; font-family:Arial, sans-serif; font-size:8.5pt; color:#8a96a3; display:flex; justify-content:space-between;">
  <span>{html_escape(title[:72])}</span>
  <span>{html_escape(doc_type[:40])}</span>
</div>
"""


def footer_template() -> str:
    return """
<div style="width:100%; padding:0 17mm; font-family:Arial, sans-serif; font-size:8.5pt; color:#8a96a3; display:flex; justify-content:flex-end;">
  <span><span class="pageNumber"></span> / <span class="totalPages"></span></span>
</div>
"""


def render_with_node_playwright(
    html_path: Path,
    output_path: Path,
    timeout_seconds: int,
) -> dict[str, Any]:
    node = shutil.which("node")
    if not node:
        raise RenderError("Node.js is not installed")

    module_paths = node_module_candidates()
    if not module_paths:
        raise RenderError("Node Playwright module path was not found")

    script_path = skill_root() / "scripts" / "render_pdf_node.cjs"
    executable = find_chromium() or ""
    env = os.environ.copy()
    env["NODE_PATH"] = os.pathsep.join(module_paths)
    command = [
        node,
        str(script_path),
        str(html_path.resolve()),
        str(output_path.resolve()),
        executable,
    ]
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        raise RenderError(f"Node Playwright render timed out after {timeout_seconds}s") from exc

    if result.returncode != 0:
        raise RenderError(
            f"Node Playwright render failed with exit code {result.returncode}: {result.stderr}"
        )
    if not output_path.exists():
        raise RenderError("Node Playwright finished but did not create the PDF output.")

    payload: dict[str, Any] = {}
    try:
        payload = json.loads(result.stdout.strip() or "{}")
    except json.JSONDecodeError:
        payload = {}
    return {
        "method": payload.get("method", "node-playwright"),
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def render_with_chromium_cli(html_path: Path, output_path: Path, timeout_seconds: int) -> dict[str, Any]:
    executable = find_chromium()
    if not executable:
        raise RenderError(
            "No Chromium executable found. Install Playwright browsers or set MBPDF_CHROME_PATH."
        )

    profile_dir = tempfile.mkdtemp(prefix="md2pdf-chrome-")
    command = [
        executable,
        "--headless=new",
        "--disable-gpu",
        "--disable-dev-shm-usage",
        "--no-first-run",
        "--no-default-browser-check",
        "--allow-file-access-from-files",
        f"--user-data-dir={profile_dir}",
        f"--print-to-pdf={str(output_path)}",
        "--no-pdf-header-footer",
        html_path.resolve().as_uri(),
    ]
    try:
        try:
            result = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            raise RenderError(f"Chromium CLI render timed out after {timeout_seconds}s") from exc
    finally:
        shutil.rmtree(profile_dir, ignore_errors=True)

    if result.returncode != 0:
        raise RenderError(
            f"Chromium PDF render failed with exit code {result.returncode}: {result.stderr}"
        )
    if not output_path.exists():
        raise RenderError("Chromium finished but did not create the PDF output.")
    return {
        "method": "chromium-cli",
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def render_pdf(
    html_path: str | Path,
    output_path: str | Path,
    *,
    timeout_seconds: int = 60,
) -> dict[str, Any]:
    html_path = Path(html_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    errors: list[str] = []
    if os.environ.get("MBPDF_DISABLE_PLAYWRIGHT") != "1":
        try:
            result = render_with_playwright(html_path, output_path, timeout_seconds * 1000)
            result["fallback_errors"] = []
            return result
        except Exception as exc:
            errors.append(str(exc))

    if os.environ.get("MBPDF_DISABLE_NODE_PLAYWRIGHT") != "1":
        try:
            result = render_with_node_playwright(html_path, output_path, timeout_seconds)
            result["fallback_errors"] = errors
            return result
        except Exception as exc:
            errors.append(str(exc))

    try:
        result = render_with_chromium_cli(html_path, output_path, timeout_seconds)
        result["fallback_errors"] = errors
        return result
    except Exception as exc:
        if errors:
            previous = "\n".join(f"- {error}" for error in errors)
            raise RenderError(f"{exc}\nPrevious renderer errors:\n{previous}") from exc
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description="Render HTML to PDF.")
    parser.add_argument("--input", required=True, help="Input HTML file")
    parser.add_argument("--output", required=True, help="Output PDF file")
    parser.add_argument("--timeout", type=int, default=60, help="Render timeout in seconds")
    parser.add_argument("--json", action="store_true", help="Print JSON render metadata")
    args = parser.parse_args()

    result = render_pdf(args.input, args.output, timeout_seconds=args.timeout)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"{result['method']} -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
