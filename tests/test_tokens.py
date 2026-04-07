"""Tests du systeme de design tokens (Story 4.1)."""

from __future__ import annotations

import logging
from pathlib import Path
from unittest.mock import patch

import pytest

from bookforge.ast_nodes import BookNode, ChapterNode, HeadingNode, ParagraphNode
from bookforge.tokens.registry import TOKEN_REGISTRY, TokenSpec
from bookforge.tokens.resolver import resolve_tokens

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "tokens"
BOOKS_DIR = Path(__file__).parent / "fixtures" / "books" / "minimal"


# --- Task 1: TokenSpec et TOKEN_REGISTRY ---


class TestTokenSpec:
    """Tests du modele TokenSpec et du registre."""

    def test_token_spec_is_frozen(self) -> None:
        """TokenSpec est immutable (frozen dataclass)."""
        spec = TokenSpec(default=11, min=9, max=14, unit="pt", source="Bringhurst")
        with pytest.raises(AttributeError):
            spec.default = 12  # type: ignore[misc]

    def test_token_spec_registry_completeness(self) -> None:
        """Chaque token du registre a min/max (si numerique) et source."""
        for name, spec in TOKEN_REGISTRY.items():
            assert spec.source, f"Token '{name}' manque une source de reference"
            assert spec.default is not None, f"Token '{name}' manque une valeur par defaut"
            # Les tokens numeriques doivent avoir min/max
            if isinstance(spec.default, (int, float)):
                assert spec.min is not None, f"Token numerique '{name}' manque min"
                assert spec.max is not None, f"Token numerique '{name}' manque max"

    def test_registry_has_expected_tokens(self) -> None:
        """Le registre contient les tokens MVP1 critiques."""
        expected = {
            "font_size",
            "line_height",
            "margin_inner",
            "margin_outer",
            "margin_top",
            "margin_bottom",
            "page_width",
            "page_height",
            "heading_1_size",
            "heading_2_size",
            "heading_3_size",
            "heading_4_size",
            "par_indent",
            "par_skip",
            "font_family",
        }
        assert expected.issubset(set(TOKEN_REGISTRY.keys()))


# --- Task 2: ResolvedTokenSet et resolve_tokens ---


