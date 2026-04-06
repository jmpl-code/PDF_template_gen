"""Tests d'importabilite de tous les packages BookForge."""

import importlib

import pytest

PACKAGES = [
    "bookforge",
    "bookforge.config",
    "bookforge.parser",
    "bookforge.ast_nodes",
    "bookforge.tokens",
    "bookforge.passes",
    "bookforge.renderers",
    "bookforge.quality",
    "bookforge.judge",
]


@pytest.mark.parametrize("package", PACKAGES)
def test_package_is_importable(package: str) -> None:
    """Chaque package doit etre importable sans erreur."""
    mod = importlib.import_module(package)
    assert mod is not None


def test_errors_importable() -> None:
    """Les classes d'erreurs sont importables depuis bookforge.errors."""
    from bookforge.errors import BookForgeError, InputError, LLMError, RenderError

    assert BookForgeError is not None
    assert InputError is not None
    assert RenderError is not None
    assert LLMError is not None


def test_run_external_importable() -> None:
    """run_external est importable depuis bookforge.external."""
    from bookforge.external import run_external

    assert callable(run_external)
