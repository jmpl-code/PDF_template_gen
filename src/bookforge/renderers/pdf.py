"""Renderer PDF via typst compile (Stories 2.3, 2.4, 2.5, 2.6, 4.1)."""

from __future__ import annotations

import datetime
import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING

from bookforge.ast_nodes import (
    ASTNode,
    BookNode,
    ChapterNode,
    HeadingNode,
    ImageNode,
    ParagraphNode,
    TableNode,
)
from bookforge.config.schema import BookConfig
from bookforge.errors import RenderError
from bookforge.external import run_external

if TYPE_CHECKING:
    from bookforge.tokens.resolver import ResolvedTokenSet

logger = logging.getLogger("bookforge.renderers.pdf")

# Caracteres speciaux Typst a echapper dans le texte
_TYPST_ESCAPE_MAP = str.maketrans(
    {
        "\\": "\\\\",
        "#": "\\#",
        "$": "\\$",
        "@": "\\@",
        "<": "\\<",
        ">": "\\>",
        "`": "\\`",
        "_": "\\_",
        "*": "\\*",
        "~": "\\~",
    }
)

# Template Typst de base inline (evite les problemes de resolution de chemin)
_BASE_TEMPLATE = """\
// Template Typst de base — BookForge (Story 2.3)
// Format livre 6x9 pouces standard KDP

// Configuration page
#set page(
  width: 6in,
  height: 9in,
  margin: (inside: 2cm, outside: 1.5cm, top: 2.5cm, bottom: 2cm),
)

// Typographie professionnelle (Bringhurst)
#set text(
  font: "New Computer Modern",
  size: 11pt,
  lang: "fr",
  region: "FR",
  hyphenate: true,
)

// Paragraphes
#set par(
  justify: true,
  leading: 1.35em,
  first-line-indent: 1em,
)

// Headings h1-h4
#show heading.where(level: 1): set text(size: 24pt, weight: "bold")
#show heading.where(level: 1): set block(above: 2em, below: 1.2em)

#show heading.where(level: 2): set text(size: 18pt, weight: "bold")
#show heading.where(level: 2): set block(above: 1.8em, below: 1em)

#show heading.where(level: 3): set text(size: 14pt, weight: "bold")
#show heading.where(level: 3): set block(above: 1.4em, below: 0.8em)

#show heading.where(level: 4): set text(size: 12pt, weight: "bold")
#show heading.where(level: 4): set block(above: 1.2em, below: 0.6em)

// --- BEGIN CONTENT ---
"""


_SAFE_DIMENSION_RE = re.compile(r"^[\d.]+(pt|mm|cm|in|em)$")
_SAFE_FONT_RE = re.compile(r'^[A-Za-z0-9 \-]+$')


def _safe_dim(value: str, fallback: str) -> str:
    """Valide une dimension token — retourne fallback si suspecte."""
    if _SAFE_DIMENSION_RE.match(value):
        return value
    logger.warning("Token dimension suspect ignore : '%s' — fallback '%s'", value, fallback)
    return fallback


def _safe_font(value: str, fallback: str) -> str:
    """Valide un nom de police — retourne fallback si suspect."""
    if _SAFE_FONT_RE.match(value):
        return value
    logger.warning("Token font suspect ignore : '%s' — fallback '%s'", value, fallback)
    return fallback


def _build_template_from_tokens(tokens: ResolvedTokenSet) -> str:
    """Genere le template Typst a partir des design tokens resolus."""
    pw = _safe_dim(str(tokens.page_width), "6in")
    ph = _safe_dim(str(tokens.page_height), "9in")
    mi = _safe_dim(str(tokens.margin_inner), "2cm")
    mo = _safe_dim(str(tokens.margin_outer), "1.5cm")
    mt = _safe_dim(str(tokens.margin_top), "2.5cm")
    mb = _safe_dim(str(tokens.margin_bottom), "2cm")
    ff = _safe_font(str(tokens.font_family), "New Computer Modern")
    pi = _safe_dim(str(tokens.par_indent), "1em")
    return f"""\
// Template Typst dynamique — BookForge (Story 4.1)
// Genere a partir des design tokens resolus

// Configuration page
#set page(
  width: {pw},
  height: {ph},
  margin: (inside: {mi}, outside: {mo},
           top: {mt}, bottom: {mb}),
)

// Typographie professionnelle
#set text(
  font: "{ff}",
  size: {tokens.font_size}pt,
  lang: "fr",
  region: "FR",
  hyphenate: true,
)

// Paragraphes
#set par(
  justify: true,
  leading: {tokens.line_height}em,
  first-line-indent: {pi},
)

// Headings h1-h4
#show heading.where(level: 1): set text(size: {tokens.heading_1_size}pt, weight: "bold")
#show heading.where(level: 1): set block(above: 2em, below: 1.2em)

#show heading.where(level: 2): set text(size: {tokens.heading_2_size}pt, weight: "bold")
#show heading.where(level: 2): set block(above: 1.8em, below: 1em)

#show heading.where(level: 3): set text(size: {tokens.heading_3_size}pt, weight: "bold")
#show heading.where(level: 3): set block(above: 1.4em, below: 0.8em)

#show heading.where(level: 4): set text(size: {tokens.heading_4_size}pt, weight: "bold")
#show heading.where(level: 4): set block(above: 1.2em, below: 0.6em)

// --- BEGIN CONTENT ---
"""


