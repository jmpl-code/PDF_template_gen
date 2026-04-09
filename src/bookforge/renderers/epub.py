"""Renderer EPUB via Pandoc (Stories 3.1, 4.1)."""

from __future__ import annotations

import datetime
import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING

import matplotlib
import matplotlib.pyplot as plt
import yaml

from bookforge.ast_nodes import (
    ASTNode,
    BookNode,
    CalloutNode,
    ChapterSummaryNode,
    FrameworkNode,
    HeadingNode,
    ImageNode,
    ParagraphNode,
    TableNode,
)
from bookforge.config.schema import BookConfig
from bookforge.external import run_external

if TYPE_CHECKING:
    from bookforge.tokens.resolver import ResolvedTokenSet

matplotlib.use("Agg")

logger = logging.getLogger("bookforge.renderers.epub")

_SEMANTIC_CSS = """\
/* Semantic containers (Story 4.3) */
.framework {
  border: 2px solid #2563eb;
  background-color: #eff6ff;
  padding: 1em;
  margin: 1.5em 0;
  border-radius: 4px;
}
.framework::before {
  content: "Framework";
  display: block;
  font-weight: bold;
  margin-bottom: 0.5em;
  font-size: 0.9em;
}
.callout {
  border-left: 4px solid #f59e0b;
  background-color: #fffbeb;
  padding: 1em;
  margin: 1.5em 0;
}
.chapter-summary {
  border-top: 1px solid #6b7280;
  border-bottom: 1px solid #6b7280;
  background-color: #f9fafb;
  padding: 1em;
  margin: 1.5em 0;
  font-style: italic;
}
.chapter-summary::before {
  content: "Resume du chapitre";
  display: block;
  font-weight: bold;
  font-style: normal;
  margin-bottom: 0.5em;
  font-size: 0.9em;
}
"""

_KINDLE_CSS = """\
/* epub.css — style Kindle basique (Story 3.1) */
body {
  font-family: serif;
  line-height: 1.4;
}
h1 { font-size: 1.8em; margin-top: 2em; margin-bottom: 0.8em; }
h2 { font-size: 1.4em; margin-top: 1.5em; margin-bottom: 0.6em; }
h3 { font-size: 1.2em; margin-top: 1.2em; margin-bottom: 0.5em; }
h4 { font-size: 1.1em; margin-top: 1em; margin-bottom: 0.4em; }
p { text-indent: 1em; margin: 0.2em 0; }
img { max-width: 100%; height: auto; }
table { border-collapse: collapse; width: 100%; }
td, th { border: 1px solid #ccc; padding: 0.3em 0.5em; }
""" + _SEMANTIC_CSS

_MAX_TABLE_COLUMNS = 4


_SAFE_CSS_DIM_RE = re.compile(r"^[\d.]+(pt|mm|cm|in|em|rem|%)$")


def _safe_css_dim(value: str, fallback: str) -> str:
    """Valide une dimension CSS — retourne fallback si suspecte."""
    if _SAFE_CSS_DIM_RE.match(value):
        return value
    logger.warning("Token CSS suspect ignore : '%s' — fallback '%s'", value, fallback)
    return fallback


def _build_css_from_tokens(tokens: ResolvedTokenSet) -> str:
    """Genere le CSS Kindle a partir des design tokens resolus."""
    font_size = tokens.font_size if isinstance(tokens.font_size, (int, float)) else 11
    h1_ratio = round(tokens.heading_1_size / font_size, 2) if font_size else 1.8
    h2_ratio = round(tokens.heading_2_size / font_size, 2) if font_size else 1.4
    h3_ratio = round(tokens.heading_3_size / font_size, 2) if font_size else 1.2
    h4_ratio = round(tokens.heading_4_size / font_size, 2) if font_size else 1.1
    par_indent = _safe_css_dim(str(tokens.par_indent), "1em")
    return f"""\
/* epub.css — style Kindle dynamique (Story 4.1) */
body {{
  font-family: serif;
  font-size: {font_size}pt;
  line-height: {tokens.line_height};
}}
h1 {{ font-size: {h1_ratio}em; margin-top: 2em; margin-bottom: 0.8em; }}
h2 {{ font-size: {h2_ratio}em; margin-top: 1.5em; margin-bottom: 0.6em; }}
h3 {{ font-size: {h3_ratio}em; margin-top: 1.2em; margin-bottom: 0.5em; }}
h4 {{ font-size: {h4_ratio}em; margin-top: 1em; margin-bottom: 0.4em; }}
p {{ text-indent: {par_indent}; margin: 0.2em 0; }}
img {{ max-width: 100%; height: auto; }}
table {{ border-collapse: collapse; width: 100%; }}
td, th {{ border: 1px solid #ccc; padding: 0.3em 0.5em; }}
""" + _SEMANTIC_CSS


def _render_table_as_image(table: TableNode, output_path: Path) -> None:
    """Render a wide table as a PNG image via Matplotlib."""
    rows = [list(row) for row in table.rows]
    headers = list(table.headers)
    fig, ax = plt.subplots()
    ax.axis("off")
    ax.table(
        cellText=rows,
        colLabels=headers,
        cellLoc="center",
        loc="center",
    )
    fig.savefig(str(output_path), dpi=300, bbox_inches="tight", pad_inches=0.1)
    plt.close(fig)
    logger.debug("Table image generated: %s", output_path)


