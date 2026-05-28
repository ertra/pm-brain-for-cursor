"""Atlassian Document Format -> plain text.

ADF is a JSON tree. This walker flattens it into readable plaintext so the text
can be embedded and FTS-indexed. The output preserves enough structure
(bullets, headings, links) to make quoted excerpts auditable without dragging
markup noise into the embedding space.
"""

from __future__ import annotations

import logging
from typing import Any

log = logging.getLogger(__name__)


def adf_to_text(node: Any, *, source_hint: str | None = None) -> str:
    """Convert an ADF document (or subtree) to plain text.

    `node` may be the top-level ``{"type": "doc", ...}`` object, a subtree,
    a list of nodes, or None/empty. Unknown node types are logged as
    warnings (once per type per call) and their children are still walked.
    """
    if not node:
        return ""
    ctx = _Context(source_hint=source_hint)
    return _walk(node, ctx).rstrip()


class _Context:
    def __init__(self, source_hint: str | None) -> None:
        self.source_hint = source_hint
        self.warned_types: set[str] = set()
        self.list_depth = 0
        self.ordered_stack: list[int] = []


def _walk(node: Any, ctx: _Context) -> str:
    if node is None:
        return ""
    if isinstance(node, list):
        return "".join(_walk(n, ctx) for n in node)
    if not isinstance(node, dict):
        return ""

    ntype = node.get("type")
    content = node.get("content") or []

    if ntype == "doc":
        return _walk(content, ctx)

    if ntype == "text":
        return _render_text(node)

    if ntype == "paragraph":
        return _walk(content, ctx) + "\n\n"

    if ntype == "heading":
        level = int(node.get("attrs", {}).get("level", 1))
        prefix = "#" * max(1, min(level, 6)) + " "
        return prefix + _walk(content, ctx).rstrip() + "\n\n"

    if ntype == "bulletList":
        ctx.list_depth += 1
        try:
            out = ""
            for item in content:
                out += _render_list_item(item, ctx, bullet="- ")
            return out + ("\n" if ctx.list_depth == 1 else "")
        finally:
            ctx.list_depth -= 1

    if ntype == "orderedList":
        ctx.list_depth += 1
        ctx.ordered_stack.append(int(node.get("attrs", {}).get("order", 1)))
        try:
            out = ""
            for item in content:
                idx = ctx.ordered_stack[-1]
                out += _render_list_item(item, ctx, bullet=f"{idx}. ")
                ctx.ordered_stack[-1] = idx + 1
            return out + ("\n" if ctx.list_depth == 1 else "")
        finally:
            ctx.ordered_stack.pop()
            ctx.list_depth -= 1

    if ntype == "listItem":
        return _walk(content, ctx)

    if ntype in ("codeBlock", "code_block"):
        inner = "".join(_render_text(c) for c in content if isinstance(c, dict) and c.get("type") == "text")
        return "```\n" + inner.rstrip() + "\n```\n\n"

    if ntype == "blockquote":
        inner = _walk(content, ctx).rstrip()
        quoted = "\n".join("> " + line for line in inner.splitlines())
        return quoted + "\n\n"

    if ntype in ("rule", "hardBreak", "hard_break"):
        return "\n"

    if ntype == "mention":
        text = node.get("attrs", {}).get("text") or node.get("attrs", {}).get("displayName") or ""
        return f"@{text.lstrip('@')}" if text else ""

    if ntype == "emoji":
        return node.get("attrs", {}).get("shortName", "") or node.get("attrs", {}).get("text", "")

    if ntype in ("inlineCard", "blockCard"):
        url = node.get("attrs", {}).get("url", "")
        return f" ({url}) " if url else ""

    if ntype == "table":
        return _render_table(content, ctx)

    if ntype in ("tableRow", "tableHeader", "tableCell"):
        return _walk(content, ctx)

    if ntype == "mediaSingle" or ntype == "mediaGroup" or ntype == "media":
        return ""

    if ntype and ntype not in ctx.warned_types:
        ctx.warned_types.add(ntype)
        where = f" in {ctx.source_hint}" if ctx.source_hint else ""
        log.warning("adf: unrecognized node type %r%s; walking children", ntype, where)

    return _walk(content, ctx)


def _render_list_item(item: Any, ctx: _Context, *, bullet: str) -> str:
    inner = _walk(item.get("content") or [] if isinstance(item, dict) else item, ctx).rstrip()
    if not inner:
        return ""
    indent = "  " * (ctx.list_depth - 1)
    lines = inner.splitlines()
    head = indent + bullet + lines[0]
    cont_indent = indent + " " * len(bullet)
    tail = "\n".join(cont_indent + ln for ln in lines[1:])
    return head + ("\n" + tail if tail else "") + "\n"


def _render_text(node: dict) -> str:
    text = node.get("text", "") or ""
    marks = node.get("marks") or []
    for mark in marks:
        if not isinstance(mark, dict):
            continue
        if mark.get("type") == "link":
            href = (mark.get("attrs") or {}).get("href")
            if href and href != text:
                text = f"{text} ({href})"
    return text


def _render_table(rows: Any, ctx: _Context) -> str:
    """Render tables as simple pipe-separated rows.

    Loses alignment fidelity but preserves cell contents for search.
    """
    if not isinstance(rows, list):
        return ""
    lines: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        cells = row.get("content") or []
        rendered_cells = []
        for cell in cells:
            if not isinstance(cell, dict):
                continue
            rendered = _walk(cell.get("content") or [], ctx).strip().replace("\n", " ")
            rendered_cells.append(rendered)
        if rendered_cells:
            lines.append(" | ".join(rendered_cells))
    return ("\n".join(lines) + "\n\n") if lines else ""
