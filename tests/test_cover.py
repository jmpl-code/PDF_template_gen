"""Tests pour le renderer de couverture (Story 2.7)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from bookforge.config.schema import BookConfig, ChapterConfig
from bookforge.errors import RenderError
from bookforge.renderers.cover import generate_cover_typst, render_cover


@pytest.fixture()
def config_with_subtitle() -> BookConfig:
    return BookConfig(
        titre="Mon Livre Business",
        sous_titre="Un guide pratique",
        auteur="JM",
        genre="business",
        chapitres=[ChapterConfig(titre="Ch1", fichier="ch1.md")],
    )


@pytest.fixture()
def config_without_subtitle() -> BookConfig:
    return BookConfig(
        titre="Mon Livre",
        auteur="JM",
        genre="business",
        chapitres=[ChapterConfig(titre="Ch1", fichier="ch1.md")],
    )


class TestGenerateCoverTypst:
    """Tests pour la generation du fichier .typ de couverture."""

    def test_cover_generates_typ_file(
        self, config_with_subtitle: BookConfig, tmp_path: Path
    ) -> None:
        typ_path = tmp_path / "couverture.typ"
        result = generate_cover_typst(config_with_subtitle, typ_path)
        assert result == typ_path
        assert typ_path.exists()
        assert typ_path.read_text(encoding="utf-8").strip() != ""

    def test_cover_title_in_typ(self, config_with_subtitle: BookConfig, tmp_path: Path) -> None:
        typ_path = tmp_path / "couverture.typ"
        generate_cover_typst(config_with_subtitle, typ_path)
        content = typ_path.read_text(encoding="utf-8")
        assert "Mon Livre Business" in content

    def test_cover_subtitle_present_when_defined(
        self, config_with_subtitle: BookConfig, tmp_path: Path
    ) -> None:
        typ_path = tmp_path / "couverture.typ"
        generate_cover_typst(config_with_subtitle, typ_path)
        content = typ_path.read_text(encoding="utf-8")
        assert "Un guide pratique" in content
        assert "size: 20pt" in content

    def test_cover_subtitle_absent_when_none(
        self, config_without_subtitle: BookConfig, tmp_path: Path
    ) -> None:
        typ_path = tmp_path / "couverture.typ"
        generate_cover_typst(config_without_subtitle, typ_path)
        content = typ_path.read_text(encoding="utf-8")
        assert "size: 20pt" not in content

    def test_cover_author_in_typ(self, config_with_subtitle: BookConfig, tmp_path: Path) -> None:
        typ_path = tmp_path / "couverture.typ"
        generate_cover_typst(config_with_subtitle, typ_path)
        content = typ_path.read_text(encoding="utf-8")
        assert "JM" in content
        assert "size: 18pt" in content

    def test_cover_special_chars_escaped(self, tmp_path: Path) -> None:
        config = BookConfig(
            titre="Titre #1 $pecial @uteur",
            sous_titre="Sous <titre> & *details*",
            auteur="L'auteur #2",
            genre="test",
            chapitres=[ChapterConfig(titre="Ch1", fichier="ch1.md")],
        )
        typ_path = tmp_path / "couverture.typ"
        generate_cover_typst(config, typ_path)
        content = typ_path.read_text(encoding="utf-8")
        assert "\\#1" in content
        assert "\\$pecial" in content
        assert "\\@uteur" in content
        assert "\\<titre\\>" in content
        assert "\\*details\\*" in content
        assert "\\#2" in content

    def test_cover_deterministic_output(
        self, config_with_subtitle: BookConfig, tmp_path: Path
    ) -> None:
        path1 = tmp_path / "cover1.typ"
        path2 = tmp_path / "cover2.typ"
        generate_cover_typst(config_with_subtitle, path1)
        generate_cover_typst(config_with_subtitle, path2)
        assert path1.read_text(encoding="utf-8") == path2.read_text(encoding="utf-8")


class TestRenderCover:
    """Tests pour le point d'entree render_cover (integration)."""

    def test_cover_typst_not_found_raises_render_error(
        self, config_with_subtitle: BookConfig, tmp_path: Path
    ) -> None:
        with patch(
            "bookforge.renderers.cover.run_external",
            side_effect=RenderError(
                "Compilation couverture Typst vers PDF: commande 'typst' introuvable"
            ),
        ):
            with pytest.raises(RenderError, match="typst"):
                render_cover(config_with_subtitle, tmp_path)

    def test_cover_output_path_correct(
        self, config_with_subtitle: BookConfig, tmp_path: Path
    ) -> None:
        with patch("bookforge.renderers.cover.run_external"):
            result = render_cover(config_with_subtitle, tmp_path)
            assert result == tmp_path / "couverture.pdf"
            assert (tmp_path / "couverture.typ").exists()
