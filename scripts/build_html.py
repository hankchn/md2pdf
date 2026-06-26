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
    line = re.sub(r"[┌┐└┘├┤┬┴┼─│↑↓↗↘]+", " ", line)
    line = re.sub(r"\s+", " ", line)
    return line.strip()


def card(title: str, body: str = "") -> str:
    body_html = f"<span>{html.escape(body)}</span>" if body else ""
    return f'<div class="diagram-card"><strong>{html.escape(title)}</strong>{body_html}</div>'


def render_formula(text: str) -> str:
    formula = "<br />".join(html.escape(line.strip()) for line in text.splitlines() if line.strip())
    return f'<div class="formula-card">{formula}</div>'


def render_cost_trap() -> str:
    return (
        '<figure class="diagram-block">'
        '<div class="diagram-title">版权模式结构性困境</div>'
        '<div class="diagram-flow">'
        + card("版权成本", "年年涨价，不可控")
        + '<div class="diagram-arrow">→</div>'
        + card("收入天花板", "用户付费意愿弱，增长受限")
        + '<div class="diagram-arrow">→</div>'
        + card("结果", "版权费高于收入，长期亏损")
        + "</div></figure>"
    )


def render_path_split() -> str:
    return (
        '<figure class="diagram-block">'
        '<div class="diagram-title">失去 NBA 后的两条路径</div>'
        + card("腾讯体育", "失去 NBA 后的平台战略选择")
        + '<div class="diagram-grid cols-2" style="margin-top:0.85rem">'
        + card("路径 A：防守型", "多版权拼盘 + 降本增效；结果是慢性萎缩")
        + card("路径 B：进攻型", "自有资产 + 平台化 + AI 赋能；结果是第二增长曲线")
        + "</div></figure>"
    )


def render_demand_layers(text: str) -> str:
    lines = text.splitlines()
    cards = []
    for index, line in enumerate(lines):
        match = re.search(r"([\u4e00-\u9fff]+层)（([^）]+)）", line)
        if not match:
            continue
        detail = ""
        for next_line in lines[index + 1 : index + 3]:
            if "→" in next_line:
                detail = clean_diagram_line(next_line).replace("→", "").strip()
                break
        cards.append(card(f"{match.group(1)}", f"{match.group(2)}：{detail}"))
    if not cards:
        return render_generic_diagram(text, "体育用户需求图")
    return (
        '<figure class="diagram-block">'
        '<div class="diagram-title">体育用户需求全景图</div>'
        f'<div class="diagram-stack">{"".join(cards)}</div>'
        "</figure>"
    )


def render_participation_platform() -> str:
    return (
        '<figure class="diagram-block">'
        '<div class="diagram-title">体育参与平台架构</div>'
        '<div class="diagram-grid cols-3">'
        + card("约赛系统", "LBS 匹配")
        + card("AI 教练", "视频分析")
        + card("业余联赛", "组织工具")
        + "</div>"
        '<div class="diagram-hub">用户运动数据中枢 · 可穿戴设备接入</div>'
        '<div class="diagram-grid cols-3">'
        + card("社区分享", "UGC 内容")
        + card("个人成长", "数据驱动")
        + card("电商消费", "精准推荐")
        + "</div></figure>"
    )


def render_industry_platform() -> str:
    customers = "中小赛事方、体育经纪公司、健身品牌、城市体育局、校园体育"
    return (
        '<figure class="diagram-block">'
        '<div class="diagram-title">腾讯体育产业服务平台</div>'
        '<div class="diagram-grid cols-3">'
        + card("直播云", "SaaS")
        + card("数据云", "Analytics")
        + card("营销云", "AdTech")
        + "</div>"
        '<div class="diagram-card" style="margin-top:0.85rem">'
        "<strong>目标客户</strong>"
        f"<span>{html.escape(customers)}</span>"
        "</div></figure>"
    )


def render_data_flywheel() -> str:
    return (
        '<figure class="diagram-block">'
        '<div class="diagram-title">AI + 体育数据飞轮</div>'
        '<div class="diagram-flow">'
        + card("用户行为数据")
        + '<div class="diagram-arrow">→</div>'
        + card("AI 精准推荐")
        + '<div class="diagram-arrow">→</div>'
        + card("体验提升")
        + '<div class="diagram-arrow">→</div>'
        + card("留存增长")
        + "</div>"
        '<div class="diagram-card" style="margin-top:0.85rem">'
        "<strong>飞轮闭环</strong><span>用户停留更久，产生更多数据，继续强化推荐和商业效率。</span>"
        "</div></figure>"
    )


def render_priority_matrix() -> str:
    return (
        '<figure class="diagram-block">'
        '<div class="diagram-title">战略优先级矩阵</div>'
        '<div class="quadrant">'
        + card("体育社区", "高影响力 / 中可行性")
        + card("AI + 体育", "高影响力 / 高可行性")
        + card("产业服务", "中影响力 / 中可行性")
        + card("自有 IP 内容", "中影响力 / 最快见效")
        + "</div></figure>"
    )


def render_generic_diagram(text: str, title: str = "结构图") -> str:
    meaningful = [
        clean_diagram_line(line)
        for line in text.splitlines()
        if clean_diagram_line(line) and len(clean_diagram_line(line)) > 1
    ]
    cards = []
    for line in meaningful[:8]:
        if "：" in line:
            head, body = line.split("：", 1)
            cards.append(card(head.strip(), body.strip()))
        else:
            cards.append(card(line.strip()))
    if not cards:
        cards = [f'<pre class="diagram-raw">{html.escape(text)}</pre>']
    return (
        '<figure class="diagram-block">'
        f'<div class="diagram-title">{html.escape(title)}</div>'
        f'<div class="diagram-grid cols-2">{"".join(cards)}</div>'
        "</figure>"
    )


def looks_like_visual_diagram(text: str) -> bool:
    return any(token in text for token in ["┌", "└", "│", "→", "↑", "↓", "↗", "↘", "【"])


def render_visual_code(block: dict[str, Any]) -> str | None:
    language = (block.get("language") or "").strip().lower()
    text = block.get("text", "")
    stripped = text.strip()
    if language and language not in {"text", "diagram", "mermaid"}:
        return None
    if re.fullmatch(r"价值\s*=.+", stripped):
        return render_formula(stripped)
    if not looks_like_visual_diagram(stripped):
        return None
    if "版权成本" in stripped and "永远亏损" in stripped:
        return render_cost_trap()
    if "路径A" in stripped and "路径B" in stripped:
        return render_path_split()
    if "体育用户需求全景图" in stripped:
        return render_demand_layers(stripped)
    if "体育参与平台架构" in stripped:
        return render_participation_platform()
    if "腾讯体育产业服务平台" in stripped:
        return render_industry_platform()
    if "用户行为数据" in stripped and "AI" in stripped:
        return render_data_flywheel()
    if "高影响力" in stripped and "高可行性" in stripped:
        return render_priority_matrix()
    title_match = re.search(r"【([^】]+)】", stripped)
    title = title_match.group(1) if title_match else "结构图"
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
