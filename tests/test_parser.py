"""Tests pour le parser Markdown vers AST (Story 2.2)."""

import json
from pathlib import Path
from typing import Any

import pytest

from bookforge.ast_nodes import (
    BookNode,
    ChapterNode,
    HeadingNode,
    ImageNode,
    ParagraphNode,
    TableNode,
)
from bookforge.config import load_book_config
from bookforge.errors import InputError
from bookforge.parser import parse_book

FIXTURES = Path(__file__).parent / "fixtures"
BOOKS = FIXTURES / "books"
GOLDEN = FIXTURES / "golden"


def ast_to_dict(node: Any) -> dict[str, Any]:
    """Serialise un noeud AST en dict comparable (sans chemins absolus)."""
    if isinstance(node, BookNode):
        return {
            "type": "BookNode",
            "title": node.title,
            "chapters": [ast_to_dict(c) for c in node.chapters],
        }
    if isinstance(node, ChapterNode):
        return {
            "type": "ChapterNode",
            "title": node.title,
            "line_number": node.line_number,
            "children": [ast_to_dict(c) for c in node.children],
        }
    if isinstance(node, HeadingNode):
        return {
            "type": "HeadingNode",
            "level": node.level,
            "text": node.text,
            "line_number": node.line_number,
        }
    if isinstance(node, ParagraphNode):
        return {
            "type": "ParagraphNode",
            "text": node.text,
            "line_number": node.line_number,
        }
    if isinstance(node, ImageNode):
        return {
            "type": "ImageNode",
            "alt": node.alt,
            "line_number": node.line_number,
        }
    if isinstance(node, TableNode):
        return {
            "type": "TableNode",
            "headers": list(node.headers),
            "rows": [list(r) for r in node.rows],
            "line_number": node.line_number,
        }
    return {}


def _load_minimal_book() -> BookNode:
    """Charge et parse le livre minimal de fixture."""
    book_yaml = BOOKS / "minimal" / "book.yaml"
    config = load_book_config(book_yaml)
    return parse_book(config, book_yaml.parent)


class TestParserValid:
    """Tests avec du Markdown valide."""

    def test_parser_valid_markdown_returns_book_node(self) -> None:
        book = _load_minimal_book()
        assert isinstance(book, BookNode)
        assert book.title == "Mon Livre Business"
        assert len(book.chapters) == 1
        assert isinstance(book.chapters[0], ChapterNode)
        assert book.chapters[0].title == "Introduction"

    def test_parser_nodes_carry_source_file_and_line_number(self) -> None:
        book = _load_minimal_book()
        chapter = book.chapters[0]
        assert chapter.source_file.exists()
        assert chapter.line_number == 1
        for child in chapter.children:
            assert hasattr(child, "source_file")
            assert hasattr(child, "line_number")
            assert child.line_number > 0

    def test_parser_image_paths_resolved_absolute(self) -> None:
        book = _load_minimal_book()
        chapter = book.chapters[0]
        images = [c for c in chapter.children if isinstance(c, ImageNode)]
        assert len(images) == 1
        assert images[0].src.is_absolute()
        assert images[0].src.exists()
        assert images[0].alt == "Diagramme exemple"

    def test_parser_heading_levels_preserved(self) -> None:
        book = _load_minimal_book()
        chapter = book.chapters[0]
        headings = [c for c in chapter.children if isinstance(c, HeadingNode)]
        assert len(headings) == 2
        assert headings[0].level == 1
        assert headings[0].text == "Introduction"
        assert headings[1].level == 2
        assert headings[1].text == "Section 1"

    def test_parser_table_parsed_correctly(self) -> None:
        book = _load_minimal_book()
        chapter = book.chapters[0]
        tables = [c for c in chapter.children if isinstance(c, TableNode)]
        assert len(tables) == 1
        table = tables[0]
        assert table.headers == ("Colonne A", "Colonne B")
        assert len(table.rows) == 2
        assert table.rows[0] == ("valeur 1", "valeur 2")
        assert table.rows[1] == ("valeur 3", "valeur 4")

    def test_parser_golden_file_ast_stability(self) -> None:
        book = _load_minimal_book()
        actual = ast_to_dict(book)
        golden_path = GOLDEN / "minimal-ast.json"
        expected = json.loads(golden_path.read_text(encoding="utf-8"))
        assert actual == expected


class TestParserErrors:
    """Tests avec des erreurs."""

    def test_parser_missing_image_raises_input_error(self, tmp_path: Path) -> None:
        md_file = tmp_path / "chapter.md"
        md_file.write_text("![alt](nonexistent.png)\n", encoding="utf-8")

        from bookforge.parser.markdown import parse_markdown_file
        from bookforge.parser.transform import tokens_to_ast

        tokens = parse_markdown_file(md_file)
        with pytest.raises(InputError, match="nonexistent.png"):
            tokens_to_ast(tokens, md_file)


class TestASTImmutability:
    """Tests d'immutabilite des noeuds."""

    def test_parser_nodes_are_frozen(self) -> None:
        book = _load_minimal_book()
        with pytest.raises(AttributeError):
            book.title = "modified"  # type: ignore[misc]
        chapter = book.chapters[0]
        with pytest.raises(AttributeError):
            chapter.title = "modified"  # type: ignore[misc]

    def test_parser_children_are_tuples(self) -> None:
        book = _load_minimal_book()
        assert isinstance(book.chapters, tuple)
        assert isinstance(book.chapters[0].children, tuple)
