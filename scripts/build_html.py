#!/usr/bin/env python3
"""Build print-ready HTML from the structured Markdown document model."""

from __future__ import annotations

import argparse
import datetime as _dt
import html
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from parse_md import parse_markdown_file


CALLOUT_LABELS = {
    "NOTE": "提示",
    "IMPORTANT": "重点",
    "WARNING": "风险",
    "TIP": "建议",
}


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def is_external_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https", "data", "file", "mailto"}


def resolve_asset_url(src: str, source_dir: Path | None) -> str:
    if is_external_url(src) or src.startswith("#"):
        return src
    if not source_dir:
        return src
    candidate = (source_dir / src).resolve()
    if candidate.exists():
        return candidate.as_uri()
    return src


def render_inline(text: str, source_dir: Path | None = None) -> str:
    tokens: dict[str, str] = {}

    def stash(value: str) -> str:
        key = f"@@HTMLTOKEN{len(tokens)}@@"
        tokens[key] = value
        return key

    def code_repl(match: re.Match[str]) -> str:
        return stash(f"<code>{html.escape(match.group(1))}</code>")

    def image_repl(match: re.Match[str]) -> str:
        alt = html.escape(match.group(1), quote=True)
        src = html.escape(resolve_asset_url(match.group(2), source_dir), quote=True)
        return stash(f'<img src="{src}" alt="{alt}" class="inline-image" />')

    def link_repl(match: re.Match[str]) -> str:
        label = html.escape(match.group(1))
        href = html.escape(resolve_asset_url(match.group(2), source_dir), quote=True)
        return stash(f'<a href="{href}">{label}</a>')

    def strong_repl(match: re.Match[str]) -> str:
        return stash(f"<strong>{html.escape(match.group(1))}</strong>")

    def em_repl(match: re.Match[str]) -> str:
        return stash(f"<em>{html.escape(match.group(1))}</em>")

    working = text
    working = re.sub(r"`([^`]+)`", code_repl, working)
    working = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]+\")?\)", image_repl, working)
    working = re.sub(r"\[([^\]]+)\]\(([^)\s]+)(?:\s+\"[^\"]+\")?\)", link_repl, working)
    working = re.sub(r"\*\*([^*]+)\*\*", strong_repl, working)
    working = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", em_repl, working)

    escaped = html.escape(working)
    for key, value in tokens.items():
        escaped = escaped.replace(key, value)
    return escaped


def render_line_groups(lines: list[str], source_dir: Path | None) -> str:
    groups: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if line.strip():
            current.append(line.strip())
        elif current:
            groups.append(current)
            current = []
    if current:
        groups.append(current)
    return "\n".join(
        f"<p>{render_inline(' '.join(group), source_dir)}</p>" for group in groups
    )


def render_table(block: dict[str, Any], source_dir: Path | None) -> str:
    alignments = block.get("alignments") or []

    def cell_style(index: int) -> str:
        if index < len(alignments) and alignments[index] in {"left", "center", "right"}:
            return f' style="text-align: {alignments[index]}"'
        return ""

    header = "".join(
        f"<th{cell_style(index)}>{render_inline(value, source_dir)}</th>"
        for index, value in enumerate(block.get("header", []))
    )
    rows = []
    for row in block.get("rows", []):
        rows.append(
            "<tr>"
            + "".join(
                f"<td{cell_style(index)}>{render_inline(value, source_dir)}</td>"
                for index, value in enumerate(row)
            )
            + "</tr>"
        )
    return (
        '<div class="table-wrap"><table>'
        f"<thead><tr>{header}</tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table></div>"
    )


def clean_diagram_line(line: str) -> str:
    line = normalize_arrow(line)
    line = re.sub(r"[┌┐└┘├┤┬┴┼─│┃┏┓┗┛┣┫┳┻╋━]+", " ", line)
    line = re.sub(r"^[\s>*•·●○+-]+", "", line)
    line = re.sub(r"[\s>*•·●○+-]+$", "", line)
    line = re.sub(r"\s+", " ", line)
    return line.strip()


def normalize_arrow(text: str) -> str:
    text = re.sub(r"--?\|[^|]+\|>", "→", text)
    text = re.sub(r"--[^-]+-->", "→", text)
    return re.sub(r"\s*(?:-{1,2}>|=+>|→|⇒|➜|⟶)\s*", " → ", text)