def escape_typst(text: str) -> str:
    """Echappe les caracteres speciaux Typst dans du texte brut."""
    return text.translate(_TYPST_ESCAPE_MAP)


def _render_node(node: ASTNode, typ_dir: Path) -> str:
    """Convertit un noeud AST en code Typst."""
    if isinstance(node, HeadingNode):
        prefix = "=" * node.level + " "
        return f"{prefix}{escape_typst(node.text)}\n\n"
    if isinstance(node, ParagraphNode):
        return f"{escape_typst(node.text)}\n\n"
    if isinstance(node, ImageNode):
        return _render_image(node, typ_dir)
    if isinstance(node, TableNode):
        return _render_table(node)
    logger.warning(
        "Unknown node type %s at %s:%d",
        type(node).__name__,
        getattr(node, "source_file", "?"),
        getattr(node, "line_number", 0),
    )
    return ""


def _render_image(image: ImageNode, typ_dir: Path) -> str:
    """Genere le code Typst pour une image avec protection anti-coupure."""
    try:
        rel_path = image.src.resolve().relative_to(typ_dir.resolve())
    except ValueError:
        raise RenderError(
            f"L'image '{image.src}' est hors du repertoire de sortie "
            f"'{typ_dir}' — deplacez-la ou utilisez un chemin accessible"
        )
    # Forward slashes pour Typst cross-platform
    src_str = str(rel_path).replace("\\", "/")
    caption_line = ""
    if image.alt:
        caption_line = f"\n    caption: [{escape_typst(image.alt)}],"
    return (
        "#block(breakable: false)[\n"
        "  #figure(\n"
        f'    image("{src_str}", width: 80%),{caption_line}\n'
        "  )\n"
        "]\n\n"
    )


def _render_table(table: TableNode) -> str:
    """Genere le code Typst pour un tableau."""
    col_count = len(table.headers)
    if col_count == 0:
        logger.warning("Empty table at %s:%d, skipping", table.source_file, table.line_number)
        return ""
    lines: list[str] = [f"#table(\n  columns: {col_count},\n"]
    header_cells = ", ".join(f"[{escape_typst(h)}]" for h in table.headers)
    lines.append(f"  {header_cells},\n")
    for row in table.rows:
        if not row:
            continue
        row_cells = ", ".join(f"[{escape_typst(cell)}]" for cell in row)
        lines.append(f"  {row_cells},\n")
    lines.append(")\n\n")
    return "".join(lines)


def _render_title_page(config: BookConfig) -> str:
    """Genere la page de titre Typst."""
    parts: list[str] = ["#align(center + horizon)[\n"]
    parts.append(f'  #text(size: 28pt, weight: "bold")[{escape_typst(config.titre)}]\n')
    if config.sous_titre:
        parts.append("  #v(1em)\n")
        parts.append(f"  #text(size: 18pt)[{escape_typst(config.sous_titre)}]\n")
    parts.append("  #v(4em)\n")
    parts.append(f"  #text(size: 16pt)[{escape_typst(config.auteur)}]\n")
    parts.append("]\n")
    return "".join(parts)


def _render_copyright_page(config: BookConfig) -> str:
    """Genere la page de copyright Typst."""
    year = datetime.date.today().year
    parts: list[str] = ["#align(bottom)[\n"]
    parts.append("  #set text(size: 9pt)\n")
    parts.append(f"  \\u{{00A9}} {year} {escape_typst(config.auteur)}. Tous droits reserves.\n")
    if config.isbn:
        parts.append("  #linebreak()\n")
        parts.append(f"  ISBN : {escape_typst(config.isbn)}\n")
    parts.append("]\n")
    return "".join(parts)


def _render_dedication_page(dedicace: str) -> str:
    """Genere la page de dedicace Typst."""
    return f"#align(center + horizon)[\n  #emph[{escape_typst(dedicace)}]\n]\n"


def _render_toc() -> str:
    """Genere la table des matieres Typst."""
    return "#heading(outlined: false, level: 1)[Table des matieres]\n#outline(indent: auto)\n"


