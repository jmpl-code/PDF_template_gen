"""Point d'entree CLI BookForge via Typer."""

import logging

import typer

from bookforge import __version__

logger = logging.getLogger("bookforge.cli")

app = typer.Typer(
    name="bookforge",
    help="Pipeline CLI transformant des manuscrits Markdown en PDF et EPUB conformes KDP.",
)


@app.command()
def build(book: str = typer.Argument(help="Chemin vers le fichier book.yaml")) -> None:
    """Lancer le pipeline de generation a partir d'un fichier book.yaml."""
    logger.info("BookForge v%s — build from: %s", __version__, book)


if __name__ == "__main__":
    app()
