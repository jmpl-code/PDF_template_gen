"""Tests du renderer EPUB Pandoc (Story 3.1)."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from bookforge.ast_nodes import (
    BookNode,
    ChapterNode,
    HeadingNode,
    ImageNode,
    ParagraphNode,
    TableNode,
)
from bookforge.config.schema import BookConfig, ChapterConfig
from bookforge.errors import RenderError
from bookforge.renderers.epub import (
    _ast_to_markdown,
    _generate_metadata,
    _render_table_as_markdown,
    render_epub,
)

# --- Helpers ---

_SOURCE = Path("test.md")


def _make_config() -> BookConfig:
    return BookConfig(
        titre="Mon Livre",
        sous_titre="Sous-titre",
        auteur="JM",
        genre="business",
        isbn="978-2-1234-5678-0",
        description="Un livre business.",
        mots_cles=["business", "management"],
        chapitres=[ChapterConfig(titre="Intro", fichier="intro.md")],
    )


def _make_minimal_book() -> BookNode:
    return BookNode(
        title="Mon Livre",
        chapters=(
            ChapterNode(
                title="Introduction",
                children=(
                    HeadingNode(level=2, text="Section 1", source_file=_SOURCE, line_number=1),
                    ParagraphNode(text="Un paragraphe.", source_file=_SOURCE, line_number=3),
                    ImageNode(
                        src=Path("/images/diagram.png"),
                        alt="Diagramme",
                        source_file=_SOURCE,
                        line_number=5,
                    ),
                    TableNode(
                        headers=("A", "B"),
                        rows=(("1", "2"), ("3", "4")),
                        source_file=_SOURCE,
                        line_number=7,
                    ),
                ),
                source_file=_SOURCE,
                line_number=1,
            ),
        ),
        source_file=_SOURCE,
        line_number=1,
    )


def _make_wide_table_book() -> BookNode:
    return BookNode(
        title="Wide Tables",
        chapters=(
            ChapterNode(
                title="Chapitre",
                children=(
                    TableNode(
                        headers=("A", "B", "C", "D", "E"),
                        rows=(("1", "2", "3", "4", "5"),),
                        source_file=_SOURCE,
                        line_number=1,
                    ),
                ),
                source_file=_SOURCE,
                line_number=1,
            ),
        ),
        source_file=_SOURCE,
        line_number=1,
    )


# --- Task 4.1: AST → Markdown ---


class TestAstToMarkdown:
    def test_ast_to_markdown_minimal_book(self, tmp_path: Path) -> None:
        """AST minimal → Markdown intermédiaire correct."""
        book = _make_minimal_book()
        md = _ast_to_markdown(book, tmp_path)

        assert "# Introduction\n\n" in md
        assert "## Section 1\n\n" in md
        assert "Un paragraphe.\n\n" in md
        assert "![Diagramme](" in md
        assert "diagram.png)" in md
        # Table with 2 columns → pipe table
        assert "| A | B |" in md
        assert "| 1 | 2 |" in md

    def test_ast_to_markdown_chapter_heading(self, tmp_path: Path) -> None:
        """ChapterNode generates level-1 heading."""
        book = BookNode(
            title="Test",
            chapters=(
                ChapterNode(
                    title="Mon Chapitre",
                    children=(),
                    source_file=_SOURCE,
                    line_number=1,
                ),
            ),
            source_file=_SOURCE,
            line_number=1,
        )
        md = _ast_to_markdown(book, tmp_path)
        assert md.startswith("# Mon Chapitre\n\n")

    def test_ast_to_markdown_empty_table_skipped(self, tmp_path: Path) -> None:
        """Empty table (0 headers) is skipped with warning."""
        book = BookNode(
            title="Test",
            chapters=(
                ChapterNode(
                    title="Ch",
                    children=(
                        TableNode(
                            headers=(),
                            rows=(),
                            source_file=_SOURCE,
                            line_number=1,
                        ),
                    ),
                    source_file=_SOURCE,
                    line_number=1,
                ),
            ),
            source_file=_SOURCE,
            line_number=1,
        )
        md = _ast_to_markdown(book, tmp_path)
        # Only the chapter heading, no table
        assert md.strip() == "# Ch"


# --- Task 4.2: Metadata YAML ---


class TestGenerateMetadata:
    def test_generate_metadata_complete(self) -> None:
        """Métadonnées YAML générées correctement depuis BookConfig complet."""
        config = _make_config()
        meta = _generate_metadata(config)

        assert meta["title"] == "Mon Livre"
        assert meta["author"] == "JM"
        assert meta["lang"] == "fr"
        assert "JM" in str(meta["rights"])
        assert "\u00a9" in str(meta["rights"])
        assert meta["description"] == "Un livre business."
        assert meta["keywords"] == ["business", "management"]
        assert meta["identifier"] == "978-2-1234-5678-0"

    def test_generate_metadata_minimal(self) -> None:
        """Métadonnées sans champs optionnels."""
        config = BookConfig(
            titre="Titre",
            auteur="Auteur",
            genre="fiction",
            chapitres=[ChapterConfig(titre="Ch", fichier="ch.md")],
        )
        meta = _generate_metadata(config)

        assert meta["title"] == "Titre"
        assert meta["author"] == "Auteur"
        assert "description" not in meta
        assert "keywords" not in meta
        assert "identifier" not in meta

    def test_metadata_yaml_serializable(self) -> None:
        """Metadata dict can be serialized to valid YAML."""
        config = _make_config()
        meta = _generate_metadata(config)
        yaml_str = yaml.dump(meta, allow_unicode=True, default_flow_style=False)
        parsed = yaml.safe_load(yaml_str)
        assert parsed["title"] == "Mon Livre"


# --- Task 4.3: Wide table → image fallback ---


class TestWideTableFallback:
    @patch("bookforge.renderers.epub.plt")
    def test_wide_table_generates_image(self, mock_plt: MagicMock, tmp_path: Path) -> None:
        """Tableau > 4 colonnes → image fallback via Matplotlib."""
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_plt.subplots.return_value = (mock_fig, mock_ax)

        book = _make_wide_table_book()
        md = _ast_to_markdown(book, tmp_path)

        # Should generate image reference, not pipe table
        assert "![Table 1](" in md
        assert "table_1.png" in md
        assert "| A |" not in md

        # Matplotlib called correctly
        mock_ax.axis.assert_called_once_with("off")
        mock_ax.table.assert_called_once()
        mock_fig.savefig.assert_called_once()
        call_kwargs = mock_fig.savefig.call_args
        assert call_kwargs[1]["dpi"] == 300
        mock_plt.close.assert_called_once_with(mock_fig)


# --- Task 4.4: Small table → pipe table ---


class TestSmallTableMarkdown:
    def test_table_4_columns_pipe_table(self, tmp_path: Path) -> None:
        """Tableau ≤ 4 colonnes → Markdown pipe table."""
        table = TableNode(
            headers=("A", "B", "C", "D"),
            rows=(("1", "2", "3", "4"),),
            source_file=_SOURCE,
            line_number=1,
        )
        md = _render_table_as_markdown(table)
        assert "| A | B | C | D |" in md
        assert "| --- | --- | --- | --- |" in md
        assert "| 1 | 2 | 3 | 4 |" in md

    def test_table_2_columns_pipe_table(self, tmp_path: Path) -> None:
        """Tableau 2 colonnes → pipe table standard."""
        table = TableNode(
            headers=("X", "Y"),
            rows=(("a", "b"),),
            source_file=_SOURCE,
            line_number=1,
        )
        md = _render_table_as_markdown(table)
        assert "| X | Y |" in md
        assert "| a | b |" in md


# --- Task 4.5: render_epub integration ---


class TestRenderEpub:
    @patch("bookforge.renderers.epub.run_external")
    def test_render_epub_calls_pandoc(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """render_epub() appelle run_external avec les bons arguments Pandoc."""
        mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0)
        book = _make_minimal_book()
        config = _make_config()

        result = render_epub(book, tmp_path, config=config)

        assert result == tmp_path / "livre.epub"
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        # description may be positional or keyword
        positional = mock_run.call_args[0]
        kwargs = mock_run.call_args[1]
        desc = positional[1] if len(positional) > 1 else kwargs.get("description", "")

        assert cmd[0] == "pandoc"
        assert any("content.md" in arg for arg in cmd)
        assert any("--css=" in arg for arg in cmd)
        assert any("--epub-chapter-level=1" in arg for arg in cmd)
        assert any("--toc" in arg for arg in cmd)
        assert any("--metadata-file=" in arg for arg in cmd)
        assert any(arg.endswith("livre.epub") for arg in cmd)
        assert "Pandoc" in desc

    @patch("bookforge.renderers.epub.run_external")
    def test_render_epub_without_config(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """render_epub() sans config → pas de metadata-file."""
        mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0)
        book = _make_minimal_book()

        result = render_epub(book, tmp_path)

        assert result == tmp_path / "livre.epub"
        cmd = mock_run.call_args[0][0]
        assert not any("--metadata-file=" in arg for arg in cmd)

    @patch("bookforge.renderers.epub.run_external")
    def test_render_epub_creates_build_dir(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """render_epub() crée le sous-dossier _epub_build."""
        mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0)
        book = _make_minimal_book()

        render_epub(book, tmp_path)

        build_dir = tmp_path / "_epub_build"
        assert build_dir.is_dir()
        assert (build_dir / "content.md").is_file()
        assert (build_dir / "epub.css").is_file()

    @patch("bookforge.renderers.epub.run_external")
    def test_render_epub_css_content(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """CSS Kindle basique est écrit correctement."""
        mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0)
        book = _make_minimal_book()

        render_epub(book, tmp_path)

        css = (tmp_path / "_epub_build" / "epub.css").read_text(encoding="utf-8")
        assert "font-family: serif" in css
        assert "line-height: 1.4" in css

    @patch("bookforge.renderers.epub.run_external")
    def test_render_epub_metadata_yaml_written(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Fichier metadata.yaml est écrit avec les bonnes valeurs."""
        mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0)
        config = _make_config()
        book = _make_minimal_book()

        render_epub(book, tmp_path, config=config)

        meta_path = tmp_path / "_epub_build" / "metadata.yaml"
        assert meta_path.is_file()
        meta = yaml.safe_load(meta_path.read_text(encoding="utf-8"))
        assert meta["title"] == "Mon Livre"
        assert meta["author"] == "JM"
        assert meta["lang"] == "fr"


# --- Task 4.6: Pandoc not found → RenderError ---


class TestPandocErrors:
    def test_render_epub_pandoc_not_found_raises_render_error(self, tmp_path: Path) -> None:
        """Si Pandoc n'est pas installé → RenderError."""
        book = _make_minimal_book()

        with patch(
            "bookforge.renderers.epub.run_external",
            side_effect=RenderError("Generation EPUB via Pandoc: commande 'pandoc' introuvable"),
        ):
            with pytest.raises(RenderError, match="pandoc.*introuvable"):
                render_epub(book, tmp_path)
