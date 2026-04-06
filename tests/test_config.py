"""Tests pour le parsing et la validation de book.yaml (Story 2.1)."""

from pathlib import Path

import pytest

from bookforge.config import BookConfig, ChapterConfig, load_book_config
from bookforge.errors import InputError

FIXTURES = Path(__file__).parent / "fixtures" / "books"


class TestLoadBookConfigValid:
    """Tests avec des configurations valides."""

    def test_config_valid_book_yaml_returns_book_config(self) -> None:
        config = load_book_config(FIXTURES / "minimal" / "book.yaml")
        assert isinstance(config, BookConfig)
        assert config.titre == "Mon Livre Business"
        assert config.sous_titre == "Un guide pratique"
        assert config.auteur == "JM"
        assert config.genre == "business"
        assert len(config.chapitres) == 1
        assert isinstance(config.chapitres[0], ChapterConfig)
        assert config.chapitres[0].titre == "Introduction"
        assert config.chapitres[0].fichier == "chapitres/01-introduction.md"

    def test_config_optional_fields_default_none(self) -> None:
        config = load_book_config(FIXTURES / "minimal" / "book.yaml")
        assert config.isbn is None
        assert config.dedicace is None

    def test_config_chapter_paths_resolved_relative_to_yaml(self) -> None:
        config = load_book_config(FIXTURES / "minimal" / "book.yaml")
        book_dir = FIXTURES / "minimal"
        chap_path = book_dir / config.chapitres[0].fichier
        assert chap_path.exists()


class TestLoadBookConfigErrors:
    """Tests avec des configurations invalides."""

    def test_config_missing_required_field_raises_input_error(self) -> None:
        with pytest.raises(InputError, match="titre"):
            load_book_config(FIXTURES / "broken" / "missing-title.yaml")

    def test_config_missing_chapters_raises_input_error(self) -> None:
        with pytest.raises(InputError, match="chapitres"):
            load_book_config(FIXTURES / "broken" / "missing-chapters.yaml")

    def test_config_missing_chapter_file_raises_input_error(self) -> None:
        with pytest.raises(InputError, match="inexistant.md"):
            load_book_config(FIXTURES / "broken" / "missing-file-ref.yaml")

    def test_config_file_not_found_raises_input_error(self) -> None:
        with pytest.raises(InputError, match="introuvable"):
            load_book_config(FIXTURES / "nonexistent" / "book.yaml")

    def test_config_empty_chapitres_raises_input_error(self, tmp_path: Path) -> None:
        yaml_file = tmp_path / "book.yaml"
        yaml_file.write_text(
            'titre: "Test"\nauteur: "A"\ngenre: "b"\nchapitres: []\n',
            encoding="utf-8",
        )
        with pytest.raises(InputError, match="chapitres"):
            load_book_config(yaml_file)
