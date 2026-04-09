"""Plugin markdown-it-py pour balises semantiques (Story 4.3)."""

import logging
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from markdown_it import MarkdownIt
    from markdown_it.rules_block import StateBlock

logger = logging.getLogger("bookforge.parser.semantic")

KNOWN_SEMANTIC_TAGS = frozenset({"framework", "callout", "chapter-summary"})

_OPEN_RE = re.compile(r"^:{3,}\s*(\S+)\s*$")
_CLOSE_RE = re.compile(r"^:{3,}\s*$")


def _semantic_container_rule(
    state: "StateBlock", startLine: int, endLine: int, silent: bool  # noqa: N803
) -> bool:
    """Block rule that matches :::tag ... ::: containers."""
    pos = state.bMarks[startLine] + state.tShift[startLine]
    maximum = state.eMarks[startLine]

    line_text = state.src[pos:maximum]
    match = _OPEN_RE.match(line_text)
    if not match:
        return False

    tag = match.group(1)

    if tag not in KNOWN_SEMANTIC_TAGS:
        logger.warning(
            "Unknown semantic tag '%s' at line %d",
            tag,
            startLine + 1,
        )
        # Skip the block silently — find closing ::: and advance past it
        next_line = startLine + 1
        while next_line < endLine:
            line_pos = state.bMarks[next_line] + state.tShift[next_line]
            line_max = state.eMarks[next_line]
            if _CLOSE_RE.match(state.src[line_pos:line_max]):
                break
            next_line += 1
        state.line = next_line + 1 if next_line < endLine else endLine
        return True

    if silent:
        return True

    # Find the closing :::
    next_line = startLine + 1
    has_close = False
    while next_line < endLine:
        line_pos = state.bMarks[next_line] + state.tShift[next_line]
        line_max = state.eMarks[next_line]
        if _CLOSE_RE.match(state.src[line_pos:line_max]):
            has_close = True
            break
        next_line += 1

    if not has_close:
        return False

    # Extract content between open and close lines
    content_lines: list[str] = []
    for i in range(startLine + 1, next_line):
        line_pos = state.bMarks[i]
        line_max = state.eMarks[i]
        content_lines.append(state.src[line_pos:line_max])
    content = "\n".join(content_lines)

    # Emit open token
    token_open = state.push(f"semantic_{tag}_open", "div", 1)
    token_open.info = tag
    token_open.content = content
    token_open.map = [startLine, next_line + 1]
    token_open.block = True

    # Emit close token
    token_close = state.push(f"semantic_{tag}_close", "div", -1)
    token_close.info = tag

    state.line = next_line + 1
    return True


def semantic_plugin(md: "MarkdownIt") -> None:
    """Enregistre le plugin de balises semantiques sur une instance MarkdownIt."""
    md.block.ruler.before(
        "fence",
        "semantic_container",
        _semantic_container_rule,
    )
