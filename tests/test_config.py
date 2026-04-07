"""Tests pour le parsing et la validation de book.yaml (Stories 2.1, 4.2)."""

from pathlib import Path

import pytest
from pydantic import ValidationError

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


class TestBookConfigDocumentClass:
    """Tests du champ document_class (Story 4.2)."""

    _BASE: dict[str, object] = {
        "titre": "T",
        "auteur": "A",
        "genre": "g",
        "chapitres": [{"titre": "c", "fichier": "f"}],
    }

    def test_book_config_with_class_alias(self) -> None:
        """BookConfig accepte le champ 'class' comme alias de document_class."""
        config = BookConfig(**{**self._BASE, "class": "business-manual"})
        assert config.document_class == "business-manual"

    def test_book_config_default_class(self) -> None:
        """Sans champ class, document_class vaut 'business-manual'."""
        config = BookConfig(**self._BASE)
        assert config.document_class == "business-manual"

    def test_book_config_custom_class(self) -> None:
        """BookConfig accepte une classe custom en kebab-case."""
        config = BookConfig(**{**self._BASE, "class": "fiction-novel"})
        assert config.document_class == "fiction-novel"

    def test_book_config_class_validation_rejects_uppercase(self) -> None:
        """Noms de classe avec majuscules sont rejetes."""
        with pytest.raises(ValidationError, match="string_pattern_mismatch"):
            BookConfig(**{**self._BASE, "class": "Business-Manual"})

    def test_book_config_class_validation_rejects_spaces(self) -> None:
        """Noms de classe avec espaces sont rejetes."""
        with pytest.raises(ValidationError, match="string_pattern_mismatch"):
            BookConfig(**{**self._BASE, "class": "business manual"})

    def test_book_config_class_validation_rejects_special_chars(self) -> None:
        """Noms de classe avec caracteres speciaux sont rejetes."""
        with pytest.raises(ValidationError, match="string_pattern_mismatch"):
            BookConfig(**{**self._BASE, "class": "business_manual!"})

    def test_book_config_with_tokens_path(self) -> None:
        """BookConfig accepte un chemin tokens optionnel."""
        config = BookConfig(**{**self._BASE, "tokens": "custom-tokens.yaml"})
        assert config.tokens == "custom-tokens.yaml"

    def test_book_config_tokens_default_none(self) -> None:
        """Sans champ tokens, la valeur est None."""
        config = BookConfig(**self._BASE)
        assert config.tokens is None