def _render_front_matter(config: BookConfig) -> str:
    """Assemble les pages liminaires : titre, copyright, dedicace, TDM."""
    parts: list[str] = []
    # Desactiver la numerotation de page pour les liminaires
    parts.append("#set page(numbering: none)\n\n")
    # Page de titre
    parts.append(_render_title_page(config))
    parts.append("\n#pagebreak()\n\n")
    # Page de copyright
    parts.append(_render_copyright_page(config))
    parts.append("\n#pagebreak()\n\n")
    # Page de dedicace (optionnelle)
    if config.dedicace:
        parts.append(_render_dedication_page(config.dedicace))
        parts.append("\n#pagebreak()\n\n")
    # Table des matieres
    parts.append(_render_toc())
    parts.append("\n#pagebreak()\n\n")
    # Numerotation et headers sont actives par _render_running_headers()
    return "".join(parts)


def _render_chapter_title_page(chapter: ChapterNode) -> str:
    """Genere la page de garde d'un chapitre."""
    logger.debug("Generating chapter title page: %s", chapter.title)
    return (
        "#pagebreak(weak: true)\n"
        "#align(center + horizon)[\n"
        f'  #text(size: 28pt, weight: "bold")[{escape_typst(chapter.title)}]\n'
        "] <chapter-start>\n"
        "#pagebreak()\n\n"
    )


def _render_running_headers(config: BookConfig) -> str:
    """Active les en-tetes/pieds de page et la numerotation arabe."""
    book_title = escape_typst(config.titre)
    return (
        "// En-tetes et pieds de page (Story 2.5)\n"
        "#set page(\n"
        '  numbering: "1",\n'
        "  header: context {\n"
        "    let start-matches = query(<chapter-start>)\n"
        "    let current = counter(page).get()\n"
        "    let is-chapter-start = start-matches.any(m =>\n"
        "      counter(page).at(m.location()) == current\n"
        "    )\n"
        "    if not is-chapter-start {\n"
        "      let chapters = query(selector(heading.where(level: 1)).before(here()))\n"
        "      let chapter-title = if chapters.len() > 0 {\n"
        "        chapters.last().body\n"
        "      } else { [] }\n"
        f"      emph[{book_title}]\n"
        "      h(1fr)\n"
        "      emph[#chapter-title]\n"
        "    }\n"
        "  },\n"
        "  footer: context {\n"
        '    align(center)[#counter(page).display("1")]\n'
        "  },\n"
        ")\n"
        "#counter(page).update(1)\n\n"
    )


def _render_chapter(
    chapter: ChapterNode,
    is_first: bool,
    typ_dir: Path,
    *,
    has_chapter_pages: bool = False,
) -> str:
    """Genere le Typst pour un chapitre."""
    parts: list[str] = []
    if has_chapter_pages:
        parts.append(_render_chapter_title_page(chapter))
    elif not is_first:
        parts.append("#pagebreak()\n\n")
    for child in chapter.children:
        parts.append(_render_node(child, typ_dir))
    return "".join(parts)


def generate_typst(
    book: BookNode,
    output_path: Path,
    config: BookConfig | None = None,
    tokens: ResolvedTokenSet | None = None,
) -> Path:
    """Genere un fichier .typ depuis l'AST BookNode."""
    typ_dir = output_path.resolve().parent
    template = _build_template_from_tokens(tokens) if tokens is not None else _BASE_TEMPLATE
    content_parts: list[str] = [template, "\n"]
    has_chapter_pages = config is not None
    if config is not None:
        content_parts.append(_render_front_matter(config))
        content_parts.append(_render_running_headers(config))
    for i, chapter in enumerate(book.chapters):
        content_parts.append(
            _render_chapter(
                chapter,
                is_first=(i == 0),
                typ_dir=typ_dir,
                has_chapter_pages=has_chapter_pages,
            ),
        )
    output_path.write_text("".join(content_parts), encoding="utf-8")
    logger.debug("Generated .typ file: %s", output_path)
    return output_path


def compile_typst(typ_path: Path, pdf_path: Path) -> Path:
    """Compile un fichier .typ en PDF via Typst."""
    run_external(
        ["typst", "compile", str(typ_path), str(pdf_path)],
        description="Compilation Typst vers PDF",
    )
    return pdf_path


def render_pdf(
    book: BookNode,
    output_dir: Path,
    config: BookConfig | None = None,
    tokens: ResolvedTokenSet | None = None,
) -> Path:
    """Point d'entree : AST -> .typ -> PDF."""
    output_dir.mkdir(parents=True, exist_ok=True)
    typ_path = output_dir / "livre-interieur.typ"
    pdf_path = output_dir / "livre-interieur.pdf"
    generate_typst(book, typ_path, config=config, tokens=tokens)
    compile_typst(typ_path, pdf_path)
    logger.debug("PDF generated: %s", pdf_path)
    return pdf_path
