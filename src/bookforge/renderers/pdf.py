"""Renderer PDF via typst compile (Stories 2.3, 2.4)."""

from __future__ import annotations

import datetime
import logging
from pathlib import Path

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
  leading: 1.3em,
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
    """Genere le code Typst pour une image avec chemin relatif au .typ."""
    try:
        rel_path = image.src.resolve().relative_to(typ_dir.resolve())
    except ValueError:
        raise RenderError(
            f"L'image '{image.src}' est hors du repertoire de sortie "
            f"'{typ_dir}' — deplacez-la ou utilisez un chemin accessible"
        )
    # Forward slashes pour Typst cross-platform
    src_str = str(rel_path).replace("\\", "/")
    return f'#align(center)[#image("{src_str}", width: 80%)]\n\n'


def _render_table(table: TableNode) -> str:
    """Genere le code Typst pour un tableau."""
    col_count = len(table.headers)
    if col_count == 0:
        logger.warning("Empty table at %s:%d, skipping", table.source_file, table.line_number)
        return ""
    lines: list[str] = [f"#table(\n  columns: {col_count},\n"]
    header_cells = ", ".join(
        f"[{escape_typst(h)}]" for h in table.headers
    )
    lines.append(f"  {header_cells},\n")
    for row in table.rows:
        if not row:
            continue
        row_cells = ", ".join(
            f"[{escape_typst(cell)}]" for cell in row
        )
        lines.append(f"  {row_cells},\n")
    lines.append(")\n\n")
    return "".join(lines)


def _render_title_page(config: BookConfig) -> str:
    """Genere la page de titre Typst."""
    parts: list[str] = ["#align(center + horizon)[\n"]
    parts.append(
        f'  #text(size: 28pt, weight: "bold")[{escape_typst(config.titre)}]\n'
    )
    if config.sous_titre:
        parts.append("  #v(1em)\n")
        parts.append(
            f"  #text(size: 18pt)[{escape_typst(config.sous_titre)}]\n"
        )
    parts.append("  #v(4em)\n")
    parts.append(f"  #text(size: 16pt)[{escape_typst(config.auteur)}]\n")
    parts.append("]\n")
    return "".join(parts)


def _render_copyright_page(config: BookConfig) -> str:
    """Genere la page de copyright Typst."""
    year = datetime.date.today().year
    parts: list[str] = ["#align(bottom)[\n"]
    parts.append("  #set text(size: 9pt)\n")
    parts.append(
        f"  \\u{{00A9}} {year} {escape_typst(config.auteur)}."
        " Tous droits reserves.\n"
    )
    if config.isbn:
        parts.append("  #linebreak()\n")
        parts.append(f"  ISBN : {escape_typst(config.isbn)}\n")
    parts.append("]\n")
    return "".join(parts)


def _render_dedication_page(dedicace: str) -> str:
    """Genere la page de dedicace Typst."""
    return (
        "#align(center + horizon)[\n"
        f"  #emph[{escape_typst(dedicace)}]\n"
        "]\n"
    )


def _render_toc() -> str:
    """Genere la table des matieres Typst."""
    return (
        '#heading(outlined: false, level: 1)[Table des matieres]\n'
        "#outline(indent: auto)\n"
    )


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
    # Reactiver la numerotation arabe et reset a page 1
    parts.append('#set page(numbering: "1")\n')
    parts.append("#counter(page).update(1)\n\n")
    return "".join(parts)


def _render_chapter(
    chapter: ChapterNode, is_first: bool, typ_dir: Path,
) -> str:
    """Genere le Typst pour un chapitre."""
    parts: list[str] = []
    if not is_first:
        parts.append("#pagebreak()\n\n")
    # Le titre chapitre est rendu par le HeadingNode level 1 dans children
    # Pas de doublon ici — seul le pagebreak est gere
    for child in chapter.children:
        parts.append(_render_node(child, typ_dir))
    return "".join(parts)


def generate_typst(
    book: BookNode,
    output_path: Path,
    config: BookConfig | None = None,
) -> Path:
    """Genere un fichier .typ depuis l'AST BookNode."""
    typ_dir = output_path.resolve().parent
    content_parts: list[str] = [_BASE_TEMPLATE, "\n"]
    if config is not None:
        content_parts.append(_render_front_matter(config))
    for i, chapter in enumerate(book.chapters):
        content_parts.append(
            _render_chapter(chapter, is_first=(i == 0), typ_dir=typ_dir),
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
) -> Path:
    """Point d'entree : AST -> .typ -> PDF."""
    output_dir.mkdir(parents=True, exist_ok=True)
    typ_path = output_dir / "livre-interieur.typ"
    pdf_path = output_dir / "livre-interieur.pdf"
    generate_typst(book, typ_path, config=config)
    compile_typst(typ_path, pdf_path)
    logger.debug("PDF generated: %s", pdf_path)
    return pdf_path
