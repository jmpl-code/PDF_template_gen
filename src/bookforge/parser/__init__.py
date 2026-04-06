"""Parsing Markdown vers AST."""

import logging
from pathlib import Path

from bookforge.ast_nodes import BookNode, ChapterNode
from bookforge.config import BookConfig
from bookforge.parser.markdown import parse_markdown_file
from bookforge.parser.transform import tokens_to_ast

logger = logging.getLogger("bookforge.parser")


def parse_book(config: BookConfig, book_dir: Path) -> BookNode:
    """Parse tous les chapitres d'un livre et retourne l'AST complet.

    Args:
        config: Configuration du livre (issue de book.yaml).
        book_dir: Repertoire parent du fichier book.yaml.

    Returns:
        BookNode racine de l'AST.
    """
    chapters: list[ChapterNode] = []

    for chap in config.chapitres:
        chap_path = (book_dir / chap.fichier).resolve()
        logger.debug("Parsing chapter: %s -> %s", chap.titre, chap_path)

        tokens = parse_markdown_file(chap_path)
        children = tokens_to_ast(tokens, chap_path)

        chapter = ChapterNode(
            title=chap.titre,
            children=tuple(children),
            source_file=chap_path,
            line_number=1,
        )
        chapters.append(chapter)

    logger.debug("Book AST built: %s (%d chapters)", config.titre, len(chapters))
    return BookNode(title=config.titre, chapters=tuple(chapters))


__all__ = ["parse_book", "parse_markdown_file", "tokens_to_ast"]
