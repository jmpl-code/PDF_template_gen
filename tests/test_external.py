"""Tests pour run_external() — pattern subprocess uniforme."""

import sys

import pytest

from bookforge.errors import RenderError
from bookforge.external import run_external


class TestRunExternal:
    """Tests du wrapper subprocess."""

    def test_successful_command(self) -> None:
        result = run_external(
            [sys.executable, "-c", "print('hello')"],
            "Test Python",
        )
        assert result.stdout.strip() == "hello"
        assert result.returncode == 0

    def test_command_not_found_raises_render_error(self) -> None:
        with pytest.raises(RenderError, match="commande 'inexistant_xyz' introuvable"):
            run_external(["inexistant_xyz"], "Test commande introuvable")

    def test_command_failure_raises_render_error(self) -> None:
        with pytest.raises(RenderError, match="Test echec"):
            run_external(
                [sys.executable, "-c", "import sys; sys.stderr.write('erreur'); sys.exit(1)"],
                "Test echec",
            )

    def test_stderr_content_in_error_message(self) -> None:
        with pytest.raises(RenderError, match="message stderr"):
            run_external(
                [
                    sys.executable,
                    "-c",
                    "import sys; sys.stderr.write('message stderr'); sys.exit(1)",
                ],
                "Description",
            )

    def test_empty_cmd_raises_render_error(self) -> None:
        with pytest.raises(RenderError, match="commande vide"):
            run_external([], "Test vide")

    def test_never_uses_shell(self) -> None:
        """run_external ne doit jamais utiliser shell=True."""
        import inspect

        source = inspect.getsource(run_external)
        assert "shell=True" not in source
        assert "shell = True" not in source