def card(title: str, body: str = "") -> str:
    body_html = f"<span>{html.escape(body)}</span>" if body else ""
    return f'<div class="diagram-card"><strong>{html.escape(title)}</strong>{body_html}</div>'


def render_formula(text: str) -> str:
    formula = "<br />".join(html.escape(line.strip()) for line in text.splitlines() if line.strip())
    return f'<div class="formula-card">{formula}</div>'


def strip_mermaid_node_markup(value: str) -> str:
    value = value.strip().strip(";")
    match = re.fullmatch(r"[A-Za-z0-9_-]*[\[\(\{]\"?([^\"\]\)\}]+)\"?[\]\)\}]", value)
    if match:
        return match.group(1).strip()
    return value.strip("\"' ")


def split_card_text(line: str) -> tuple[str, str]:
    cleaned = strip_mermaid_node_markup(clean_diagram_line(line))
    cleaned = re.sub(r"^[\d一二三四五六七八九十]+[.)、．]\s*", "", cleaned)
    bracket_match = re.fullmatch(r"[【\[](.+?)[】\]]", cleaned)
    if bracket_match:
        cleaned = bracket_match.group(1).strip()

    layer_match = re.match(r"^(.{1,24}?层|layer\s*\d*)[（(](.+?)[）)]\s*(.*)$", cleaned, re.I)
    if layer_match:
        title = layer_match.group(1).strip()
        body = " ".join(part.strip() for part in layer_match.groups()[1:] if part.strip())
        return title, body

    for separator in ("：", ":", " - ", " | ", "｜"):
        if separator in cleaned:
            head, body = cleaned.split(separator, 1)
            if head.strip() and body.strip():
                return head.strip(), body.strip()
    return cleaned, ""


def dedupe_adjacent_items(items: list[tuple[str, str]]) -> list[tuple[str, str]]:
    deduped: list[tuple[str, str]] = []
    for title, body in items:
        title = title.strip()
        body = body.strip()
        if not title or title == "→":
            continue
        if deduped and deduped[-1][0] == title:
            previous_title, previous_body = deduped[-1]
            deduped[-1] = (previous_title, previous_body or body)
            continue
        deduped.append((title, body))
    return deduped


def extract_diagram_title(lines: list[str]) -> tuple[str | None, list[str]]:
    if not lines:
        return None, lines
    first = clean_diagram_line(lines[0])
    for pattern in (
        r"^[【\[](.+?)[】\]]$",
        r"^(?:title|diagram|chart|figure|图|图表)\s*[:：]\s*(.+)$",
    ):
        match = re.match(pattern, first, re.I)
        if match:
            return match.group(1).strip(), lines[1:]
    return None, lines


def extract_flow_items(lines: list[str]) -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    for line in lines:
        normalized = clean_diagram_line(line)
        if "→" not in normalized:
            continue
        segments = [segment.strip() for segment in normalized.split("→") if segment.strip()]
        if len(segments) < 2:
            continue
        items.extend(split_card_text(segment) for segment in segments)
    return dedupe_adjacent_items(items)


def extract_card_items(lines: list[str]) -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    for line in lines:
        cleaned = clean_diagram_line(line)
        if not cleaned or cleaned == "→":
            continue
        if re.fullmatch(r"[+|\-=_ ]+", cleaned):
            continue
        if "→" in cleaned:
            items.extend(split_card_text(segment) for segment in cleaned.split("→") if segment.strip())
            continue
        items.append(split_card_text(cleaned))
    return dedupe_adjacent_items(items)


def render_flow_diagram(title: str, items: list[tuple[str, str]]) -> str:
    pieces: list[str] = []
    for index, (item_title, item_body) in enumerate(items):
        if index:
            pieces.append('<div class="diagram-arrow">→</div>')
        pieces.append(card(item_title, item_body))
    return (
        '<figure class="diagram-block">'
        f'<div class="diagram-title">{html.escape(title)}</div>'
        f'<div class="diagram-flow">{"".join(pieces)}</div>'
        "</figure>"
    )


