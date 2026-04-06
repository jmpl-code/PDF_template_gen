"""Transformation tokens markdown-it-py vers AST BookForge (Story 2.2)."""

import logging
from pathlib import Path

from markdown_it.token import Token

from bookforge.ast_nodes.base import ASTNode
from bookforge.ast_nodes.content import ImageNode, ParagraphNode, TableNode
from bookforge.ast_nodes.structure import HeadingNode
from bookforge.errors import InputError

logger = logging.getLogger("bookforge.parser")


def _line_number(token: Token) -> int:
    """Extrait le numero de ligne (1-indexed) depuis token.map."""
    if token.map is not None:
        return token.map[0] + 1
    return 0


def _extract_inline_text(token: Token) -> str:
    """Extrait le texte brut d'un token inline."""
    return token.content


def _extract_image(
    token: Token, source_file: Path, line_number: int
) -> ImageNode:
    """Extrait un ImageNode depuis un token image (enfant d'inline)."""
    src_raw = str(token.attrGet("src") or "")
    alt = str(token.attrGet("alt") or "")
    if not alt and token.children:
        alt = token.children[0].content

    # Resoudre le chemin relatif au fichier Markdown source
    src_path = (source_file.parent / src_raw).resolve()

    if not src_path.exists():
        raise InputError(
            f"Image introuvable : '{src_raw}' "
            f"(resolu en '{src_path}', reference dans '{source_file}' ligne {line_number})"
        )

    return ImageNode(
        src=src_path,
        alt=alt,
        source_file=source_file,
        line_number=line_number,
    )


def _extract_table(
    tokens: list[Token], start: int, source_file: Path, line_number: int
) -> tuple[TableNode, int]:
    """Extrait un TableNode depuis les tokens table_open..table_close.

    Returns:
        Tuple (TableNode, index apres table_close).
    """
    headers: list[str] = []
    rows: list[tuple[str, ...]] = []
    current_row: list[str] = []
    in_thead = False
    in_tbody = False

    i = start + 1  # Skip table_open
    while i < len(tokens) and tokens[i].type != "table_close":
        t = tokens[i]
        if t.type == "thead_open":
            in_thead = True
        elif t.type == "thead_close":
            in_thead = False
        elif t.type == "tbody_open":
            in_tbody = True
        elif t.type == "tbody_close":
            in_tbody = False
        elif t.type == "tr_open":
            current_row = []
        elif t.type == "tr_close":
            if in_thead:
                headers = current_row
            elif in_tbody:
                rows.append(tuple(current_row))
        elif t.type == "inline":
            current_row.append(t.content)
        i += 1

    return (
        TableNode(
            headers=tuple(headers),
            rows=tuple(rows),
            source_file=source_file,
            line_number=line_number,
        ),
        i + 1,  # Skip table_close
    )


def tokens_to_ast(tokens: list[Token], source_file: Path) -> list[ASTNode]:
    """Convertit les tokens markdown-it-py en noeuds AST BookForge.

    Args:
        tokens: Tokens produits par markdown-it-py.
        source_file: Chemin absolu du fichier .md source.

    Returns:
        Liste de noeuds AST.

    Raises:
        InputError: Si une image referencee n'existe pas.
    """
    nodes: list[ASTNode] = []
    i = 0

    while i < len(tokens):
        token = tokens[i]

        if token.type == "heading_open":
            # Extraire le level depuis le tag (h1-h6)
            level = int(token.tag[1])
            line = _line_number(token)
            # Le token suivant est l'inline avec le texte
            i += 1
            text = _extract_inline_text(tokens[i])
            nodes.append(HeadingNode(
                level=level, text=text, source_file=source_file, line_number=line,
            ))
            i += 1  # Skip heading_close
            i += 1
            continue

        if token.type == "paragraph_open":
            line = _line_number(token)
            # Le token suivant est l'inline
            i += 1
            inline_token = tokens[i]

            # Verifier si l'inline contient uniquement une image
            if (
                inline_token.children
                and len(inline_token.children) == 1
                and inline_token.children[0].type == "image"
            ):
                img_token = inline_token.children[0]
                nodes.append(_extract_image(img_token, source_file, line))
            else:
                text = _extract_inline_text(inline_token)
                if text.strip():
                    nodes.append(ParagraphNode(
                        text=text, source_file=source_file, line_number=line,
                    ))

            i += 1  # Skip paragraph_close
            i += 1
            continue

        if token.type == "table_open":
            line = _line_number(token)
            table_node, next_i = _extract_table(tokens, i, source_file, line)
            nodes.append(table_node)
            i = next_i
            continue

        # Skip tokens non geres (fence, hr, etc.)
        i += 1

    logger.debug(
        "Transformed %d tokens into %d AST nodes from %s", len(tokens), len(nodes), source_file
    )
    return nodes
