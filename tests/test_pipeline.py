"""Tests pipeline orchestrateur (Stories 2.9, 3.2)."""

from __future__ import annotations

import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from bookforge.errors import InputError, RenderError
from bookforge.pipeline import run_pipeline

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "books"


def _copy_fixture_to(fixture_name: str, dest: Path) -> Path:
    """Copy a book fixture to dest and return path to book.yaml."""
    src = FIXTURES_DIR / fixture_name
    shutil.copytree(src, dest, dirs_exist_ok=True)
    return dest / "book.yaml"


class TestRunPipeline:
    """Tests d'integration pipeline complet."""

    def test_pipeline_minimal_book_runs_end_to_end(self, tmp_path: Path) -> None:
        """Pipeline complet avec fixture minimal — mock Typst compile."""
        book_dir = tmp_path / "book"
        book_yaml = _copy_fixture_to("minimal", book_dir)
        output_dir = tmp_path / "output"

        with (
            patch("bookforge.renderers.pdf.run_external") as mock_pdf_ext,
            patch("bookforge.renderers.cover.run_external") as mock_cover_ext,
        ):

            def fake_pdf_compile(cmd: list[str], description: str):  # noqa: ANN001
                pdf_path = Path(cmd[-1])
                pdf_path.parent.mkdir(parents=True, exist_ok=True)
                pdf_path.write_bytes(b"%PDF-1.4 fake interior")
                return MagicMock()

            def fake_cover_compile(cmd: list[str], description: str):  # noqa: ANN001
                pdf_path = Path(cmd[-1])
                pdf_path.parent.mkdir(parents=True, exist_ok=True)
                pdf_path.write_bytes(b"%PDF-1.4 fake cover")
                return MagicMock()

            mock_pdf_ext.side_effect = fake_pdf_compile
            mock_cover_ext.side_effect = fake_cover_compile

            result = run_pipeline(
                book_path=book_yaml.resolve(),
                output_dir=output_dir,
            )

        assert result == output_dir
        assert (output_dir / "livre-interieur.pdf").exists()
        assert (output_dir / "couverture.pdf").exists()
        assert (output_dir / "metadata-kdp.json").exists()

    def test_pipeline_invalid_book_yaml_raises_input_error(self, tmp_path: Path) -> None:
        """book.yaml invalide leve InputError."""
        bad_yaml = tmp_path / "book.yaml"
        bad_yaml.write_text("not: valid", encoding="utf-8")

        with pytest.raises(InputError):
            run_pipeline(book_path=bad_yaml, output_dir=tmp_path / "output")

    def test_pipeline_missing_book_yaml_raises_input_error(self, tmp_path: Path) -> None:
        """book.yaml inexistant leve InputError."""
        missing = tmp_path / "nonexistent.yaml"

        with pytest.raises(InputError):
            run_pipeline(book_path=missing, output_dir=tmp_path / "output")

    def test_pipeline_progress_callback_called(self, tmp_path: Path) -> None:
        """progress_callback est appele avec les bonnes phases."""
        book_dir = tmp_path / "book"
        book_yaml = _copy_fixture_to("minimal", book_dir)
        output_dir = tmp_path / "output"
        callback = MagicMock()

        with (
            patch("bookforge.renderers.pdf.run_external") as mock_pdf_ext,
            patch("bookforge.renderers.cover.run_external") as mock_cover_ext,
        ):

            def fake_compile(cmd: list[str], description: str):  # noqa: ANN001
                pdf_path = Path(cmd[-1])
                pdf_path.parent.mkdir(parents=True, exist_ok=True)
                pdf_path.write_bytes(b"%PDF-1.4 fake")
                return MagicMock()

            mock_pdf_ext.side_effect = fake_compile
            mock_cover_ext.side_effect = fake_compile

            run_pipeline(
                book_path=book_yaml.resolve(),
                output_dir=output_dir,
                progress_callback=callback,
            )

        phase_calls = [(c.args[0], c.args[1]) for c in callback.call_args_list]
        assert ("parsing", 0) in phase_calls
        assert ("parsing", 100) in phase_calls
        assert ("rendering", 0) in phase_calls
        assert ("rendering", 100) in phase_calls
        assert ("export", 0) in phase_calls
        assert ("export", 100) in phase_calls

    def test_pipeline_no_callback_does_not_fail(self, tmp_path: Path) -> None:
        """Pipeline sans callback ne crashe pas."""
        book_dir = tmp_path / "book"
        book_yaml = _copy_fixture_to("minimal", book_dir)
        output_dir = tmp_path / "output"

        with (
            patch("bookforge.renderers.pdf.run_external") as mock_pdf_ext,
            patch("bookforge.renderers.cover.run_external") as mock_cover_ext,
        ):

            def fake_compile(cmd: list[str], description: str):  # noqa: ANN001
                pdf_path = Path(cmd[-1])
                pdf_path.parent.mkdir(parents=True, exist_ok=True)
                pdf_path.write_bytes(b"%PDF-1.4 fake")
                return MagicMock()

            mock_pdf_ext.side_effect = fake_compile
            mock_cover_ext.side_effect = fake_compile

            result = run_pipeline(
                book_path=book_yaml.resolve(),
                output_dir=output_dir,
                progress_callback=None,
            )

        assert result == output_dir

    def test_pipeline_output_dir_equals_book_root_raises_input_error(self, tmp_path: Path) -> None:
        """output_dir == book_root leve InputError."""
        book_dir = tmp_path / "book"
        book_yaml = _copy_fixture_to("minimal", book_dir)

        with pytest.raises(InputError, match="ne peut pas etre le meme"):
            run_pipeline(book_path=book_yaml.resolve(), output_dir=book_dir)