def render_grid_diagram(title: str, items: list[tuple[str, str]]) -> str:
    columns = "cols-3" if len(items) >= 6 else "cols-2"
    cards = "".join(card(item_title, item_body) for item_title, item_body in items[:10])
    return (
        '<figure class="diagram-block">'
        f'<div class="diagram-title">{html.escape(title)}</div>'
        f'<div class="diagram-grid {columns}">{cards}</div>'
        "</figure>"
    )


def render_stack_diagram(title: str, items: list[tuple[str, str]]) -> str:
    cards = "".join(card(item_title, item_body) for item_title, item_body in items[:10])
    return (
        '<figure class="diagram-block">'
        f'<div class="diagram-title">{html.escape(title)}</div>'
        f'<div class="diagram-stack">{cards}</div>'
        "</figure>"
    )


def render_matrix_diagram(title: str, items: list[tuple[str, str]]) -> str:
    cards = "".join(card(item_title, item_body) for item_title, item_body in items[:4])
    return (
        '<figure class="diagram-block">'
        f'<div class="diagram-title">{html.escape(title)}</div>'
        f'<div class="quadrant">{cards}</div>'
        "</figure>"
    )


def looks_like_layer_stack(text: str, items: list[tuple[str, str]]) -> bool:
    if any(token in text for token in ("↑", "↓", "↗", "↘")):
        return True
    return any("层" in title or title.lower().startswith("layer") for title, _ in items)


def looks_like_matrix(items: list[tuple[str, str]]) -> bool:
    if len(items) != 4:
        return False
    markers = ("高", "低", "high", "low", "impact", "effort", "risk", "value", "优先级", "可行性")
    payload = " ".join(f"{title} {body}" for title, body in items).lower()
    marker_count = sum(1 for marker in markers if marker in payload)
    return marker_count >= 2 or sum(1 for _, body in items if "/" in body) >= 2


def render_generic_diagram(text: str, title: str | None = None) -> str:
    raw_lines = [line for line in text.splitlines() if line.strip()]
    extracted_title, body_lines = extract_diagram_title(raw_lines)
    title = title or extracted_title

    flow_items = extract_flow_items(body_lines)
    if 2 <= len(flow_items) <= 4:
        return render_flow_diagram(title or "流程图", flow_items)

    items = extract_card_items(body_lines)
    if not items:
        return (
            '<figure class="diagram-block">'
            f'<div class="diagram-title">{html.escape(title or "结构图")}</div>'
            f'<pre class="diagram-raw">{html.escape(text)}</pre>'
            "</figure>"
        )
    if looks_like_layer_stack(text, items):
        return render_stack_diagram(title or "分层图", items)
    if looks_like_matrix(items):
        return render_matrix_diagram(title or "矩阵图", items)
    if len(flow_items) > 4:
        return render_grid_diagram(title or "流程图", flow_items)
    return render_grid_diagram(title or "结构图", items)


def looks_like_visual_diagram(text: str) -> bool:
    if any(token in text for token in ["┌", "└", "│", "┃", "→", "=>", "->", "-->", "↑", "↓", "↗", "↘", "【"]):
        return True
    return bool(re.search(r"^\s*(?:graph|flowchart|sequenceDiagram|classDiagram|stateDiagram)", text, re.I | re.M))


def looks_like_formula(text: str) -> bool:
    if len(text.splitlines()) > 3 or "→" in normalize_arrow(text):
        return False
    return bool(re.fullmatch(r"[\w\s\u4e00-\u9fff+\-*/().（）]+[=＝].+", text.strip()))


def render_visual_code(block: dict[str, Any]) -> str | None:
    language = (block.get("language") or "").strip().lower()
    text = block.get("text", "")
    stripped = text.strip()
    diagram_languages = {"text", "diagram", "mermaid", "flowchart"}
    if language and language not in diagram_languages:
        return None
    if looks_like_formula(stripped):
        return render_formula(stripped)
    if language in {"diagram", "mermaid", "flowchart"}:
        return render_generic_diagram(stripped)
    if not looks_like_visual_diagram(stripped):
        return None
    title_match = re.search(r"【([^】]+)】", stripped)
    title = title_match.group(1) if title_match else None
    return render_generic_diagram(stripped, title)


