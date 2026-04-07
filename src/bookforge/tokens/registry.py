"""Registre de tokens avec assertions min/max/source (Story 4.1)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TokenSpec:
    """Specification d'un design token avec contraintes verifiables."""

    default: int | float | str
    min: int | float | None = None
    max: int | float | None = None
    unit: str = ""
    source: str = ""


TOKEN_REGISTRY: dict[str, TokenSpec] = {
    # --- Geometrie page (KDP specs) ---
    "page_width": TokenSpec(default="6in", unit="", source="KDP standard trim 6x9"),
    "page_height": TokenSpec(default="9in", unit="", source="KDP standard trim 6x9"),
    "margin_inner": TokenSpec(default="2cm", unit="", source="KDP minimum margins"),
    "margin_outer": TokenSpec(default="1.5cm", unit="", source="KDP minimum margins"),
    "margin_top": TokenSpec(default="2.5cm", unit="", source="KDP minimum margins"),
    "margin_bottom": TokenSpec(default="2cm", unit="", source="KDP minimum margins"),
    # --- Typographie corps (Bringhurst) ---
    "font_family": TokenSpec(default="New Computer Modern", unit="", source="Bringhurst"),
    "font_size": TokenSpec(default=11, min=9, max=14, unit="pt", source="Bringhurst"),
    "line_height": TokenSpec(
        default=1.35, min=1.20, max=1.45, unit="em", source="Bringhurst §2.1"
    ),
    # --- Hierarchie titres (KOMA-Script) ---
    "heading_1_size": TokenSpec(default=24, min=18, max=36, unit="pt", source="KOMA-Script"),
    "heading_2_size": TokenSpec(default=18, min=14, max=28, unit="pt", source="KOMA-Script"),
    "heading_3_size": TokenSpec(default=14, min=11, max=22, unit="pt", source="KOMA-Script"),
    "heading_4_size": TokenSpec(default=12, min=10, max=18, unit="pt", source="KOMA-Script"),
    # --- Espacement (LaTeX memoir) ---
    "par_indent": TokenSpec(default="1em", unit="", source="LaTeX memoir"),
    "par_skip": TokenSpec(default="0pt", unit="", source="LaTeX memoir"),
}
