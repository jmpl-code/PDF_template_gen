"""Tests CLI Typer (Story 2.9)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from bookforge.cli import app
from bookforge.errors import InputError, RenderError

runner = CliRunner()

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "books"


class TestCliExitCodes:
    """Tests des codes de sortie CLI."""

    def test_cli_success_exit_code_0(self, tmp_path: Path) -> None:
        """Exit code 0 en cas de succes."""
        book_yaml = FIXTURES_DIR / "minimal" / "book.yaml"

        with patch("bookforge.cli.run_pipeline") as mock_pipeline:
            mock_pipeline.return_value = tmp_path / "output"
            result = runner.invoke(
                app,
                [str(book_yaml), "--output-dir", str(tmp_path / "output")],
            )

        assert result.exit_code == 0

    def test_cli_input_error_exit_code_1(self) -> None:
        """Exit code 1 pour InputError."""
        with patch("bookforge.cli.run_pipeline") as mock_pipeline:
            mock_pipeline.side_effect = InputError("Fichier introuvable")
            result = runner.invoke(app, ["nonexistent.yaml"])

        assert result.exit_code == 1

    def test_cli_render_error_exit_code_2(self) -> None:
        """Exit code 2 pour RenderError."""
        book_yaml = FIXTURES_DIR / "minimal" / "book.yaml"

        with patch("bookforge.cli.run_pipeline") as mock_pipeline:
            mock_pipeline.side_effect = RenderError("Typst introuvable")
            result = runner.invoke(app, [str(book_yaml)])

        assert result.exit_code == 2

    def test_cli_unexpected_error_exit_code_1(self) -> None:
        """Exit code 1 pour erreur inattendue."""
        book_yaml = FIXTURES_DIR / "minimal" / "book.yaml"

        with patch("bookforge.cli.run_pipeline") as mock_pipeline:
            mock_pipeline.side_effect = RuntimeError("unexpected")
            result = runner.invoke(app, [str(book_yaml)])

        assert result.exit_code == 1


class TestCliProgress:
    """Tests de la progression affichee."""

    def test_cli_progress_displayed_on_stderr(self) -> None:
        """La progression est affichee sur stderr."""
        book_yaml = FIXTURES_DIR / "minimal" / "book.yaml"

        with patch("bookforge.cli.run_pipeline") as mock_pipeline:
            # Simuler le pipeline qui appelle le callback
            def call_with_progress(
                book_path: Path,
                output_dir: Path,
                progress_callback: object = None,
            ) -> Path:
                if progress_callback:
                    progress_callback("parsing", 0)  # type: ignore[operator]
                    progress_callback("parsing", 100)  # type: ignore[operator]
                return output_dir

            mock_pipeline.side_effect = call_with_progress
            result = runner.invoke(app, [str(book_yaml)])

        assert "[Phase 1/3] parsing... 0%" in result.stderr
        assert "[Phase 1/3] parsing... 100%" in result.stderr


class TestCliOptions:
    """Tests des options CLI."""

    def test_cli_judge_stub_warns(self) -> None:
        """--judge affiche un warning."""
        book_yaml = FIXTURES_DIR / "minimal" / "book.yaml"

        with patch("bookforge.cli.run_pipeline") as mock_pipeline:
            mock_pipeline.return_value = Path("output")
            result = runner.invoke(app, [str(book_yaml), "--judge"])

        assert result.exit_code == 0

    def test_cli_preview_stub_warns(self) -> None:
        """--preview affiche un warning."""
        book_yaml = FIXTURES_DIR / "minimal" / "book.yaml"

        with patch("bookforge.cli.run_pipeline") as mock_pipeline:
            mock_pipeline.return_value = Path("output")
            result = runner.invoke(app, [str(book_yaml), "--preview"])

        assert result.exit_code == 0


class TestMainModule:
    """Test du __main__.py."""

    def test_main_module_exists_and_has_correct_content(self) -> None:
        """__main__.py existe et contient l'appel a app()."""
        main_path = Path(__file__).parent.parent / "src" / "bookforge" / "__main__.py"
        assert main_path.exists(), "__main__.py must exist"
        content = main_path.read_text(encoding="utf-8")
        assert "from bookforge.cli import app" in content
        assert "app()" in content
