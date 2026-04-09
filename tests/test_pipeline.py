"""Tests pipeline orchestrateur (Stories 2.9, 3.2, 4.2)."""

from __future__ import annotations

import logging
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


class TestPipelineTokenIntegration:
    """Tests integration pipeline + design tokens (Story 4.2)."""

    def _fake_compile(self, cmd: list[str], description: str) -> MagicMock:
        """Mock compile qui cree un faux fichier de sortie."""
        out_path = Path(cmd[-1])
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(b"%PDF-1.4 fake")
        return MagicMock()

    def test_pipeline_with_class_resolves_tokens(self, tmp_path: Path) -> None:
        """Pipeline avec class: business-manual applique les tokens dans le .typ."""
        book_dir = tmp_path / "book"
        book_yaml = _copy_fixture_to("with_class", book_dir)
        output_dir = tmp_path / "output"

        with (
            patch("bookforge.renderers.pdf.run_external") as mock_pdf_ext,
            patch("bookforge.renderers.cover.run_external") as mock_cover_ext,
        ):
            mock_pdf_ext.side_effect = self._fake_compile
            mock_cover_ext.side_effect = self._fake_compile

            run_pipeline(book_path=book_yaml.resolve(), output_dir=output_dir)

        # Le .typ est genere dans book_dir (build dir = book_root)
        typ_file = book_dir / "livre-interieur.typ"
        assert typ_file.exists()
        typ_content = typ_file.read_text(encoding="utf-8")

        # La fixture with_class a un tokens.yaml avec font_size: 12, line_height: 1.40
        assert "size: 12pt" in typ_content
        assert "leading: 1.4em" in typ_content

    def test_pipeline_with_class_and_user_tokens_overrides(self, tmp_path: Path) -> None:
        """Les tokens auteur surchargent les tokens de classe dans le .typ."""
        book_dir = tmp_path / "book"
        book_yaml = _copy_fixture_to("with_class", book_dir)
        output_dir = tmp_path / "output"

        with (
            patch("bookforge.renderers.pdf.run_external") as mock_pdf_ext,
            patch("bookforge.renderers.cover.run_external") as mock_cover_ext,
        ):
            mock_pdf_ext.side_effect = self._fake_compile
            mock_cover_ext.side_effect = self._fake_compile

            run_pipeline(book_path=book_yaml.resolve(), output_dir=output_dir)

        typ_content = (book_dir / "livre-interieur.typ").read_text(encoding="utf-8")

        # margin_inner surcharge = 2.5cm (au lieu du default 2cm)
        assert "inside: 2.5cm" in typ_content

    def test_pipeline_without_class_backward_compat(self, tmp_path: Path) -> None:
        """Pipeline avec fixture minimal (sans class) utilise les tokens par defaut."""
        book_dir = tmp_path / "book"
        book_yaml = _copy_fixture_to("minimal", book_dir)
        output_dir = tmp_path / "output"

        with (
            patch("bookforge.renderers.pdf.run_external") as mock_pdf_ext,
            patch("bookforge.renderers.cover.run_external") as mock_cover_ext,
        ):
            mock_pdf_ext.side_effect = self._fake_compile
            mock_cover_ext.side_effect = self._fake_compile

            result = run_pipeline(book_path=book_yaml.resolve(), output_dir=output_dir)

        assert result == output_dir
        assert (output_dir / "livre-interieur.pdf").exists()

        # Verifie que le .typ utilise les defaults business-manual
        typ_content = (book_dir / "livre-interieur.typ").read_text(encoding="utf-8")
        assert "size: 11pt" in typ_content
        assert "leading: 1.35em" in typ_content

    def test_pipeline_unknown_class_warns_and_falls_back(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Classe inconnue emet un warning et utilise les tokens registre."""
        book_dir = tmp_path / "book"
        book_yaml = _copy_fixture_to("minimal", book_dir)
        book_yaml.write_text(
            'titre: "T"\nauteur: "A"\ngenre: "g"\nclass: "unknown-class"\n'
            'chapitres:\n  - titre: "Intro"\n    fichier: "chapitres/01-introduction.md"\n',
            encoding="utf-8",
        )
        output_dir = tmp_path / "output"

        with (
            patch("bookforge.renderers.pdf.run_external") as mock_pdf_ext,
            patch("bookforge.renderers.cover.run_external") as mock_cover_ext,
            caplog.at_level(logging.WARNING, logger="bookforge.tokens.resolver"),
        ):
            mock_pdf_ext.side_effect = self._fake_compile
            mock_cover_ext.side_effect = self._fake_compile

            result = run_pipeline(book_path=book_yaml.resolve(), output_dir=output_dir)

        assert result == output_dir
        assert "introuvable" in caplog.text or "defaults" in caplog.text

    def test_pipeline_explicit_tokens_path_in_config(self, tmp_path: Path) -> None:
        """Le champ tokens dans book.yaml pointe vers un fichier specifique."""
        book_dir = tmp_path / "book"
        book_yaml = _copy_fixture_to("minimal", book_dir)
        custom_tokens = book_dir / "my-tokens.yaml"
        custom_tokens.write_text("font_size: 13\n", encoding="utf-8")
        book_yaml.write_text(
            'titre: "T"\nauteur: "A"\ngenre: "g"\ntokens: "my-tokens.yaml"\n'
            'chapitres:\n  - titre: "Intro"\n    fichier: "chapitres/01-introduction.md"\n',
            encoding="utf-8",
        )
        output_dir = tmp_path / "output"

        with (
            patch("bookforge.renderers.pdf.run_external") as mock_pdf_ext,
            patch("bookforge.renderers.cover.run_external") as mock_cover_ext,
        ):
            mock_pdf_ext.side_effect = self._fake_compile
            mock_cover_ext.side_effect = self._fake_compile

            run_pipeline(book_path=book_yaml.resolve(), output_dir=output_dir)

        typ_content = (book_dir / "livre-interieur.typ").read_text(encoding="utf-8")
        assert "size: 13pt" in typ_content

    def test_pipeline_with_typst_raw_injects_in_typ(self, tmp_path: Path) -> None:
        """Story 4.4 : fixture with_typst_raw injecte le champ tel quel dans le .typ."""
        book_dir = tmp_path / "book"
        book_yaml = _copy_fixture_to("with_typst_raw", book_dir)
        output_dir = tmp_path / "output"

        with (
            patch("bookforge.renderers.pdf.run_external") as mock_pdf_ext,
            patch("bookforge.renderers.cover.run_external") as mock_cover_ext,
        ):
            mock_pdf_ext.side_effect = self._fake_compile
            mock_cover_ext.side_effect = self._fake_compile

            run_pipeline(book_path=book_yaml.resolve(), output_dir=output_dir)

        typ_content = (book_dir / "livre-interieur.typ").read_text(encoding="utf-8")
        assert "BEGIN typst_raw" in typ_content
        assert '#let accent = rgb("#2563eb")' in typ_content
        # Verifie aussi que la numerotation romaine est presente (Story 4.4 AC#1)
        assert '#set page(numbering: "i")' in typ_content

    def test_pipeline_missing_tokens_file_raises_input_error(self, tmp_path: Path) -> None:
        """Fichier tokens reference mais introuvable leve InputError."""
        book_dir = tmp_path / "book"
        book_yaml = _copy_fixture_to("minimal", book_dir)
        book_yaml.write_text(
            'titre: "T"\nauteur: "A"\ngenre: "g"\ntokens: "nonexistent.yaml"\n'
            'chapitres:\n  - titre: "Intro"\n    fichier: "chapitres/01-introduction.md"\n',
            encoding="utf-8",
        )
        output_dir = tmp_path / "output"

        with pytest.raises(InputError, match="tokens introuvable"):
            run_pipeline(book_path=book_yaml.resolve(), output_dir=output_dir)
