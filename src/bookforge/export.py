"""Export metadonnees KDP et organisation du dossier de sortie (Story 2.8)."""

from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path

from bookforge.config.schema import BookConfig

logger = logging.getLogger("bookforge.export")


def export_metadata_kdp(config: BookConfig, output_dir: Path) -> Path:
    """Exporte les metadonnees KDP en JSON pret a copier-coller."""
    output_dir.mkdir(parents=True, exist_ok=True)
    metadata = {
        "titre": config.titre,
        "auteur": config.auteur,
        "sous_titre": config.sous_titre,
        "description": config.description,
        "mots_cles": config.mots_cles,
        "categories": config.categories,
        "isbn": config.isbn,
        "genre": config.genre,
    }
    output_path = output_dir / "metadata-kdp.json"
    output_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    logger.debug("KDP metadata exported: %s", output_path)
    return output_path


def organize_output(
    config: BookConfig,
    interior_pdf: Path,
    cover_pdf: Path,
    output_dir: Path,
) -> Path:
    """Organise le dossier de sortie final avec tous les livrables."""
    output_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(interior_pdf, output_dir / "livre-interieur.pdf")
    logger.debug("Copied interior PDF to output: %s", output_dir / "livre-interieur.pdf")
    shutil.copy2(cover_pdf, output_dir / "couverture.pdf")
    logger.debug("Copied cover PDF to output: %s", output_dir / "couverture.pdf")
    export_metadata_kdp(config, output_dir)
    logger.debug("Output directory organized: %s", output_dir)
    return output_dir
