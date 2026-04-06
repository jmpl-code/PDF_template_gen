"""Noeuds structurels : BookNode, ChapterNode, HeadingNode (Story 2.2)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bookforge.ast_nodes.base import ASTNode


@dataclass(frozen=True)
class HeadingNode:
    """Titre (h1-h6)."""

    level: int
    text: str
    source_file: Path
    line_number: int


@dataclass(frozen=True)
class ChapterNode:
    """Chapitre contenant des noeuds enfants."""

    title: str
    children: tuple[ASTNode, ...]
    source_file: Path
    line_number: int


@dataclass(frozen=True)
class BookNode:
    """Racine de l'AST — livre complet."""

    title: str
    chapters: tuple[ChapterNode, ...]
    source_file: Path
    line_number: int