def render_block(block: dict[str, Any], source_dir: Path | None) -> str:
    block_type = block.get("type")
    if block_type == "heading":
        level = int(block.get("level", 2))
        anchor = html.escape(block.get("id", ""), quote=True)
        return f'<h{level} id="{anchor}">{render_inline(block.get("text", ""), source_dir)}</h{level}>'
    if block_type == "paragraph":
        return f'<p>{render_inline(block.get("text", ""), source_dir)}</p>'
    if block_type == "list":
        tag = "ol" if block.get("ordered") else "ul"
        items = "".join(
            f"<li>{render_inline(item, source_dir)}</li>" for item in block.get("items", [])
        )
        return f'<{tag} class="content-list">{items}</{tag}>'
    if block_type == "quote":
        return f'<blockquote>{render_line_groups(block.get("lines", []), source_dir)}</blockquote>'
    if block_type == "callout":
        callout_type = block.get("callout_type", "NOTE").upper()
        title = block.get("title") or CALLOUT_LABELS.get(callout_type, callout_type.title())
        body = render_line_groups(block.get("lines", []), source_dir)
        return (
            f'<aside class="callout callout-{html.escape(callout_type.lower())}">'
            f'<div class="callout-label">{html.escape(title)}</div>'
            f'<div class="callout-body">{body}</div>'
            "</aside>"
        )
    if block_type == "code":
        visual = render_visual_code(block)
        if visual:
            return visual
        language = block.get("language", "")
        label = f'<div class="code-label">{html.escape(language)}</div>' if language else ""
        return (
            '<figure class="code-block">'
            f"{label}<pre><code>{html.escape(block.get('text', ''))}</code></pre>"
            "</figure>"
        )
    if block_type == "table":
        return render_table(block, source_dir)
    if block_type == "image":
        src = html.escape(resolve_asset_url(block.get("src", ""), source_dir), quote=True)
        alt = html.escape(block.get("alt", ""), quote=True)
        caption = html.escape(block.get("title") or block.get("alt", ""))
        figcaption = f"<figcaption>{caption}</figcaption>" if caption else ""
        return f'<figure class="image-block"><img src="{src}" alt="{alt}" />{figcaption}</figure>'
    if block_type == "divider":
        return '<hr class="section-divider" />'
    return ""


def render_blocks(blocks: list[dict[str, Any]], source_dir: Path | None) -> str:
    return "\n".join(render_block(block, source_dir) for block in blocks)


def strip_toc_prefix(text: str) -> str:
    """Remove repeated outline numbering from TOC labels only."""
    patterns = [
        r"^\s*[一二三四五六七八九十百]+[、.．]\s*",
        r"^\s*\d+(?:\.\d+)*[.)、．]?\s*",
    ]
    cleaned = text
    for pattern in patterns:
        cleaned = re.sub(pattern, "", cleaned)
    return cleaned.strip() or text


def toc_marker(level: int, counters: list[int]) -> tuple[str, str]:
    if level == 1:
        counters[0] += 1
        counters[1] = 0
        counters[2] = 0
        return "CHAPTER", f"{counters[0]:02d}"
    if level == 2:
        if counters[0] == 0:
            counters[0] = 1
        counters[1] += 1
        counters[2] = 0
        return "SECTION", f"{counters[0]}.{counters[1]}"
    if counters[0] == 0:
        counters[0] = 1
    if counters[1] == 0:
        counters[1] = 1
    counters[2] += 1
    return "POINT", f"{counters[0]}.{counters[1]}.{counters[2]}"


