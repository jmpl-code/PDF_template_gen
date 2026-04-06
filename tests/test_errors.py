"""Tests pour la hierarchie d'erreurs BookForge."""

import pytest

from bookforge.errors import BookForgeError, InputError, LLMError, RenderError


class TestErrorHierarchy:
    """Toutes les erreurs heritent de BookForgeError."""

    @pytest.mark.parametrize(
        ("error_class", "expected_exit_code"),
        [
            (InputError, 1),
            (RenderError, 2),
            (LLMError, 3),
        ],
    )
    def test_exit_code_mapping(
        self, error_class: type[BookForgeError], expected_exit_code: int
    ) -> None:
        err = error_class("message test")
        assert err.exit_code == expected_exit_code

    @pytest.mark.parametrize(
        "error_class",
        [InputError, RenderError, LLMError],
    )
    def test_inherits_from_bookforge_error(
        self, error_class: type[BookForgeError]
    ) -> None:
        err = error_class("message")
        assert isinstance(err, BookForgeError)
        assert isinstance(err, Exception)

    @pytest.mark.parametrize(
        "error_class",
        [InputError, RenderError, LLMError],
    )
    def test_message_preserved(self, error_class: type[BookForgeError]) -> None:
        msg = "Le fichier 'book.yaml' est invalide"
        err = error_class(msg)
        assert str(err) == msg

    def test_bookforge_error_is_catchable(self) -> None:
        with pytest.raises(BookForgeError):
            raise InputError("erreur test")

    def test_bookforge_error_base_exit_code(self) -> None:
        err = BookForgeError("erreur de base")
        assert err.exit_code == 1
