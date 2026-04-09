"""Noeuds semantiques : FrameworkNode, CalloutNode, ChapterSummaryNode (Story 4.3)."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FrameworkNode:
    """Encadre framework (:::framework ... :::)."""

    content: str
    source_file: Path
    line_number: int


@dataclass(frozen=True)
class CalloutNode:
    """Encadre callout (:::callout ... :::)."""

    content: str
    source_file: Path
    line_number: int


@dataclass(frozen=True)
class ChapterSummaryNode:
    """Resume de chapitre (:::chapter-summary ... :::)."""

    content: str
    source_file: Path
    line_number: int
