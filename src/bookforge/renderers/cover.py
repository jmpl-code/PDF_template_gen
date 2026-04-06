"""Generation de couverture via template Typst (Story 2.7)."""

from __future__ import annotations

import logging
from pathlib import Path

from bookforge.config.schema import BookConfig
from bookforge.external import run_external
from bookforge.renderers.pdf import escape_typst

logger = logging.getLogger("bookforge.renderers.cover")

# Template Typst inline pour la couverture statique MVP0
_COVER_TEMPLATE = """\
// Couverture statique — BookForge (Story 2.7)
// Format 6x9 pouces (KDP standard)

#set page(
  width: 6in,
  height: 9in,
  margin: (x: 1.5cm, y: 2cm),
  numbering: none,
)

#set text(
  font: "New Computer Modern",
  lang: "fr",
  region: "FR",
)

// Disposition verticale centree
#align(center)[
  #v(1fr)

  #text(size: 36pt, weight: "bold")[{titre}]

{bloc_sous_titre}\
  #v(1fr)

  #text(size: 18pt)[{auteur}]

  #v(2cm)
]
"""


def generate_cover_typst(config: BookConfig, output_path: Path) -> Path:
    """Genere le fichier .typ de couverture depuis BookConfig."""
    titre = escape_typst(config.titre)
    auteur = escape_typst(config.auteur)

    if config.sous_titre:
        sous_titre = escape_typst(config.sous_titre)
        bloc_sous_titre = f"\n  #v(1em)\n  #text(size: 20pt)[{sous_titre}]\n\n"
    else:
        bloc_sous_titre = "\n"

    content = _COVER_TEMPLATE.format(
        titre=titre,
        auteur=auteur,
        bloc_sous_titre=bloc_sous_titre,
    )
    output_path.write_text(content, encoding="utf-8")
    logger.debug("Generated cover .typ file: %s", output_path)
    return output_path


def compile_cover(typ_path: Path, pdf_path: Path) -> Path:
    """Compile le .typ couverture en PDF via Typst."""
    run_external(
        ["typst", "compile", str(typ_path), str(pdf_path)],
        description="Compilation couverture Typst vers PDF",
    )
    return pdf_path


def render_cover(config: BookConfig, output_dir: Path) -> Path:
    """Point d'entree : BookConfig -> couverture.typ -> couverture.pdf."""
    output_dir.mkdir(parents=True, exist_ok=True)
    typ_path = output_dir / "couverture.typ"
    pdf_path = output_dir / "couverture.pdf"
    generate_cover_typst(config, typ_path)
    compile_cover(typ_path, pdf_path)
    logger.debug("Cover PDF generated: %s", pdf_path)
    return pdf_path
