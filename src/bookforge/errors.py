"""Hierarchie d'erreurs BookForge."""


class BookForgeError(Exception):
    """Erreur de base BookForge."""

    exit_code: int = 1

    def __init__(self, message: str) -> None:
        super().__init__(message)


class InputError(BookForgeError):
    """Erreur d'entree utilisateur (config invalide, fichier manquant)."""

    exit_code: int = 1


class RenderError(BookForgeError):
    """Erreur de rendu (subprocess, template)."""

    exit_code: int = 2


class LLMError(BookForgeError):
    """Erreur LLM (API, timeout)."""

    exit_code: int = 3
