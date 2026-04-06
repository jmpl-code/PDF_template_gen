"""Tests d'initialisation — verifie que le package bookforge est importable."""


def test_bookforge_is_importable() -> None:
    """Le package bookforge doit etre importable."""
    import bookforge

    assert bookforge is not None


def test_version_exists_and_is_string() -> None:
    """__version__ doit exister et etre une chaine non vide."""
    from bookforge import __version__

    assert isinstance(__version__, str)
    assert len(__version__) > 0


def test_version_format_semver() -> None:
    """__version__ doit suivre le format semver X.Y.Z."""
    from bookforge import __version__

    parts = __version__.split(".")
    assert len(parts) == 3
    for part in parts:
        assert part.isdigit()