class TestDualExport:
    """Tests dual export PDF + EPUB (Story 3.2)."""

    def test_pipeline_produces_pdf_and_epub(self, tmp_path: Path) -> None:
        """Pipeline complet produit PDF et EPUB dans le dossier de sortie."""
        book_dir = tmp_path / "book"
        book_yaml = _copy_fixture_to("minimal", book_dir)
        output_dir = tmp_path / "output"

        with (
            patch("bookforge.renderers.pdf.run_external") as mock_pdf_ext,
            patch("bookforge.renderers.cover.run_external") as mock_cover_ext,
            patch("bookforge.renderers.epub.run_external") as mock_epub_ext,
        ):

            def fake_pdf_compile(cmd: list[str], description: str) -> MagicMock:  # noqa: ANN001
                pdf_path = Path(cmd[-1])
                pdf_path.parent.mkdir(parents=True, exist_ok=True)
                pdf_path.write_bytes(b"%PDF-1.4 fake interior")
                return MagicMock()

            def fake_cover_compile(cmd: list[str], description: str) -> MagicMock:  # noqa: ANN001
                pdf_path = Path(cmd[-1])
                pdf_path.parent.mkdir(parents=True, exist_ok=True)
                pdf_path.write_bytes(b"%PDF-1.4 fake cover")
                return MagicMock()

            def fake_epub_pandoc(cmd: list[str], description: str) -> MagicMock:  # noqa: ANN001
                epub_path = Path(cmd[-1])
                epub_path.parent.mkdir(parents=True, exist_ok=True)
                epub_path.write_bytes(b"PK fake epub")
                return MagicMock()

            mock_pdf_ext.side_effect = fake_pdf_compile
            mock_cover_ext.side_effect = fake_cover_compile
            mock_epub_ext.side_effect = fake_epub_pandoc

            result = run_pipeline(
                book_path=book_yaml.resolve(),
                output_dir=output_dir,
            )

        assert result == output_dir
        assert (output_dir / "livre-interieur.pdf").exists()
        assert (output_dir / "couverture.pdf").exists()
        assert (output_dir / "livre.epub").exists()
        assert (output_dir / "metadata-kdp.json").exists()

    def test_pipeline_epub_failure_still_produces_pdf(self, tmp_path: Path) -> None:
        """Si EPUB echoue, le PDF est quand meme produit sans exception pipeline."""
        book_dir = tmp_path / "book"
        book_yaml = _copy_fixture_to("minimal", book_dir)
        output_dir = tmp_path / "output"

        with (
            patch("bookforge.renderers.pdf.run_external") as mock_pdf_ext,
            patch("bookforge.renderers.cover.run_external") as mock_cover_ext,
            patch("bookforge.renderers.epub.run_external") as mock_epub_ext,
        ):

            def fake_compile(cmd: list[str], description: str) -> MagicMock:  # noqa: ANN001
                pdf_path = Path(cmd[-1])
                pdf_path.parent.mkdir(parents=True, exist_ok=True)
                pdf_path.write_bytes(b"%PDF-1.4 fake")
                return MagicMock()

            mock_pdf_ext.side_effect = fake_compile
            mock_cover_ext.side_effect = fake_compile
            mock_epub_ext.side_effect = RenderError("Pandoc not found")

            result = run_pipeline(
                book_path=book_yaml.resolve(),
                output_dir=output_dir,
            )

        assert result == output_dir
        assert (output_dir / "livre-interieur.pdf").exists()
        assert (output_dir / "couverture.pdf").exists()
        assert not (output_dir / "livre.epub").exists()

    def test_pipeline_dual_export_progress_callback(self, tmp_path: Path) -> None:
        """Les callbacks de progression sont appeles correctement avec dual export."""
        book_dir = tmp_path / "book"
        book_yaml = _copy_fixture_to("minimal", book_dir)
        output_dir = tmp_path / "output"
        callback = MagicMock()

        with (
            patch("bookforge.renderers.pdf.run_external") as mock_pdf_ext,
            patch("bookforge.renderers.cover.run_external") as mock_cover_ext,
            patch("bookforge.renderers.epub.run_external") as mock_epub_ext,
        ):

            def fake_compile(cmd: list[str], description: str) -> MagicMock:  # noqa: ANN001
                out_path = Path(cmd[-1])
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_bytes(b"%PDF-1.4 fake")
                return MagicMock()

            def fake_epub(cmd: list[str], description: str) -> MagicMock:  # noqa: ANN001
                epub_path = Path(cmd[-1])
                epub_path.parent.mkdir(parents=True, exist_ok=True)
                epub_path.write_bytes(b"PK fake epub")
                return MagicMock()

            mock_pdf_ext.side_effect = fake_compile
            mock_cover_ext.side_effect = fake_compile
            mock_epub_ext.side_effect = fake_epub

            run_pipeline(
                book_path=book_yaml.resolve(),
                output_dir=output_dir,
                progress_callback=callback,
            )

        phase_calls = [(c.args[0], c.args[1]) for c in callback.call_args_list]
        assert ("parsing", 0) in phase_calls
        assert ("parsing", 100) in phase_calls
        assert ("rendering", 0) in phase_calls
        assert ("rendering", 100) in phase_calls
        assert ("export", 0) in phase_calls
        assert ("export", 100) in phase_calls
