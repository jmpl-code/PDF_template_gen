"""Tests du renderer PDF Typst (Stories 2.3, 2.4, 2.5)."""

import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

from bookforge.ast_nodes import (
    BookNode,
    ChapterNode,
    HeadingNode,
    ImageNode,
    ParagraphNode,
    TableNode,
)
from bookforge.config.schema import BookConfig, ChapterConfig
from bookforge.errors import RenderError
from bookforge.renderers.pdf import (
    compile_typst,
    escape_typst,
    generate_typst,
    render_pdf,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"
GOLDEN_DIR = FIXTURES_DIR / "golden"
MINIMAL_DIR = FIXTURES_DIR / "books" / "minimal"

# --- Helpers ---


def _make_book(tmp_path: Path) -> BookNode:
    """Cree un BookNode minimal avec image copiee dans tmp_path."""
    # Copier l'image dans tmp_path pour que le chemin soit relatif
    images_dir = tmp_path / "images"
    images_dir.mkdir(exist_ok=True)
    src_img = MINIMAL_DIR / "images" / "diagram.png"
    dest_img = images_dir / "diagram.png"
    if not dest_img.exists():
        shutil.copy2(src_img, dest_img)

    source = MINIMAL_DIR / "chapitres" / "01-introduction.md"
    return BookNode(
        title="Mon Livre Business",
        chapters=(
            ChapterNode(
                title="Introduction",
                children=(
                    HeadingNode(
                        level=1,
                        text="Introduction",
                        source_file=source,
                        line_number=1,
                    ),
                    ParagraphNode(
                        text="Ceci est le contenu du premier chapitre.",
                        source_file=source,
                        line_number=3,
                    ),
                    HeadingNode(
                        level=2,
                        text="Section 1",
                        source_file=source,
                        line_number=5,
                    ),
                    ParagraphNode(
                        text="Un paragraphe avec du texte explicatif.",
                        source_file=source,
                        line_number=7,
                    ),
                    ImageNode(
                        src=dest_img,
                        alt="Diagramme exemple",
                        source_file=source,
                        line_number=9,
                    ),
                    TableNode(
                        headers=("Colonne A", "Colonne B"),
                        rows=(
                            ("valeur 1", "valeur 2"),
                            ("valeur 3", "valeur 4"),
                        ),
                        source_file=source,
                        line_number=11,
                    ),
                ),
                source_file=source,
                line_number=1,
            ),
        ),
        source_file=MINIMAL_DIR / "book.yaml",
        line_number=1,
    )


def _make_book_in(output_dir: Path) -> BookNode:
    """Cree un BookNode avec image dans output_dir (pour render_pdf)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    images_dir = output_dir / "images"
    images_dir.mkdir(exist_ok=True)
    src_img = MINIMAL_DIR / "images" / "diagram.png"
    dest_img = images_dir / "diagram.png"
    if not dest_img.exists():
        shutil.copy2(src_img, dest_img)

    source = MINIMAL_DIR / "chapitres" / "01-introduction.md"
    return BookNode(
        title="Mon Livre Business",
        chapters=(
            ChapterNode(
                title="Introduction",
                children=(
                    HeadingNode(
                        level=1,
                        text="Introduction",
                        source_file=source,
                        line_number=1,
                    ),
                    ParagraphNode(
                        text="Hello world",
                        source_file=source,
                        line_number=3,
                    ),
                    ImageNode(
                        src=dest_img,
                        alt="Diagramme",
                        source_file=source,
                        line_number=5,
                    ),
                ),
                source_file=source,
                line_number=1,
            ),
        ),
        source_file=MINIMAL_DIR / "book.yaml",
        line_number=1,
    )


def _make_config(
    *,
    dedicace: str | None = None,
    sous_titre: str | None = "Un sous-titre",
    isbn: str | None = "978-2-1234-5678-0",
) -> BookConfig:
    """Cree un BookConfig minimal pour les tests."""
    return BookConfig(
        titre="Mon Livre Business",
        sous_titre=sous_titre,
        auteur="Jean Dupont",
        genre="business",
        isbn=isbn,
        dedicace=dedicace,
        chapitres=[
            ChapterConfig(titre="Introduction", fichier="01-introduction.md"),
        ],
    )


# --- Tests escape_typst ---


class TestEscapeTypst:
    """Tests de la fonction d'echappement Typst."""

    def test_escape_typst_hash(self) -> None:
        assert escape_typst("prix #1") == "prix \\#1"

    def test_escape_typst_dollar(self) -> None:
        assert escape_typst("coût $5") == "coût \\$5"

    def test_escape_typst_at(self) -> None:
        assert escape_typst("ref @label") == "ref \\@label"

    def test_escape_typst_angle_brackets(self) -> None:
        assert escape_typst("<tag>") == "\\<tag\\>"

    def test_escape_typst_backtick(self) -> None:
        assert escape_typst("`code`") == "\\`code\\`"

    def test_escape_typst_underscore_star(self) -> None:
        result = escape_typst("_italic_ et *bold*")
        assert result == "\\_italic\\_ et \\*bold\\*"

    def test_escape_typst_tilde(self) -> None:
        assert escape_typst("a~b") == "a\\~b"

    def test_escape_typst_backslash(self) -> None:
        assert escape_typst("a\\b") == "a\\\\b"

    def test_escape_typst_plain_text_unchanged(self) -> None:
        text = "Texte normal sans caractères spéciaux."
        assert escape_typst(text) == text

    def test_escape_typst_multiple_specials(self) -> None:
        assert escape_typst("#$@") == "\\#\\$\\@"


# --- Tests generate_typst ---


class TestGenerateTypst:
    """Tests de la generation du fichier .typ."""

    def test_generate_typst_valid_ast_produces_typ_file(
        self,
        tmp_path: Path,
    ) -> None:
        book = _make_book(tmp_path)
        typ_path = tmp_path / "output.typ"
        result = generate_typst(book, typ_path)
        assert result == typ_path
        assert typ_path.exists()
        content = typ_path.read_text(encoding="utf-8")
        assert len(content) > 0

    def test_generate_typst_contains_template_preamble(
        self,
        tmp_path: Path,
    ) -> None:
        book = _make_book(tmp_path)
        typ_path = tmp_path / "output.typ"
        generate_typst(book, typ_path)
        content = typ_path.read_text(encoding="utf-8")
        assert "#set page(" in content
        assert "#set text(" in content
        assert "#set par(" in content
        assert "// --- BEGIN CONTENT ---" in content

    def test_generate_typst_all_node_types_rendered(
        self,
        tmp_path: Path,
    ) -> None:
        book = _make_book(tmp_path)
        typ_path = tmp_path / "output.typ"
        generate_typst(book, typ_path)
        content = typ_path.read_text(encoding="utf-8")
        # HeadingNode level 1
        assert "= Introduction" in content
        # HeadingNode level 2
        assert "== Section 1" in content
        # ParagraphNode
        assert "Ceci est le contenu du premier chapitre." in content
        assert "Un paragraphe avec du texte explicatif." in content
        # ImageNode (Story 2.6: figure + block)
        assert 'image("' in content
        assert "diagram.png" in content
        # TableNode
        assert "#table(" in content
        assert "Colonne A" in content
        assert "valeur 1" in content

    def test_generate_typst_no_duplicate_chapter_title(
        self,
        tmp_path: Path,
    ) -> None:
        """C1 fix: le titre chapitre ne doit pas etre duplique."""
        book = _make_book(tmp_path)
        typ_path = tmp_path / "output.typ"
        generate_typst(book, typ_path)
        content = typ_path.read_text(encoding="utf-8")
        # "= Introduction" ne doit apparaitre qu'une seule fois
        count = content.count("= Introduction\n")
        assert count == 1, f"Titre duplique: {count} occurrences"

    def test_generate_typst_escapes_special_characters(
        self,
        tmp_path: Path,
    ) -> None:
        source = MINIMAL_DIR / "chapitres" / "01-introduction.md"
        book = BookNode(
            title="Test",
            chapters=(
                ChapterNode(
                    title="Chapitre",
                    children=(
                        ParagraphNode(
                            text="prix #1 et coût $5",
                            source_file=source,
                            line_number=1,
                        ),
                    ),
                    source_file=source,
                    line_number=1,
                ),
            ),
            source_file=source,
            line_number=1,
        )
        typ_path = tmp_path / "output.typ"
        generate_typst(book, typ_path)
        content = typ_path.read_text(encoding="utf-8")
        assert "prix \\#1 et coût \\$5" in content

    def test_generate_typst_deterministic_output(
        self,
        tmp_path: Path,
    ) -> None:
        book = _make_book(tmp_path)
        typ1 = tmp_path / "output1.typ"
        typ2 = tmp_path / "output2.typ"
        generate_typst(book, typ1)
        generate_typst(book, typ2)
        assert typ1.read_text(encoding="utf-8") == typ2.read_text(
            encoding="utf-8",
        )

    def test_generate_typst_content_matches_golden_file(
        self,
        tmp_path: Path,
    ) -> None:
        book = _make_book(tmp_path)
        typ_path = tmp_path / "output.typ"
        generate_typst(book, typ_path)
        actual = typ_path.read_text(encoding="utf-8")

        golden_path = GOLDEN_DIR / "minimal.typ"
        if not golden_path.exists():
            pytest.skip("Golden file minimal.typ not yet created")

        golden = golden_path.read_text(encoding="utf-8")
        # Les chemins images varient — on compare tout sauf ces lignes
        actual_lines = [line for line in actual.splitlines() if 'image("' not in line]
        golden_lines = [line for line in golden.splitlines() if 'image("' not in line]
        assert actual_lines == golden_lines

    def test_generate_typst_chapter_pagebreak(
        self,
        tmp_path: Path,
    ) -> None:
        source = MINIMAL_DIR / "chapitres" / "01-introduction.md"
        book = BookNode(
            title="Test",
            chapters=(
                ChapterNode(
                    title="Chapitre 1",
                    children=(
                        HeadingNode(
                            level=1,
                            text="Chapitre 1",
                            source_file=source,
                            line_number=1,
                        ),
                    ),
                    source_file=source,
                    line_number=1,
                ),
                ChapterNode(
                    title="Chapitre 2",
                    children=(
                        HeadingNode(
                            level=1,
                            text="Chapitre 2",
                            source_file=source,
                            line_number=1,
                        ),
                    ),
                    source_file=source,
                    line_number=1,
                ),
            ),
            source_file=source,
            line_number=1,
        )
        typ_path = tmp_path / "output.typ"
        generate_typst(book, typ_path)
        content = typ_path.read_text(encoding="utf-8")
        first_pos = content.index("= Chapitre 1")
        before_first = content[:first_pos]
        assert "#pagebreak()" not in before_first
        assert "#pagebreak()" in content
        second_pos = content.index("= Chapitre 2")
        before_second = content[first_pos:second_pos]
        assert "#pagebreak()" in before_second

    def test_generate_typst_image_outside_dir_raises_error(
        self,
        tmp_path: Path,
    ) -> None:
        """C2 fix: image hors du repertoire .typ leve RenderError."""
        source = MINIMAL_DIR / "chapitres" / "01-introduction.md"
        # Image dans un autre repertoire que le .typ
        other_dir = tmp_path / "other"
        other_dir.mkdir()
        foreign_img = other_dir / "img.png"
        foreign_img.write_bytes(b"\x89PNG")

        book = BookNode(
            title="Test",
            chapters=(
                ChapterNode(
                    title="Ch",
                    children=(
                        ImageNode(
                            src=foreign_img,
                            alt="test",
                            source_file=source,
                            line_number=1,
                        ),
                    ),
                    source_file=source,
                    line_number=1,
                ),
            ),
            source_file=source,
            line_number=1,
        )
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        typ_path = output_dir / "book.typ"
        with pytest.raises(RenderError, match="hors du repertoire"):
            generate_typst(book, typ_path)


# --- Tests compile_typst ---


class TestCompileTypst:
    """Tests de la compilation Typst."""

    def test_compile_typst_missing_binary_raises_render_error(
        self,
        tmp_path: Path,
    ) -> None:
        typ_path = tmp_path / "test.typ"
        typ_path.write_text("Hello", encoding="utf-8")
        pdf_path = tmp_path / "test.pdf"
        err = RenderError(
            "Compilation Typst vers PDF: commande 'typst' introuvable",
        )
        with patch(
            "bookforge.renderers.pdf.run_external",
            side_effect=err,
        ):
            with pytest.raises(
                RenderError,
                match="commande 'typst' introuvable",
            ):
                compile_typst(typ_path, pdf_path)

    @pytest.mark.skipif(
        shutil.which("typst") is None,
        reason="Typst non installe",
    )
    def test_compile_typst_produces_pdf(self, tmp_path: Path) -> None:
        typ_path = tmp_path / "test.typ"
        typ_path.write_text(
            "#set page(width: 6in, height: 9in)\nHello World\n",
            encoding="utf-8",
        )
        pdf_path = tmp_path / "test.pdf"
        result = compile_typst(typ_path, pdf_path)
        assert result == pdf_path
        assert pdf_path.exists()
        pdf_bytes = pdf_path.read_bytes()
        assert pdf_bytes[:5] == b"%PDF-"


# --- Tests render_pdf (integration) ---


class TestRenderPdf:
    """Tests d'integration du renderer PDF complet."""

    def test_render_pdf_preserves_intermediate_file(
        self,
        tmp_path: Path,
    ) -> None:
        output_dir = tmp_path / "output"
        book = _make_book_in(output_dir)
        with patch(
            "bookforge.renderers.pdf.compile_typst",
        ) as mock_compile:
            mock_compile.return_value = output_dir / "livre-interieur.pdf"
            render_pdf(book, output_dir)
        typ_path = output_dir / "livre-interieur.typ"
        assert typ_path.exists()

    def test_render_pdf_creates_output_dir(
        self,
        tmp_path: Path,
    ) -> None:
        output_dir = tmp_path / "new" / "output"
        assert not output_dir.exists()
        book = _make_book_in(output_dir)
        with patch(
            "bookforge.renderers.pdf.compile_typst",
        ) as mock_compile:
            mock_compile.return_value = output_dir / "livre-interieur.pdf"
            render_pdf(book, output_dir)
        assert output_dir.exists()

    @pytest.mark.skipif(
        shutil.which("typst") is None,
        reason="Typst non installe",
    )
    def test_render_pdf_produces_valid_pdf(
        self,
        tmp_path: Path,
    ) -> None:
        output_dir = tmp_path / "output"
        images_dir = output_dir / "images"
        images_dir.mkdir(parents=True)
        src_img = MINIMAL_DIR / "images" / "diagram.png"
        dest_img = images_dir / "diagram.png"
        shutil.copy2(src_img, dest_img)

        source = MINIMAL_DIR / "chapitres" / "01-introduction.md"
        book = BookNode(
            title="Test PDF",
            chapters=(
                ChapterNode(
                    title="Introduction",
                    children=(
                        HeadingNode(
                            level=1,
                            text="Introduction",
                            source_file=source,
                            line_number=1,
                        ),
                        ParagraphNode(
                            text="Hello world",
                            source_file=source,
                            line_number=2,
                        ),
                        ImageNode(
                            src=dest_img,
                            alt="test",
                            source_file=source,
                            line_number=3,
                        ),
                    ),
                    source_file=source,
                    line_number=1,
                ),
            ),
            source_file=source,
            line_number=1,
        )
        result = render_pdf(book, output_dir)
        assert result.exists()
        assert result.name == "livre-interieur.pdf"
        pdf_bytes = result.read_bytes()
        assert pdf_bytes[:5] == b"%PDF-"
        assert (output_dir / "livre-interieur.typ").exists()


# --- Tests pages liminaires et TDM (Story 2.4) ---


class TestFrontMatter:
    """Tests des pages liminaires et de la table des matieres."""

    def test_generate_typst_includes_title_page(
        self,
        tmp_path: Path,
    ) -> None:
        """AC #2 : la page de titre contient titre et auteur."""
        book = _make_book(tmp_path)
        config = _make_config()
        typ_path = tmp_path / "output.typ"
        generate_typst(book, typ_path, config=config)
        content = typ_path.read_text(encoding="utf-8")
        assert "Mon Livre Business" in content
        assert "Jean Dupont" in content
        assert 'size: 28pt, weight: "bold"' in content

    def test_generate_typst_includes_subtitle(
        self,
        tmp_path: Path,
    ) -> None:
        """AC #2 : le sous-titre est affiche si present."""
        book = _make_book(tmp_path)
        config = _make_config(sous_titre="Sous-titre Test")
        typ_path = tmp_path / "output.typ"
        generate_typst(book, typ_path, config=config)
        content = typ_path.read_text(encoding="utf-8")
        assert "Sous-titre Test" in content

    def test_generate_typst_no_subtitle_when_none(
        self,
        tmp_path: Path,
    ) -> None:
        """Pas de sous-titre si non configure."""
        book = _make_book(tmp_path)
        config = _make_config(sous_titre=None)
        typ_path = tmp_path / "output.typ"
        generate_typst(book, typ_path, config=config)
        content = typ_path.read_text(encoding="utf-8")
        # Le #text(size: 18pt) du sous-titre ne doit pas etre present
        # (size: 18pt apparait dans les headings h2, on verifie le contexte)
        assert "#text(size: 18pt)[" not in content

    def test_generate_typst_includes_copyright_page(
        self,
        tmp_path: Path,
    ) -> None:
        """AC #2 : la page de copyright est presente."""
        book = _make_book(tmp_path)
        config = _make_config()
        typ_path = tmp_path / "output.typ"
        generate_typst(book, typ_path, config=config)
        content = typ_path.read_text(encoding="utf-8")
        assert "\\u{00A9}" in content
        assert "Jean Dupont" in content
        assert "Tous droits reserves" in content
        assert "978-2-1234-5678-0" in content

    def test_generate_typst_copyright_no_isbn(
        self,
        tmp_path: Path,
    ) -> None:
        """Copyright sans ISBN si non configure."""
        book = _make_book(tmp_path)
        config = _make_config(isbn=None)
        typ_path = tmp_path / "output.typ"
        generate_typst(book, typ_path, config=config)
        content = typ_path.read_text(encoding="utf-8")
        assert "Tous droits reserves" in content
        assert "ISBN" not in content

    def test_generate_typst_includes_dedication_when_configured(
        self,
        tmp_path: Path,
    ) -> None:
        """AC #3 : dedicace presente si configuree."""
        book = _make_book(tmp_path)
        config = _make_config(dedicace="A ma famille")
        typ_path = tmp_path / "output.typ"
        generate_typst(book, typ_path, config=config)
        content = typ_path.read_text(encoding="utf-8")
        assert "A ma famille" in content
        assert "#emph[" in content

    def test_generate_typst_no_dedication_when_not_configured(
        self,
        tmp_path: Path,
    ) -> None:
        """AC #3 : pas de dedicace si non configuree."""
        book = _make_book(tmp_path)
        config = _make_config(dedicace=None)
        typ_path = tmp_path / "output.typ"
        generate_typst(book, typ_path, config=config)
        content = typ_path.read_text(encoding="utf-8")
        assert "#emph[" not in content

    def test_generate_typst_includes_outline(
        self,
        tmp_path: Path,
    ) -> None:
        """AC #1, #5 : la TDM est presente avec #outline."""
        book = _make_book(tmp_path)
        config = _make_config()
        typ_path = tmp_path / "output.typ"
        generate_typst(book, typ_path, config=config)
        content = typ_path.read_text(encoding="utf-8")
        assert "#outline(indent: auto)" in content
        assert "Table des matieres" in content

    def test_generate_typst_front_matter_order(
        self,
        tmp_path: Path,
    ) -> None:
        """AC #4 : ordre titre < copyright < TDM < contenu."""
        book = _make_book(tmp_path)
        config = _make_config(dedicace="Dedicace test")
        typ_path = tmp_path / "output.typ"
        generate_typst(book, typ_path, config=config)
        content = typ_path.read_text(encoding="utf-8")
        title_pos = content.index('size: 28pt, weight: "bold"')
        copyright_pos = content.index("Tous droits reserves")
        dedication_pos = content.index("Dedicace test")
        toc_pos = content.index("#outline(indent: auto)")
        chapter_pos = content.index("= Introduction")
        assert title_pos < copyright_pos < dedication_pos < toc_pos < chapter_pos

    def test_generate_typst_page_numbering_reset(
        self,
        tmp_path: Path,
    ) -> None:
        """AC #6 : numerotation desactivee pour liminaires, reset avant contenu."""
        book = _make_book(tmp_path)
        config = _make_config()
        typ_path = tmp_path / "output.typ"
        generate_typst(book, typ_path, config=config)
        content = typ_path.read_text(encoding="utf-8")
        assert "#set page(numbering: none)" in content
        assert 'numbering: "1"' in content
        assert "#counter(page).update(1)" in content
        reset_pos = content.index("#counter(page).update(1)")
        chapter_pos = content.index("= Introduction")
        assert reset_pos < chapter_pos

    def test_generate_typst_no_front_matter_without_config(
        self,
        tmp_path: Path,
    ) -> None:
        """Sans config, pas de pages liminaires (retro-compatibilite)."""
        book = _make_book(tmp_path)
        typ_path = tmp_path / "output.typ"
        generate_typst(book, typ_path)
        content = typ_path.read_text(encoding="utf-8")
        assert "#outline(" not in content
        assert "Tous droits reserves" not in content
        assert "#set page(numbering: none)" not in content

    def test_generate_typst_escapes_config_text(
        self,
        tmp_path: Path,
    ) -> None:
        """Le contenu utilisateur dans BookConfig est echappe."""
        book = _make_book(tmp_path)
        config = BookConfig(
            titre="Titre #1 avec $pecial",
            auteur="L'auteur @test",
            genre="business",
            chapitres=[
                ChapterConfig(titre="Ch", fichier="ch.md"),
            ],
        )
        typ_path = tmp_path / "output.typ"
        generate_typst(book, typ_path, config=config)
        content = typ_path.read_text(encoding="utf-8")
        assert "Titre \\#1 avec \\$pecial" in content
        assert "L'auteur \\@test" in content

    def test_render_pdf_with_config_produces_pdf(
        self,
        tmp_path: Path,
    ) -> None:
        """Integration : render_pdf avec config genere un .typ avec front matter."""
        output_dir = tmp_path / "output"
        book = _make_book_in(output_dir)
        config = _make_config()
        with patch(
            "bookforge.renderers.pdf.compile_typst",
        ) as mock_compile:
            mock_compile.return_value = output_dir / "livre-interieur.pdf"
            render_pdf(book, output_dir, config=config)
        typ_path = output_dir / "livre-interieur.typ"
        assert typ_path.exists()
        content = typ_path.read_text(encoding="utf-8")
        assert "#outline(indent: auto)" in content
        assert "Mon Livre Business" in content


# --- Tests pages de garde et en-tetes/pieds de page (Story 2.5) ---


def _make_multi_chapter_book(tmp_path: Path) -> BookNode:
    """Cree un BookNode avec 2 chapitres pour tester les pages de garde."""
    source = MINIMAL_DIR / "chapitres" / "01-introduction.md"
    return BookNode(
        title="Mon Livre Business",
        chapters=(
            ChapterNode(
                title="Introduction",
                children=(
                    HeadingNode(
                        level=1,
                        text="Introduction",
                        source_file=source,
                        line_number=1,
                    ),
                    ParagraphNode(
                        text="Contenu du premier chapitre.",
                        source_file=source,
                        line_number=3,
                    ),
                ),
                source_file=source,
                line_number=1,
            ),
            ChapterNode(
                title="Methode",
                children=(
                    HeadingNode(
                        level=1,
                        text="Methode",
                        source_file=source,
                        line_number=10,
                    ),
                    ParagraphNode(
                        text="Contenu du deuxieme chapitre.",
                        source_file=source,
                        line_number=12,
                    ),
                ),
                source_file=source,
                line_number=10,
            ),
        ),
        source_file=MINIMAL_DIR / "book.yaml",
        line_number=1,
    )


class TestChapterPagesAndHeaders:
    """Tests des pages de garde de chapitre et en-tetes/pieds de page (Story 2.5)."""

    def test_chapter_title_page_generated(
        self,
        tmp_path: Path,
    ) -> None:
        """AC #1 : page de garde avec titre du chapitre."""
        book = _make_multi_chapter_book(tmp_path)
        config = _make_config()
        typ_path = tmp_path / "output.typ"
        generate_typst(book, typ_path, config=config)
        content = typ_path.read_text(encoding="utf-8")
        # Label reel (pas celui dans le query du header)
        assert "] <chapter-start>" in content
        assert "#pagebreak(weak: true)" in content

    def test_chapter_title_page_styling(
        self,
        tmp_path: Path,
    ) -> None:
        """AC #1 : style page de garde -- centree, grande typographie."""
        book = _make_multi_chapter_book(tmp_path)
        config = _make_config()
        typ_path = tmp_path / "output.typ"
        generate_typst(book, typ_path, config=config)
        content = typ_path.read_text(encoding="utf-8")
        assert "#align(center + horizon)" in content
        # Le titre du chapitre dans la page de garde (label reel, pas query)
        ch_start_pos = content.index("] <chapter-start>")
        before_label = content[:ch_start_pos]
        assert 'size: 28pt, weight: "bold"' in before_label
        assert "Introduction" in before_label

    def test_chapter_title_page_each_chapter(
        self,
        tmp_path: Path,
    ) -> None:
        """AC #1 : chaque chapitre a sa propre page de garde."""
        book = _make_multi_chapter_book(tmp_path)
        config = _make_config()
        typ_path = tmp_path / "output.typ"
        generate_typst(book, typ_path, config=config)
        content = typ_path.read_text(encoding="utf-8")
        # Labels reels ("] <chapter-start>") — pas les refs dans query()
        assert content.count("] <chapter-start>") == 2

    def test_running_header_contains_book_title(
        self,
        tmp_path: Path,
    ) -> None:
        """AC #2 : en-tete contient le titre du livre."""
        book = _make_multi_chapter_book(tmp_path)
        config = _make_config()
        typ_path = tmp_path / "output.typ"
        generate_typst(book, typ_path, config=config)
        content = typ_path.read_text(encoding="utf-8")
        assert "header: context {" in content
        assert "Mon Livre Business" in content

    def test_running_header_contains_chapter_title(
        self,
        tmp_path: Path,
    ) -> None:
        """AC #2 : en-tete contient le titre du chapitre courant via query."""
        book = _make_multi_chapter_book(tmp_path)
        config = _make_config()
        typ_path = tmp_path / "output.typ"
        generate_typst(book, typ_path, config=config)
        content = typ_path.read_text(encoding="utf-8")
        assert "selector(heading.where(level: 1)).before(here())" in content
        assert "chapters.last().body" in content

    def test_footer_page_number(
        self,
        tmp_path: Path,
    ) -> None:
        """AC #3 : pied de page avec numero de page centre."""
        book = _make_multi_chapter_book(tmp_path)
        config = _make_config()
        typ_path = tmp_path / "output.typ"
        generate_typst(book, typ_path, config=config)
        content = typ_path.read_text(encoding="utf-8")
        assert "footer: context {" in content
        assert 'counter(page).display("1")' in content

    def test_front_matter_no_header_footer(
        self,
        tmp_path: Path,
    ) -> None:
        """AC #4 : pages liminaires sans en-tetes/pieds de page."""
        book = _make_multi_chapter_book(tmp_path)
        config = _make_config()
        typ_path = tmp_path / "output.typ"
        generate_typst(book, typ_path, config=config)
        content = typ_path.read_text(encoding="utf-8")
        none_pos = content.index("#set page(numbering: none)")
        header_pos = content.index("header: context {")
        assert none_pos < header_pos

    def test_chapter_start_page_no_header(
        self,
        tmp_path: Path,
    ) -> None:
        """AC #5 : page de garde sans en-tete (detection via label)."""
        book = _make_multi_chapter_book(tmp_path)
        config = _make_config()
        typ_path = tmp_path / "output.typ"
        generate_typst(book, typ_path, config=config)
        content = typ_path.read_text(encoding="utf-8")
        assert "query(<chapter-start>)" in content
        assert "is-chapter-start" in content

    def test_multi_chapter_headers_footers(
        self,
        tmp_path: Path,
    ) -> None:
        """Integration : 2 chapitres avec pages de garde, headers et footers."""
        book = _make_multi_chapter_book(tmp_path)
        config = _make_config()
        typ_path = tmp_path / "output.typ"
        generate_typst(book, typ_path, config=config)
        content = typ_path.read_text(encoding="utf-8")

        numbering_none_pos = content.index("#set page(numbering: none)")
        outline_pos = content.index("#outline(indent: auto)")
        header_setup_pos = content.index("header: context {")
        counter_reset_pos = content.index("#counter(page).update(1)")
        first_cs = content.index("] <chapter-start>")
        second_cs = content.index("] <chapter-start>", first_cs + 1)
        h1_intro = content.index("= Introduction")
        h1_methode = content.index("= Methode")

        assert numbering_none_pos < outline_pos
        assert outline_pos < header_setup_pos
        assert header_setup_pos < counter_reset_pos
        assert counter_reset_pos < first_cs
        assert first_cs < h1_intro
        assert h1_intro < second_cs
        assert second_cs < h1_methode

    def test_no_chapter_pages_without_config(
        self,
        tmp_path: Path,
    ) -> None:
        """AC #6 : sans config, pas de pages de garde ni headers (retro-compat)."""
        book = _make_multi_chapter_book(tmp_path)
        typ_path = tmp_path / "output.typ"
        generate_typst(book, typ_path)
        content = typ_path.read_text(encoding="utf-8")
        assert "] <chapter-start>" not in content
        assert "header: context {" not in content
        assert "footer: context {" not in content

    def test_chapter_title_escapes_special_chars(
        self,
        tmp_path: Path,
    ) -> None:
        """Caracteres speciaux dans les titres de chapitre sont echappes."""
        source = MINIMAL_DIR / "chapitres" / "01-introduction.md"
        book = BookNode(
            title="Test",
            chapters=(
                ChapterNode(
                    title="Chapitre #1 avec $pecial",
                    children=(
                        HeadingNode(
                            level=1,
                            text="Chapitre #1 avec $pecial",
                            source_file=source,
                            line_number=1,
                        ),
                    ),
                    source_file=source,
                    line_number=1,
                ),
            ),
            source_file=source,
            line_number=1,
        )
        config = _make_config()
        typ_path = tmp_path / "output.typ"
        generate_typst(book, typ_path, config=config)
        content = typ_path.read_text(encoding="utf-8")
        assert "Chapitre \\#1 avec \\$pecial" in content


# --- Tests integration images et diagrammes (Story 2.6) ---


class TestImageIntegration:
    """Tests de l'integration des images avec figure et protection anti-coupure (Story 2.6)."""

    def test_image_centered_in_figure(
        self,
        tmp_path: Path,
    ) -> None:
        """AC #1 : l'image est rendue via #figure (centre par defaut)."""
        book = _make_book(tmp_path)
        typ_path = tmp_path / "output.typ"
        generate_typst(book, typ_path)
        content = typ_path.read_text(encoding="utf-8")
        assert "#figure(" in content
        assert 'image("' in content

    def test_image_breakable_false(
        self,
        tmp_path: Path,
    ) -> None:
        """AC #3 : protection anti-coupure via #block(breakable: false)."""
        book = _make_book(tmp_path)
        typ_path = tmp_path / "output.typ"
        generate_typst(book, typ_path)
        content = typ_path.read_text(encoding="utf-8")
        assert "#block(breakable: false)[" in content

    def test_image_with_alt_has_caption(
        self,
        tmp_path: Path,
    ) -> None:
        """AC #5 : texte alternatif affiche comme legende."""
        book = _make_book(tmp_path)
        typ_path = tmp_path / "output.typ"
        generate_typst(book, typ_path)
        content = typ_path.read_text(encoding="utf-8")
        assert "caption: [Diagramme exemple]," in content

    def test_image_without_alt_no_caption(
        self,
        tmp_path: Path,
    ) -> None:
        """AC #6 : pas de legende si alt text vide."""
        source = MINIMAL_DIR / "chapitres" / "01-introduction.md"
        images_dir = tmp_path / "images"
        images_dir.mkdir(exist_ok=True)
        src_img = MINIMAL_DIR / "images" / "diagram.png"
        dest_img = images_dir / "diagram.png"
        shutil.copy2(src_img, dest_img)

        book = BookNode(
            title="Test",
            chapters=(
                ChapterNode(
                    title="Ch",
                    children=(
                        ImageNode(
                            src=dest_img,
                            alt="",
                            source_file=source,
                            line_number=1,
                        ),
                    ),
                    source_file=source,
                    line_number=1,
                ),
            ),
            source_file=source,
            line_number=1,
        )
        typ_path = tmp_path / "output.typ"
        generate_typst(book, typ_path)
        content = typ_path.read_text(encoding="utf-8")
        assert "#figure(" in content
        assert "caption:" not in content

    def test_image_width_constraint(
        self,
        tmp_path: Path,
    ) -> None:
        """AC #2 : largeur contrainte a 80% pour tenir dans les marges."""
        book = _make_book(tmp_path)
        typ_path = tmp_path / "output.typ"
        generate_typst(book, typ_path)
        content = typ_path.read_text(encoding="utf-8")
        assert "width: 80%" in content

    def test_image_path_forward_slashes(
        self,
        tmp_path: Path,
    ) -> None:
        """Cross-platform : chemins avec forward slashes dans le Typst genere."""
        book = _make_book(tmp_path)
        typ_path = tmp_path / "output.typ"
        generate_typst(book, typ_path)
        content = typ_path.read_text(encoding="utf-8")
        # Extraire la ligne image et verifier pas de backslash
        for line in content.splitlines():
            if 'image("' in line:
                path_part = line.split('image("')[1].split('"')[0]
                assert "\\" not in path_part

    def test_image_alt_text_escaped(
        self,
        tmp_path: Path,
    ) -> None:
        """Le texte alt est echappe pour eviter les injections Typst."""
        source = MINIMAL_DIR / "chapitres" / "01-introduction.md"
        images_dir = tmp_path / "images"
        images_dir.mkdir(exist_ok=True)
        src_img = MINIMAL_DIR / "images" / "diagram.png"
        dest_img = images_dir / "diagram.png"
        shutil.copy2(src_img, dest_img)

        book = BookNode(
            title="Test",
            chapters=(
                ChapterNode(
                    title="Ch",
                    children=(
                        ImageNode(
                            src=dest_img,
                            alt="Figure #1 avec $pecial",
                            source_file=source,
                            line_number=1,
                        ),
                    ),
                    source_file=source,
                    line_number=1,
                ),
            ),
            source_file=source,
            line_number=1,
        )
        typ_path = tmp_path / "output.typ"
        generate_typst(book, typ_path)
        content = typ_path.read_text(encoding="utf-8")
        assert r"caption: [Figure \#1 avec \$pecial]," in content
