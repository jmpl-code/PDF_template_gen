"""Noeud AST de base et type union (Story 2.2, 4.3)."""

from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from bookforge.ast_nodes.content import ImageNode, ParagraphNode, TableNode
    from bookforge.ast_nodes.semantic import CalloutNode, ChapterSummaryNode, FrameworkNode
    from bookforge.ast_nodes.structure import HeadingNode

# Type union de tous les noeuds de contenu (feuilles et structurels inline)
ASTNode = Union[
    "HeadingNode",
    "ParagraphNode",
    "ImageNode",
    "TableNode",
    "FrameworkNode",
    "CalloutNode",
    "ChapterSummaryNode",
]
