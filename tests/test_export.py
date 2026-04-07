"""Tests pour l'export metadonnees KDP et l'organisation du dossier de sortie (Story 2.8)."""

from __future__ import annotations

import json
from pathlib import Path

from bookforge.config.schema import BookConfig, ChapterConfig
from bookforge.export import export_metadata_kdp, organize_output


def _make_config(**overrides: object) -> BookConfig:
    """Cree un BookConfig avec des valeurs par defaut pour les tests."""
    defaults: dict[str, object] = {
        "titre": "Mon Livre Business",
        "sous_titre": "Un guide pratique",
        "auteur": "JM",
        "genre": "business",
        "description": "Un livre sur le business moderne",
        "mots_cles": ["business", "guide", "productivite"],
        "categories": ["Business & Economie", "Management"],
        "chapitres": [ChapterConfig(titre="Ch1", fichier="ch1.md")],
    }
    defaults.update(overrides)
    return BookConfig(**defaults)  # type: ignore[arg-type]


class TestExportMetadataKdp:
    """Tests pour export_metadata_kdp()."""

    def test_metadata_kdp_contains_all_fields(self, tmp_path: Path) -> None:
        config = _make_config()
        result = export_metadata_kdp(config, tmp_path)
        data = json.loads(result.read_text(encoding="utf-8"))
        assert data["titre"] == "Mon Livre Business"
        assert data["auteur"] == "JM"
        assert data["sous_titre"] == "Un guide pratique"
        assert data["description"] == "Un livre sur le business moderne"
        assert data["mots_cles"] == ["business", "guide", "productivite"]
        assert data["categories"] == ["Business & Economie", "Management"]
        assert data["isbn"] is None
        assert data["genre"] == "business"

    def test_metadata_kdp_optional_fields_null(self, tmp_path: Path) -> None:
        config = _make_config(
            description=None,
            mots_cles=None,
            categories=None,
            sous_titre=None,
            isbn=None,
        )
        result = export_metadata_kdp(config, tmp_path)
        data = json.loads(result.read_text(encoding="utf-8"))
        assert data["description"] is None
        assert data["mots_cles"] is None
        assert data["categories"] is None
        assert data["sous_titre"] is None
        assert data["isbn"] is None

    def test_metadata_kdp_utf8_encoding(self, tmp_path: Path) -> None:
        config = _make_config(
            titre="L'Art de la Strategie",
            auteur="Jean-Pierre Lefevre",
            description="Guide complet sur les strategies d'entreprise a l'ere numerique",
            mots_cles=["strategie", "economie", "numerique"],
        )
        result = export_metadata_kdp(config, tmp_path)
        raw = result.read_text(encoding="utf-8")
        assert "L'Art de la Strategie" in raw
        assert "Jean-Pierre Lefevre" in raw
        assert "l'ere numerique" in raw
        data = json.loads(raw)
        assert data["titre"] == "L'Art de la Strategie"

    def test_metadata_kdp_deterministic(self, tmp_path: Path) -> None:
        config = _make_config()
        dir1 = tmp_path / "run1"
        dir2 = tmp_path / "run2"
        result1 = export_metadata_kdp(config, dir1)
        result2 = export_metadata_kdp(config, dir2)
        assert result1.read_text(encoding="utf-8") == result2.read_text(encoding="utf-8")

    def test_metadata_kdp_json_valid(self, tmp_path: Path) -> None:
        config = _make_config()
        result = export_metadata_kdp(config, tmp_path)
        raw = result.read_text(encoding="utf-8")
        data = json.loads(raw)
        assert isinstance(data, dict)
        expected_keys = {
            "titre",
            "auteur",
            "sous_titre",
            "description",
            "mots_cles",
            "categories",
            "isbn",
            "genre",
        }
        assert set(data.keys()) == expected_keys

    def test_metadata_kdp_creates_directory(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "nested" / "output"
        config = _make_config()
        result = export_metadata_kdp(config, output_dir)
        assert result.exists()
        assert output_dir.is_dir()

    def test_metadata_kdp_filename(self, tmp_path: Path) -> None:
        config = _make_config()
        result = export_metadata_kdp(config, tmp_path)
        assert result.name == "metadata-kdp.json"


class TestOrganizeOutput:
    """Tests pour organize_output()."""

    def _create_fake_pdfs(self, tmp_path: Path) -> tuple[Path, Path]:
        """Cree des faux PDF pour les tests."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        interior = build_dir / "livre-interieur.pdf"
        interior.write_bytes(b"%PDF-1.4 interior content")
        cover = build_dir / "couverture.pdf"
        cover.write_bytes(b"%PDF-1.4 cover content")
        return interior, cover

    def test_organize_output_creates_directory(self, tmp_path: Path) -> None:
        interior, cover = self._create_fake_pdfs(tmp_path)
        output_dir = tmp_path / "new_output"
        organize_output(_make_config(), interior, cover, output_dir)
        assert output_dir.is_dir()

    def test_organize_output_contains_expected_files(self, tmp_path: Path) -> None:
        interior, cover = self._create_fake_pdfs(tmp_path)
        output_dir = tmp_path / "output"
        organize_output(_make_config(), interior, cover, output_dir)
        assert (output_dir / "livre-interieur.pdf").exists()
        assert (output_dir / "couverture.pdf").exists()
        assert (output_dir / "metadata-kdp.json").exists()

    def test_organize_output_overwrites_existing(self, tmp_path: Path) -> None:
        interior, cover = self._create_fake_pdfs(tmp_path)
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        (output_dir / "metadata-kdp.json").write_text("old content", encoding="utf-8")
        (output_dir / "livre-interieur.pdf").write_bytes(b"old pdf")
        organize_output(_make_config(), interior, cover, output_dir)
        assert (output_dir / "livre-interieur.pdf").read_bytes() == b"%PDF-1.4 interior content"
        data = json.loads((output_dir / "metadata-kdp.json").read_text(encoding="utf-8"))
        assert data["titre"] == "Mon Livre Business"

    def test_organize_output_preserves_source_files(self, tmp_path: Path) -> None:
        interior, cover = self._create_fake_pdfs(tmp_path)
        output_dir = tmp_path / "output"
        organize_output(_make_config(), interior, cover, output_dir)
        assert interior.exists()
        assert cover.exists()

    def test_organize_output_without_epub_no_epub_file(self, tmp_path: Path) -> None:
        """organize_output sans epub_path ne cree pas de livre.epub (retro-compatibilite)."""
        interior, cover = self._create_fake_pdfs(tmp_path)
        output_dir = tmp_path / "output"
        organize_output(_make_config(), interior, cover, output_dir)
        assert not (output_dir / "livre.epub").exists()

    def test_organize_output_with_epub_copies_epub(self, tmp_path: Path) -> None:
        """organize_output avec epub_path copie le fichier EPUB dans le dossier de sortie."""
        interior, cover = self._create_fake_pdfs(tmp_path)
        build_dir = tmp_path / "build"
        epub = build_dir / "livre.epub"
        epub.write_bytes(b"PK fake epub content")
        output_dir = tmp_path / "output"
        organize_output(_make_config(), interior, cover, output_dir, epub_path=epub)
        assert (output_dir / "livre.epub").exists()
        assert (output_dir / "livre.epub").read_bytes() == b"PK fake epub content"
        assert (output_dir / "livre-interieur.pdf").exists()
        assert (output_dir / "couverture.pdf").exists()
        assert (output_dir / "metadata-kdp.json").exists()
