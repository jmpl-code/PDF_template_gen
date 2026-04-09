"""Tests des balises semantiques : parser, AST, renderers (Story 4.3)."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from bookforge.ast_nodes import (
    ASTNode,
    BookNode,
    CalloutNode,
    ChapterSummaryNode,
    FrameworkNode,
)
from bookforge.config import load_book_config
from bookforge.parser import parse_book
from bookforge.parser.markdown import parse_markdown_file
from bookforge.parser.transform import tokens_to_ast
from bookforge.renderers.epub import _ast_to_markdown, _render_node_to_markdown
from bookforge.renderers.pdf import _render_node, generate_typst

FIXTURES = Path(__file__).parent / "fixtures"
BOOKS = FIXTURES / "books"

_SOURCE = Path("test.md")


# --- AST Node Tests ---


class TestSemanticASTNodes:
    """Tests des noeuds AST semantiques."""

    def test_framework_node_is_frozen(self) -> None:
        node = FrameworkNode(content="text", source_file=_SOURCE, line_number=1)
        with pytest.raises(AttributeError):
            node.content = "modified"  # type: ignore[misc]

    def test_callout_node_is_frozen(self) -> None:
        node = CalloutNode(content="text", source_file=_SOURCE, line_number=1)
        with pytest.raises(AttributeError):
            node.content = "modified"  # type: ignore[misc]

    def test_chapter_summary_node_is_frozen(self) -> None:
        node = ChapterSummaryNode(content="text", source_file=_SOURCE, line_number=1)
        with pytest.raises(AttributeError):
            node.content = "modified"  # type: ignore[misc]

    def test_semantic_nodes_carry_source_file_and_line_number(self) -> None:
        for cls in (FrameworkNode, CalloutNode, ChapterSummaryNode):
            node = cls(content="c", source_file=_SOURCE, line_number=42)
            assert node.source_file == _SOURCE
            assert node.line_number == 42

    def test_semantic_nodes_in_ast_node_union(self) -> None:
        """Verify semantic nodes are valid ASTNode types."""
        from typing import ForwardRef, get_args

        args = get_args(ASTNode)
        type_names: set[str] = set()
        for a in args:
            if isinstance(a, str):
                type_names.add(a)
            elif isinstance(a, ForwardRef):
                type_names.add(a.__forward_arg__)
            else:
                type_names.add(a.__name__)
        assert "FrameworkNode" in type_names
        assert "CalloutNode" in type_names
        assert "ChapterSummaryNode" in type_names


# --- Parser Tests ---


class TestSemanticParser:
    """Tests du parsing des balises semantiques."""

    def _parse_md(self, content: str, tmp_path: Path) -> list[ASTNode]:
        md_file = tmp_path / "test.md"
        md_file.write_text(content, encoding="utf-8")
        tokens = parse_markdown_file(md_file)
        return tokens_to_ast(tokens, md_file)

    def test_parser_framework_block_creates_node(self, tmp_path: Path) -> None:
        nodes = self._parse_md(
            ":::framework\nContenu framework.\n:::\n", tmp_path
        )
        frameworks = [n for n in nodes if isinstance(n, FrameworkNode)]
        assert len(frameworks) == 1
        assert frameworks[0].content == "Contenu framework."

    def test_parser_callout_block_creates_node(self, tmp_path: Path) -> None:
        nodes = self._parse_md(
            ":::callout\nAttention!\n:::\n", tmp_path
        )
        callouts = [n for n in nodes if isinstance(n, CalloutNode)]
        assert len(callouts) == 1
        assert callouts[0].content == "Attention!"

    def test_parser_chapter_summary_block_creates_node(self, tmp_path: Path) -> None:
        nodes = self._parse_md(
            ":::chapter-summary\nResume ici.\n:::\n", tmp_path
        )
        summaries = [n for n in nodes if isinstance(n, ChapterSummaryNode)]
        assert len(summaries) == 1
        assert summaries[0].content == "Resume ici."

    def test_parser_multiline_content_preserved(self, tmp_path: Path) -> None:
        nodes = self._parse_md(
            ":::framework\nLigne 1.\nLigne 2.\nLigne 3.\n:::\n", tmp_path
        )
        frameworks = [n for n in nodes if isinstance(n, FrameworkNode)]
        assert len(frameworks) == 1
        assert "Ligne 1." in frameworks[0].content
        assert "Ligne 2." in frameworks[0].content
        assert "Ligne 3." in frameworks[0].content

    def test_parser_semantic_nodes_carry_line_number(self, tmp_path: Path) -> None:
        nodes = self._parse_md(
            "# Title\n\nParagraph.\n\n:::framework\nContenu.\n:::\n", tmp_path
        )
        frameworks = [n for n in nodes if isinstance(n, FrameworkNode)]
        assert len(frameworks) == 1
        assert frameworks[0].line_number > 0

    def test_parser_unknown_tag_emits_warning_and_is_ignored(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level(logging.WARNING, logger="bookforge.parser.semantic"):
            nodes = self._parse_md(
                ":::unknown\nContenu.\n:::\n", tmp_path
            )
        unknown_nodes = [
            n
            for n in nodes
            if isinstance(n, (FrameworkNode, CalloutNode, ChapterSummaryNode))
        ]
        assert len(unknown_nodes) == 0
        assert any("Unknown semantic tag 'unknown'" in r.message for r in caplog.records)

    def test_parser_mixed_content_preserves_order(self, tmp_path: Path) -> None:
        md = (
            "# Title\n\nParagraph.\n\n"
            ":::framework\nFW.\n:::\n\n"
            "Another paragraph.\n\n"
            ":::callout\nNote.\n:::\n"
        )
        nodes = self._parse_md(md, tmp_path)
        types = [type(n).__name__ for n in nodes]
        assert types == [
            "HeadingNode",
            "ParagraphNode",
            "FrameworkNode",
            "ParagraphNode",
            "CalloutNode",
        ]

    def test_parser_no_semantic_tags_backward_compat(self, tmp_path: Path) -> None:
        """Markdown without ::: tags parses exactly as before."""
        nodes = self._parse_md(
            "# Title\n\nSome text.\n", tmp_path
        )
        types = [type(n).__name__ for n in nodes]
        assert types == ["HeadingNode", "ParagraphNode"]


# --- PDF Renderer Tests ---


class TestSemanticPDFRenderer:
    """Tests du rendu Typst pour les noeuds semantiques."""

    def test_render_framework_produces_typst_block(self, tmp_path: Path) -> None:
        node = FrameworkNode(content="Porter analysis.", source_file=_SOURCE, line_number=1)
        result = _render_node(node, tmp_path)
        assert "#block(" in result
        assert "FRAMEWORK" in result
        assert "Porter analysis." in result
        assert 'rgb("#2563eb")' in result

    def test_render_callout_produces_typst_block(self, tmp_path: Path) -> None:
        node = CalloutNode(content="Attention!", source_file=_SOURCE, line_number=1)
        result = _render_node(node, tmp_path)
        assert "#block(" in result
        assert "Attention!" in result
        assert 'rgb("#d97706")' in result

    def test_render_chapter_summary_produces_typst_block(self, tmp_path: Path) -> None:
        node = ChapterSummaryNode(content="Summary text.", source_file=_SOURCE, line_number=1)
        result = _render_node(node, tmp_path)
        assert "#block(" in result
        assert "Resume" in result
        assert "Summary text." in result
        assert 'rgb("#9ca3af")' in result

    def test_render_framework_escapes_typst_chars(self, tmp_path: Path) -> None:
        node = FrameworkNode(content="Use #hash and $dollar", source_file=_SOURCE, line_number=1)
        result = _render_node(node, tmp_path)
        assert "\\#hash" in result
        assert "\\$dollar" in result

    def test_render_semantic_nodes_visually_distinct(self, tmp_path: Path) -> None:
        """Each semantic type produces different Typst styling."""
        fw_node = FrameworkNode(content="a", source_file=_SOURCE, line_number=1)
        co_node = CalloutNode(content="a", source_file=_SOURCE, line_number=1)
        cs_node = ChapterSummaryNode(
            content="a", source_file=_SOURCE, line_number=1,
        )
        fw = _render_node(fw_node, tmp_path)
        co = _render_node(co_node, tmp_path)
        cs = _render_node(cs_node, tmp_path)
        # All different
        assert fw != co
        assert co != cs
        assert fw != cs


# --- EPUB Renderer Tests ---


class TestSemanticEPUBRenderer:
    """Tests du rendu EPUB pour les noeuds semantiques."""

    def test_render_framework_produces_div(self, tmp_path: Path) -> None:
        node = FrameworkNode(content="Porter.", source_file=_SOURCE, line_number=1)
        result = _render_node_to_markdown(node, tmp_path, [0])
        assert '<div class="framework">' in result
        assert "Porter." in result
        assert "</div>" in result

    def test_render_callout_produces_div(self, tmp_path: Path) -> None:
        node = CalloutNode(content="Attention!", source_file=_SOURCE, line_number=1)
        result = _render_node_to_markdown(node, tmp_path, [0])
        assert '<div class="callout">' in result
        assert "Attention!" in result
        assert "</div>" in result

    def test_render_chapter_summary_produces_div(self, tmp_path: Path) -> None:
        node = ChapterSummaryNode(content="Resume.", source_file=_SOURCE, line_number=1)
        result = _render_node_to_markdown(node, tmp_path, [0])
        assert '<div class="chapter-summary">' in result
        assert "Resume." in result
        assert "</div>" in result

    def test_epub_css_contains_semantic_styles(self) -> None:
        from bookforge.renderers.epub import _KINDLE_CSS

        assert ".framework" in _KINDLE_CSS
        assert ".callout" in _KINDLE_CSS
        assert ".chapter-summary" in _KINDLE_CSS

    def test_epub_dynamic_css_contains_semantic_styles(self) -> None:
        from bookforge.renderers.epub import _build_css_from_tokens
        from bookforge.tokens.resolver import ResolvedTokenSet

        tokens = ResolvedTokenSet()
        css = _build_css_from_tokens(tokens)
        assert ".framework" in css
        assert ".callout" in css
        assert ".chapter-summary" in css


# --- Integration Tests ---


class TestSemanticIntegration:
    """Tests d'integration pipeline avec balises semantiques."""

    def test_parse_book_with_semantic_fixture(self) -> None:
        book_yaml = BOOKS / "with_semantic" / "book.yaml"
        config = load_book_config(book_yaml)
        book = parse_book(config, book_yaml.parent)

        assert isinstance(book, BookNode)
        assert len(book.chapters) == 1
        chapter = book.chapters[0]

        # Verify all semantic node types present
        node_types = {type(n).__name__ for n in chapter.children}
        assert "FrameworkNode" in node_types
        assert "CalloutNode" in node_types
        assert "ChapterSummaryNode" in node_types
        # Plus regular nodes
        assert "HeadingNode" in node_types
        assert "ParagraphNode" in node_types

    def test_generate_typst_with_semantic_nodes(self, tmp_path: Path) -> None:
        """Full pipeline: parse fixture -> generate .typ -> verify content."""
        book_yaml = BOOKS / "with_semantic" / "book.yaml"
        config = load_book_config(book_yaml)
        book = parse_book(config, book_yaml.parent)

        typ_path = tmp_path / "output.typ"
        generate_typst(book, typ_path)
        typ_content = typ_path.read_text(encoding="utf-8")

        assert "#block(" in typ_content
        assert "FRAMEWORK" in typ_content
        assert "Resume" in typ_content

    def test_render_epub_with_semantic_nodes(self, tmp_path: Path) -> None:
        """Full pipeline: parse fixture -> generate EPUB markdown -> verify content."""
        book_yaml = BOOKS / "with_semantic" / "book.yaml"
        config = load_book_config(book_yaml)
        book = parse_book(config, book_yaml.parent)

        build_dir = tmp_path / "build"
        build_dir.mkdir()
        md_content = _ast_to_markdown(book, build_dir)

        assert '<div class="framework">' in md_content
        assert '<div class="callout">' in md_content
        assert '<div class="chapter-summary">' in md_content