def build_toc(headings: list[dict[str, Any]], enabled: bool) -> str:
    if not enabled or not headings:
        return ""
    items = []
    counters = [0, 0, 0]
    for heading in headings:
        level = int(heading.get("level", 1))
        if level > 3:
            continue
        anchor = html.escape(heading.get("id", ""), quote=True)
        text = html.escape(strip_toc_prefix(heading.get("text", "")))
        kind, number = toc_marker(level, counters)
        items.append(
            f'<li class="toc-item toc-level-{level}">'
            '<span class="toc-marker">'
            f'<span class="toc-kind">{kind}</span>'
            f'<span class="toc-number">{html.escape(number)}</span>'
            "</span>"
            f'<a href="#{anchor}"><span class="toc-title">{text}</span></a>'
            "</li>"
        )
    return (
        '<section class="toc-page">'
        '<div class="section-kicker">Contents</div>'
        "<h1>目录</h1>"
        f'<ol class="toc-list">{"".join(items)}</ol>'
        "</section>"
    )


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def load_template_assets(template_name: str) -> tuple[str, str, str]:
    root = skill_root() / "templates"
    template_dir = root / template_name
    if not template_dir.exists():
        raise FileNotFoundError(f"Template not found: {template_name}")

    template_html = read_text(template_dir / "template.html")
    if not template_html:
        raise FileNotFoundError(f"Missing template.html for template: {template_name}")

    style_css = "\n".join(
        [
            read_text(root / "shared" / "base.css"),
            read_text(template_dir / "style.css"),
        ]
    )
    print_css = "\n".join(
        [
            read_text(root / "shared" / "print-base.css"),
            read_text(template_dir / "print.css"),
        ]
    )
    return template_html, style_css, print_css


def template_label(template_name: str) -> str:
    return {
        "elegant-report": "Elegant Report",
        "product-doc": "Product Document",
        "research-brief": "Research Brief",
        "knowledge-note": "Knowledge Note",
    }.get(template_name, template_name.replace("-", " ").title())


def document_type_label(doc_type: str) -> str:
    return {
        "elegant-report": "Report",
        "product-doc": "Product Doc",
        "research-brief": "Research Brief",
        "knowledge-note": "Knowledge Note",
    }.get(doc_type, doc_type.replace("-", " ").title())


def contains_cjk(document: dict[str, Any]) -> bool:
    payload = json.dumps(document, ensure_ascii=False)
    return re.search(r"[\u4e00-\u9fff]", payload) is not None


def replace_tokens(template: str, context: dict[str, str]) -> str:
    rendered = template
    for key, value in context.items():
        rendered = rendered.replace("{{ " + key + " }}", value)
    return rendered


def build_html(
    document: dict[str, Any],
    *,
    template_name: str = "elegant-report",
    toc: bool = True,
    source_dir: Path | None = None,
) -> str:
    template_html, style_css, print_css = load_template_assets(template_name)
    metadata = document.get("metadata", {})
    title = metadata.get("title", "Untitled Document")
    author = metadata.get("author", "")
    date = metadata.get("date", "")
    doc_type = document.get("document_type", "elegant-report")

    cover_meta = []
    if author:
        cover_meta.append(f"<span>{html.escape(author)}</span>")
    if date:
        cover_meta.append(f"<span>{html.escape(date)}</span>")
    cover_meta.append(f"<span>{html.escape(document_type_label(doc_type))}</span>")

    context = {
        "lang": "zh-CN" if contains_cjk(document) else "en",
        "title": html.escape(title),
        "running_title": html.escape(title[:48]),
        "author_line": html.escape(author or ""),
        "date": html.escape(date),
        "document_type": html.escape(document_type_label(doc_type)),
        "template_name": html.escape(template_name),
        "template_label": html.escape(template_label(template_name)),
        "generated_at": html.escape(_dt.datetime.now().strftime("%Y-%m-%d %H:%M")),
        "cover_meta_html": '<div class="cover-meta">' + "".join(cover_meta) + "</div>",
        "toc_html": build_toc(document.get("headings", []), toc),
        "body_html": render_blocks(document.get("blocks", []), source_dir),
        "style_css": style_css,
        "print_css": print_css,
    }
    return replace_tokens(template_html, context)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build print-ready HTML from Markdown.")
    parser.add_argument("--input", required=True, help="Input Markdown file")
    parser.add_argument("--output", required=True, help="Output HTML file")
    parser.add_argument("--template", default="elegant-report", help="Template name")
    parser.add_argument("--title", help="Override document title")
    parser.add_argument("--author", help="Override author")
    parser.add_argument("--date", help="Override date")
    parser.add_argument("--toc", default="true", help="Generate table of contents: true/false")
    args = parser.parse_args()

    source_path = Path(args.input).resolve()
    document = parse_markdown_file(
        source_path,
        title=args.title,
        author=args.author,
        date=args.date,
    )
    html_text = build_html(
        document,
        template_name=args.template,
        toc=args.toc.lower() not in {"false", "0", "no"},
        source_dir=source_path.parent,
    )
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_text, encoding="utf-8")
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
