"""Pipeline principal : orchestration parse → render → export."""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path

from bookforge.config.schema import BookConfig
from bookforge.config.validator import load_book_config
from bookforge.errors import InputError
from bookforge.export import organize_output
from bookforge.parser import parse_book
from bookforge.renderers.cover import render_cover
from bookforge.renderers.pdf import render_pdf

logger = logging.getLogger("bookforge.pipeline")

ProgressCallback = Callable[[str, int], None]


def _notify(callback: ProgressCallback | None, phase: str, percent: int) -> None:
    """Invoke progress callback if provided."""
    if callback is not None:
        callback(phase, percent)


def run_pipeline(
    book_path: Path,
    output_dir: Path,
    progress_callback: ProgressCallback | None = None,
) -> Path:
    """Orchestre le pipeline parse -> render -> export.

    Args:
        book_path: Chemin vers le fichier book.yaml.
        output_dir: Dossier de sortie final.
        progress_callback: Callback optionnel (phase, percent).

    Returns:
        Le chemin du dossier de sortie.
    """
    book_root = book_path.parent

    if output_dir.resolve() == book_root.resolve():
        raise InputError(
            f"Le dossier de sortie '{output_dir}' ne peut pas etre le meme "
            f"que le dossier du livre '{book_root}'"
        )

    # Phase 1 — Parse
    _notify(progress_callback, "parsing", 0)
    logger.info("Phase 1/3: parsing %s", book_path)
    config = load_book_config(book_path)
    book = parse_book(config, book_root)
    logger.info("Parsed %d chapters", len(book.chapters))
    _notify(progress_callback, "parsing", 100)

    # Phase 2 — Render
    # Build dir must be book_root so images resolve via relative_to in Typst renderer
    _notify(progress_callback, "rendering", 0)
    logger.info("Phase 2/3: rendering PDF")
    interior_pdf = render_pdf(book, book_root, config=config)
    cover_pdf = render_cover(config, book_root)
    logger.info("Rendered interior and cover PDFs")
    _notify(progress_callback, "rendering", 100)

    # Phase 3 — Export
    _notify(progress_callback, "export", 0)
    logger.info("Phase 3/3: organizing output")
    organize_output(config, interior_pdf, cover_pdf, output_dir)
    logger.info("Output organized in %s", output_dir)
    _notify(progress_callback, "export", 100)

    return output_dir
