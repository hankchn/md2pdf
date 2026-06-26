#!/usr/bin/env python3
"""Parse Markdown into a structured document model for print layout."""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import re
from pathlib import Path
from typing import Any


HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
UL_RE = re.compile(r"^\s*[-*+]\s+(.+)$")
OL_RE = re.compile(r"^\s*\d+[.)]\s+(.+)$")
IMAGE_RE = re.compile(r"^!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"([^\"]+)\")?\)\s*$")
CALLOUT_RE = re.compile(r"^\[!(NOTE|IMPORTANT|WARNING|TIP|INFO)\]\s*(.*)$", re.I)


PRODUCT_KEYWORDS = [
    "prd",
    "product",
    "requirement",
    "需求",
    "产品",
    "用户故事",
    "验收",
    "里程碑",
    "交互",
]
RESEARCH_KEYWORDS = [
    "research",
    "brief",
    "analysis",
    "insight",
    "market",
    "调研",
    "研究",
    "分析",
    "洞察",
    "竞品",
]
KNOWLEDGE_KEYWORDS = [
    "note",
    "knowledge",
    "wiki",
    "memo",
    "笔记",
    "知识",
    "备忘",
    "复盘",
]


def split_front_matter(text: str) -> tuple[dict[str, str], str]:
    """Extract a small YAML-like front matter block without requiring PyYAML."""
    text = text.lstrip("\ufeff")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text

    end_index = None
    for index in range(1, min(len(lines), 80)):
        if lines[index].strip() in {"---", "..."}:
            end_index = index
            break
    if end_index is None:
        return {}, text

    meta: dict[str, str] = {}
    for line in lines[1:end_index]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip().lower()
        value = value.strip().strip("\"'")
        if key:
            meta[key] = value
    return meta, "\n".join(lines[end_index + 1 :])


def strip_markdown(text: str) -> str:
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[*_>#~]+", "", text)
    return re.sub(r"\s+", " ", text).strip()


def is_table_separator(line: str) -> bool:
    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    if not cells:
        return False
    return all(re.fullmatch(r":?-{3,}:?", cell or "") for cell in cells)


def split_table_row(line: str) -> list[str]:
    raw = line.strip().strip("|")
    return [cell.strip() for cell in raw.split("|")]


def table_alignments(separator: str) -> list[str]:
    alignments = []
    for cell in split_table_row(separator):
        left = cell.startswith(":")
        right = cell.endswith(":")
        if left and right:
            alignments.append("center")
        elif right:
            alignments.append("right")
        else:
            alignments.append("left")
    return alignments


def is_table_start(lines: list[str], index: int) -> bool:
    if index + 1 >= len(lines):
        return False
    return "|" in lines[index] and is_table_separator(lines[index + 1])


def is_fence(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("```") or stripped.startswith("~~~")


def is_block_start(lines: list[str], index: int) -> bool:
    line = lines[index]
    stripped = line.strip()
    return (
        not stripped
        or is_fence(line)
        or bool(HEADING_RE.match(line))
        or stripped.startswith(">")
        or bool(UL_RE.match(line))
        or bool(OL_RE.match(line))
        or bool(IMAGE_RE.match(stripped))
        or re.fullmatch(r"[-*_]{3,}", stripped) is not None
        or is_table_start(lines, index)
    )


def parse_table(lines: list[str], index: int) -> tuple[dict[str, Any], int]:
    header = split_table_row(lines[index])
    alignments = table_alignments(lines[index + 1])
    rows: list[list[str]] = []
    index += 2
    while index < len(lines) and "|" in lines[index].strip() and lines[index].strip():
        rows.append(split_table_row(lines[index]))
        index += 1
    return {
        "type": "table",
        "header": header,
        "alignments": alignments,
        "rows": rows,
    }, index


def parse_quote_or_callout(lines: list[str], index: int) -> tuple[dict[str, Any], int]:
    quote_lines: list[str] = []
    while index < len(lines):
        stripped = lines[index].lstrip()
        if not stripped.startswith(">"):
            break
        content = stripped[1:]
        if content.startswith(" "):
            content = content[1:]
        quote_lines.append(content.rstrip())
        index += 1

    while quote_lines and not quote_lines[0].strip():
        quote_lines.pop(0)
    marker = CALLOUT_RE.match(quote_lines[0].strip()) if quote_lines else None
    if marker:
        callout_type = marker.group(1).upper()
        title = marker.group(2).strip()
        body_lines = quote_lines[1:]
        return {
            "type": "callout",
            "callout_type": "NOTE" if callout_type == "INFO" else callout_type,
            "title": title,
            "lines": body_lines,
        }, index
    return {"type": "quote", "lines": quote_lines}, index


def parse_markdown_blocks(text: str) -> list[dict[str, Any]]:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    blocks: list[dict[str, Any]] = []
    index = 0

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()

        if not stripped:
            index += 1
            continue

        if is_fence(line):
            fence = stripped[:3]
            language = stripped[3:].strip()
            code_lines: list[str] = []
            index += 1
            while index < len(lines) and not lines[index].strip().startswith(fence):
                code_lines.append(lines[index])
                index += 1
            if index < len(lines):
                index += 1
            blocks.append({"type": "code", "language": language, "text": "\n".join(code_lines)})
            continue

        heading = HEADING_RE.match(line)
        if heading:
            blocks.append(
                {
                    "type": "heading",
                    "level": len(heading.group(1)),
                    "text": strip_markdown(heading.group(2)),
                }
            )
            index += 1
            continue

        if is_table_start(lines, index):
            block, index = parse_table(lines, index)
            blocks.append(block)
            continue

        if stripped.startswith(">"):
            block, index = parse_quote_or_callout(lines, index)
            blocks.append(block)
            continue

        if UL_RE.match(line):
            items = []
            while index < len(lines) and UL_RE.match(lines[index]):
                items.append(UL_RE.match(lines[index]).group(1).strip())  # type: ignore[union-attr]
                index += 1
            blocks.append({"type": "list", "ordered": False, "items": items})
            continue

        if OL_RE.match(line):
            items = []
            while index < len(lines) and OL_RE.match(lines[index]):
                items.append(OL_RE.match(lines[index]).group(1).strip())  # type: ignore[union-attr]
                index += 1
            blocks.append({"type": "list", "ordered": True, "items": items})
            continue

        image = IMAGE_RE.match(stripped)
        if image:
            blocks.append(
                {
                    "type": "image",
                    "alt": image.group(1).strip(),
                    "src": image.group(2).strip(),
                    "title": (image.group(3) or "").strip(),
                }
            )
            index += 1
            continue

        if re.fullmatch(r"[-*_]{3,}", stripped):
            blocks.append({"type": "divider"})
            index += 1
            continue

        paragraph_lines = [stripped]
        index += 1
        while index < len(lines) and not is_block_start(lines, index):
            paragraph_lines.append(lines[index].strip())
            index += 1
        blocks.append({"type": "paragraph", "text": " ".join(paragraph_lines).strip()})

    return blocks


def slugify(text: str) -> str:
    base = re.sub(r"[^\w\u4e00-\u9fff]+", "-", text.lower(), flags=re.UNICODE).strip("-")
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:6]
    if not base:
        base = "section"
    return f"{base[:48].strip('-')}-{digest}"


def classify_document(text: str, headings: list[str]) -> str:
    haystack = f"{text[:3000]} {' '.join(headings)}".lower()
    scores = {
        "product-doc": sum(1 for key in PRODUCT_KEYWORDS if key.lower() in haystack),
        "research-brief": sum(1 for key in RESEARCH_KEYWORDS if key.lower() in haystack),
        "knowledge-note": sum(1 for key in KNOWLEDGE_KEYWORDS if key.lower() in haystack),
    }
    winner, score = max(scores.items(), key=lambda item: item[1])
    return winner if score > 0 else "elegant-report"


def normalize_document(
    blocks: list[dict[str, Any]],
    *,
    raw_text: str,
    metadata: dict[str, str],
    source_path: str | None = None,
    title_override: str | None = None,
    author: str | None = None,
    date: str | None = None,
) -> dict[str, Any]:
    body = [dict(block) for block in blocks]
    source = Path(source_path) if source_path else None

    if title_override:
        title = title_override
    elif metadata.get("title"):
        title = metadata["title"]
    elif body and body[0]["type"] == "heading":
        title = body[0]["text"]
        if body[0].get("level") == 1:
            body = body[1:]
    elif source:
        title = source.stem.replace("-", " ").replace("_", " ").strip().title()
    else:
        title = "Untitled Document"

    if body and body[0].get("type") == "heading" and body[0].get("level") == 1:
        body = body[1:]

    author_value = author if author is not None else metadata.get("author", "")
    date_value = date if date is not None else metadata.get("date", _dt.date.today().isoformat())

    heading_levels = [block["level"] for block in body if block.get("type") == "heading"]
    shift = min(heading_levels) - 1 if heading_levels and min(heading_levels) > 1 else 0
    used_ids: set[str] = set()
    headings: list[dict[str, Any]] = []

    for block in body:
        if block.get("type") != "heading":
            continue
        block["level"] = max(1, min(3, int(block["level"]) - shift))
        base_id = slugify(block["text"])
        anchor = base_id
        suffix = 2
        while anchor in used_ids:
            anchor = f"{base_id}-{suffix}"
            suffix += 1
        used_ids.add(anchor)
        block["id"] = anchor
        headings.append({"id": anchor, "level": block["level"], "text": block["text"]})

    doc_type = classify_document(raw_text, [heading["text"] for heading in headings] + [title])
    return {
        "metadata": {
            "title": title,
            "author": author_value,
            "date": date_value,
            "source": str(source) if source else "",
        },
        "document_type": doc_type,
        "template_suggestion": doc_type,
        "blocks": body,
        "headings": headings,
        "stats": {
            "block_count": len(body),
            "heading_count": len(headings),
            "word_count": len(strip_markdown(raw_text).split()),
        },
    }


def parse_markdown(
    text: str,
    *,
    source_path: str | None = None,
    title: str | None = None,
    author: str | None = None,
    date: str | None = None,
) -> dict[str, Any]:
    metadata, body_text = split_front_matter(text)
    blocks = parse_markdown_blocks(body_text)
    return normalize_document(
        blocks,
        raw_text=body_text,
        metadata=metadata,
        source_path=source_path,
        title_override=title,
        author=author,
        date=date,
    )


def parse_markdown_file(
    input_path: str | Path,
    *,
    title: str | None = None,
    author: str | None = None,
    date: str | None = None,
) -> dict[str, Any]:
    path = Path(input_path)
    text = path.read_text(encoding="utf-8")
    return parse_markdown(text, source_path=str(path), title=title, author=author, date=date)


def main() -> int:
    parser = argparse.ArgumentParser(description="Parse Markdown into structured JSON.")
    parser.add_argument("--input", required=True, help="Input Markdown file")
    parser.add_argument("--title", help="Override document title")
    parser.add_argument("--author", help="Override document author")
    parser.add_argument("--date", help="Override document date")
    parser.add_argument("--output", help="Optional JSON output path")
    args = parser.parse_args()

    document = parse_markdown_file(args.input, title=args.title, author=args.author, date=args.date)
    payload = json.dumps(document, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
