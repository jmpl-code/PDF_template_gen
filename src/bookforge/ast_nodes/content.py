"""Noeuds de contenu : ParagraphNode, ImageNode, TableNode (Story 2.2)."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ParagraphNode:
    """Paragraphe de texte."""

    text: str
    source_file: Path
    line_number: int


@dataclass(frozen=True)
class ImageNode:
    """Image avec chemin absolu resolu."""

    src: Path
    alt: str
    source_file: Path
    line_number: int


@dataclass(frozen=True)
class TableNode:
    """Tableau avec en-tetes et lignes."""

    headers: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]
    source_file: Path
    line_number: int
