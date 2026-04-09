"""Parsing Markdown via markdown-it-py (Story 2.2)."""

import logging
from pathlib import Path

from markdown_it import MarkdownIt
from markdown_it.token import Token

from bookforge.errors import InputError

logger = logging.getLogger("bookforge.parser")


def parse_markdown_file(path: Path) -> list[Token]:
    """Parse un fichier Markdown et retourne les tokens markdown-it-py.

    Args:
        path: Chemin absolu vers le fichier .md.

    Returns:
        Liste de tokens markdown-it-py.

    Raises:
        InputError: Si le fichier est introuvable.
    """
    if not path.exists():
        raise InputError(f"Fichier Markdown introuvable : {path}")

    text = path.read_text(encoding="utf-8")
    md = MarkdownIt("commonmark").enable("table")
    # Enregistrer le plugin de balises semantiques (Story 4.3)
    from bookforge.parser.semantic import semantic_plugin

    semantic_plugin(md)
    logger.debug("Parsing markdown file: %s", path)
    return md.parse(text)