class TestResolveTokens:
    """Tests de la resolution des tokens."""

    def test_resolve_tokens_defaults_only(self) -> None:
        """Sans YAML utilisateur, charge les defaults business-manual."""
        tokens = resolve_tokens()
        assert tokens.font_size == 11
        assert tokens.line_height == 1.35
        assert tokens.page_width == "6in"
        assert tokens.page_height == "9in"
        assert tokens.margin_inner == "2cm"
        assert tokens.heading_1_size == 24

    def test_resolve_tokens_valid_override(self) -> None:
        """Surcharge avec des valeurs valides."""
        tokens = resolve_tokens(FIXTURES_DIR / "valid.yaml")
        assert tokens.font_size == 12
        assert tokens.line_height == 1.40
        assert tokens.margin_inner == "2.5cm"
        assert tokens.heading_1_size == 28
        assert tokens.heading_2_size == 20
        # Valeurs non surchargees restent les defaults
        assert tokens.page_width == "6in"
        assert tokens.par_indent == "1em"

    def test_resolve_tokens_out_of_bounds_warns(self, caplog: pytest.LogCaptureFixture) -> None:
        """Valeurs hors bornes declenchent un warning et utilisent le defaut."""
        with caplog.at_level(logging.WARNING, logger="bookforge.tokens.resolver"):
            tokens = resolve_tokens(FIXTURES_DIR / "out_of_bounds.yaml")

        # Valeurs hors bornes remplacees par defaut
        assert tokens.font_size == 11  # defaut (3 hors bornes [9,14])
        assert tokens.line_height == 1.35  # defaut (2.0 hors bornes [1.20,1.45])
        assert tokens.heading_1_size == 24  # defaut (50 hors bornes [18,36])

        # Verifier les warnings
        warning_messages = [r.message for r in caplog.records]
        assert any("font_size=3" in msg and "hors bornes" in msg for msg in warning_messages)
        assert any("line_height=2.0" in msg and "hors bornes" in msg for msg in warning_messages)
        assert any("heading_1_size=50" in msg and "hors bornes" in msg for msg in warning_messages)

    def test_resolve_tokens_unknown_key_warns(self, caplog: pytest.LogCaptureFixture) -> None:
        """Cles inconnues declenchent un warning et sont ignorees."""
        with caplog.at_level(logging.WARNING, logger="bookforge.tokens.resolver"):
            tokens = resolve_tokens(FIXTURES_DIR / "unknown_keys.yaml")

        # La cle connue est appliquee
        assert tokens.font_size == 12

        # Verifier les warnings pour cles inconnues
        warning_messages = [r.message for r in caplog.records]
        assert any("unknown_token" in msg for msg in warning_messages)
        assert any("another_fake" in msg for msg in warning_messages)

    def test_resolved_token_set_all_fields(self) -> None:
        """ResolvedTokenSet a une valeur pour chaque token du registre."""
        tokens = resolve_tokens()
        for name in TOKEN_REGISTRY:
            assert hasattr(tokens, name), f"ResolvedTokenSet manque le champ '{name}'"
            value = getattr(tokens, name)
            assert value is not None, f"Token '{name}' a une valeur None"

    def test_resolve_tokens_missing_class_uses_registry_defaults(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Classe inexistante utilise les defaults du registre avec warning."""
        with caplog.at_level(logging.WARNING, logger="bookforge.tokens.resolver"):
            tokens = resolve_tokens(class_name="nonexistent-class")
        assert tokens.font_size == 11
        assert any("introuvable" in r.message for r in caplog.records)


# --- Task 6.5: Tests integration renderers ---


class TestPdfWithTokens:
    """Tests d'integration PDF avec tokens."""

    def _make_book(self, tmp_path: Path) -> BookNode:
        source = BOOKS_DIR / "chapitres" / "01-introduction.md"
        return BookNode(
            title="Test Book",
            chapters=(
                ChapterNode(
                    title="Chapitre 1",
                    children=(
                        HeadingNode(level=1, text="Chapitre 1", source_file=source, line_number=1),
                        ParagraphNode(text="Contenu.", source_file=source, line_number=2),
                    ),
                    source_file=source,
                    line_number=1,
                ),
            ),
            source_file=source,
            line_number=1,
        )

    def test_render_pdf_with_tokens(self, tmp_path: Path) -> None:
        """Le .typ genere contient les valeurs des tokens."""
        from bookforge.renderers.pdf import generate_typst

        tokens = resolve_tokens(FIXTURES_DIR / "valid.yaml")
        book = self._make_book(tmp_path)
        typ_path = tmp_path / "output.typ"
        generate_typst(book, typ_path, tokens=tokens)

        content = typ_path.read_text(encoding="utf-8")
        # Verifier que les valeurs des tokens sont dans le .typ
        assert "size: 12pt" in content  # font_size=12
        assert "leading: 1.4em" in content  # line_height=1.40
        assert "inside: 2.5cm" in content  # margin_inner=2.5cm
        assert "size: 28pt" in content  # heading_1_size=28
        assert "Story 4.1" in content  # template dynamique

    def test_render_pdf_without_tokens_backward_compat(self, tmp_path: Path) -> None:
        """Sans tokens, le template hardcode est utilise."""
        from bookforge.renderers.pdf import generate_typst

        book = self._make_book(tmp_path)
        typ_path = tmp_path / "output.typ"
        generate_typst(book, typ_path)

        content = typ_path.read_text(encoding="utf-8")
        # Template hardcode original
        assert "size: 11pt" in content
        assert "leading: 1.35em" in content
        assert "inside: 2cm" in content
        assert "Story 2.3" in content  # original template marker


class TestEpubWithTokens:
    """Tests d'integration EPUB avec tokens."""

    def _make_book(self) -> BookNode:
        source = BOOKS_DIR / "chapitres" / "01-introduction.md"
        return BookNode(
            title="Test Book",
            chapters=(
                ChapterNode(
                    title="Chapitre 1",
                    children=(
                        HeadingNode(level=1, text="Chapitre 1", source_file=source, line_number=1),
                        ParagraphNode(text="Contenu.", source_file=source, line_number=2),
                    ),
                    source_file=source,
                    line_number=1,
                ),
            ),
            source_file=source,
            line_number=1,
        )

    def test_render_epub_with_tokens(self, tmp_path: Path) -> None:
        """Le CSS genere contient les valeurs des tokens."""
        from bookforge.renderers.epub import render_epub

        tokens = resolve_tokens(FIXTURES_DIR / "valid.yaml")
        book = self._make_book()

        with patch("bookforge.renderers.epub.run_external"):
            render_epub(book, tmp_path, tokens=tokens)

        css_path = tmp_path / "_epub_build" / "epub.css"
        content = css_path.read_text(encoding="utf-8")
        # Verifier les valeurs dynamiques
        assert "font-size: 12pt" in content  # font_size=12
        assert "line-height: 1.4" in content  # line_height=1.40
        assert "Story 4.1" in content  # template dynamique

    def test_render_epub_without_tokens_backward_compat(self, tmp_path: Path) -> None:
        """Sans tokens, le CSS statique est utilise."""
        from bookforge.renderers.epub import render_epub

        book = self._make_book()

        with patch("bookforge.renderers.epub.run_external"):
            render_epub(book, tmp_path)

        css_path = tmp_path / "_epub_build" / "epub.css"
        content = css_path.read_text(encoding="utf-8")
        # CSS statique original
        assert "line-height: 1.4" in content
        assert "font-size: 1.8em" in content  # h1 hardcode
        assert "Story 3.1" in content  # original marker
