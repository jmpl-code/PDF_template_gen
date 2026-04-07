"""Point d'entree CLI BookForge via Typer."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import typer

from bookforge import __version__
from bookforge.errors import BookForgeError
from bookforge.pipeline import run_pipeline

logger = logging.getLogger("bookforge.cli")

app = typer.Typer(
    name="bookforge",
    help="Pipeline CLI transformant des manuscrits Markdown en PDF et EPUB conformes KDP.",
)


def _progress(phase: str, percent: int) -> None:
    """Affiche la progression sur stderr."""
    phases = {"parsing": 1, "rendering": 2, "export": 3}
    phase_num = phases.get(phase, "?")
    typer.echo(f"[Phase {phase_num}/3] {phase}... {percent}%", err=True)


@app.command()
def build(
    book: Path = typer.Argument(..., help="Chemin vers le fichier book.yaml"),
    output_dir: Path = typer.Option(Path("output"), "--output-dir", "-o", help="Dossier de sortie"),
    lang: str = typer.Option("fr", "--lang", help="Langue (stub MVP0)"),
    judge: bool = typer.Option(False, "--judge", help="Activer LLM-judge (stub MVP0)"),
    preview: bool = typer.Option(False, "--preview", help="Preview rapide (stub MVP0)"),
) -> None:
    """Lancer le pipeline de generation a partir d'un fichier book.yaml."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-5s [%(name)s] %(message)s",
        stream=sys.stderr,
    )

    logger.info("BookForge v%s — build from: %s", __version__, book)

    if judge:
        logger.warning("--judge is not implemented yet (MVP0 stub)")
    if preview:
        logger.warning("--preview is not implemented yet (MVP0 stub)")
    if lang != "fr":
        logger.warning("--lang=%s is not implemented yet (MVP0 stub, default: fr)", lang)

    try:
        run_pipeline(
            book_path=book.resolve(),
            output_dir=output_dir.resolve(),
            progress_callback=_progress,
        )
    except BookForgeError as e:
        logger.error("%s", e)
        raise typer.Exit(code=e.exit_code) from e
    except Exception as e:
        logger.exception("Unexpected error: %s", e)
        raise typer.Exit(code=1) from e


if __name__ == "__main__":
    app()