def _render_table_as_markdown(table: TableNode) -> str:
    """Render a table as a Markdown pipe table."""
    headers = list(table.headers)
    header_line = "| " + " | ".join(headers) + " |"
    separator = "| " + " | ".join("---" for _ in headers) + " |"
    lines = [header_line, separator]
    for row in table.rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines) + "\n\n"


def _render_node_to_markdown(
    node: ASTNode,
    build_dir: Path,
    table_counter: list[int],
) -> str:
    """Convert an AST node to Markdown for Pandoc."""
    if isinstance(node, HeadingNode):
        prefix = "#" * node.level + " "
        return f"{prefix}{node.text}\n\n"
    if isinstance(node, ParagraphNode):
        return f"{node.text}\n\n"
    if isinstance(node, ImageNode):
        src_str = str(node.src).replace("\\", "/")
        return f"![{node.alt}]({src_str})\n\n"
    if isinstance(node, FrameworkNode):
        return f'<div class="framework">\n\n{node.content}\n\n</div>\n\n'
    if isinstance(node, CalloutNode):
        return f'<div class="callout">\n\n{node.content}\n\n</div>\n\n'
    if isinstance(node, ChapterSummaryNode):
        return f'<div class="chapter-summary">\n\n{node.content}\n\n</div>\n\n'
    if isinstance(node, TableNode):
        if len(node.headers) == 0:
            logger.warning(
                "Empty table at %s:%d, skipping",
                node.source_file,
                node.line_number,
            )
            return ""
        if len(node.headers) > _MAX_TABLE_COLUMNS:
            table_counter[0] += 1
            img_path = build_dir / f"table_{table_counter[0]}.png"
            _render_table_as_image(node, img_path)
            img_str = str(img_path).replace("\\", "/")
            return f"![Table {table_counter[0]}]({img_str})\n\n"
        return _render_table_as_markdown(node)
    logger.warning(
        "Unknown node type %s at %s:%d",
        type(node).__name__,
        getattr(node, "source_file", "?"),
        getattr(node, "line_number", 0),
    )
    return ""


def _ast_to_markdown(
    book: BookNode,
    build_dir: Path,
) -> str:
    """Convert the full BookNode AST to Markdown for Pandoc."""
    table_counter = [0]
    parts: list[str] = []
    for chapter in book.chapters:
        parts.append(f"# {chapter.title}\n\n")
        for child in chapter.children:
            parts.append(
                _render_node_to_markdown(child, build_dir, table_counter),
            )
    return "".join(parts)


def _generate_metadata(config: BookConfig) -> dict[str, object]:
    """Build the Pandoc metadata dict from BookConfig."""
    year = datetime.date.today().year
    metadata: dict[str, object] = {
        "title": config.titre,
        "author": config.auteur,
        "lang": "fr",
        "rights": f"\u00a9 {year} {config.auteur}",
    }
    if config.description:
        metadata["description"] = config.description
    if config.mots_cles:
        metadata["keywords"] = config.mots_cles
    if config.isbn:
        metadata["identifier"] = config.isbn
    return metadata


def render_epub(
    book: BookNode,
    output_dir: Path,
    config: BookConfig | None = None,
    tokens: ResolvedTokenSet | None = None,
) -> Path:
    """Render a BookNode AST to an EPUB file via Pandoc.

    Args:
        book: The book AST root node.
        output_dir: Directory where the EPUB and build artifacts are written.
        config: Optional book configuration for metadata injection.
        tokens: Optional design tokens for dynamic CSS generation.

    Returns:
        Path to the generated .epub file.
    """
    build_dir = output_dir / "_epub_build"
    build_dir.mkdir(parents=True, exist_ok=True)

    # 1. AST → Markdown
    md_content = _ast_to_markdown(book, build_dir)
    md_path = build_dir / "content.md"
    md_path.write_text(md_content, encoding="utf-8")
    logger.debug("EPUB Markdown written: %s", md_path)

    # 2. CSS (dynamique si tokens fournis, sinon statique)
    css_content = _build_css_from_tokens(tokens) if tokens is not None else _KINDLE_CSS
    css_path = build_dir / "epub.css"
    css_path.write_text(css_content, encoding="utf-8")

    # 3. Metadata
    pandoc_args = [
        "pandoc",
        str(md_path),
        f"--css={css_path}",
        "--epub-chapter-level=1",
        "--toc",
        "--toc-depth=2",
    ]

    if config is not None:
        metadata = _generate_metadata(config)
        metadata_path = build_dir / "metadata.yaml"
        metadata_path.write_text(
            yaml.dump(metadata, allow_unicode=True, default_flow_style=False),
            encoding="utf-8",
        )
        pandoc_args.append(f"--metadata-file={metadata_path}")

    # 4. Output path
    epub_path = output_dir / "livre.epub"
    pandoc_args.extend(["-o", str(epub_path)])

    # 5. Call Pandoc
    run_external(pandoc_args, description="Generation EPUB via Pandoc")
    logger.debug("EPUB generated: %s", epub_path)
    return epub_path
