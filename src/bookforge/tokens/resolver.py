"""Resolution des tokens : defaults + surcharges auteur → ResolvedTokenSet (Story 4.1)."""

from __future__ import annotations

import logging
from pathlib import Path

import yaml
from pydantic import BaseModel

from bookforge.tokens.registry import TOKEN_REGISTRY

logger = logging.getLogger("bookforge.tokens.resolver")

_DEFAULTS_DIR = Path(__file__).parent / "defaults"


class ResolvedTokenSet(BaseModel):
    """Jeu de tokens resolus et valides, pret a consommer par les renderers."""

    # Geometrie page
    page_width: str = "6in"
    page_height: str = "9in"
    margin_inner: str = "2cm"
    margin_outer: str = "1.5cm"
    margin_top: str = "2.5cm"
    margin_bottom: str = "2cm"

    # Typographie corps
    font_family: str = "New Computer Modern"
    font_size: int | float = 11
    line_height: float = 1.35

    # Hierarchie titres
    heading_1_size: int | float = 24
    heading_2_size: int | float = 18
    heading_3_size: int | float = 14
    heading_4_size: int | float = 12

    # Espacement
    par_indent: str = "1em"
    par_skip: str = "0pt"


def _load_yaml(path: Path) -> dict[str, object]:
    """Charge un fichier YAML et retourne un dict."""
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if data is None:
        return {}
    if not isinstance(data, dict):
        logger.warning("tokens YAML invalide (pas un mapping) : %s", path)
        return {}
    return data


def resolve_tokens(
    user_yaml: Path | None = None,
    *,
    class_name: str = "business-manual",
) -> ResolvedTokenSet:
    """Resout les tokens : defaults de classe + surcharges auteur.

    Args:
        user_yaml: Chemin optionnel vers un fichier tokens.yaml utilisateur.
        class_name: Nom de la classe de document (defaut: business-manual).

    Returns:
        Un ResolvedTokenSet valide avec toutes les valeurs resolues.
    """
    # 1. Charger les defaults de la classe
    class_file_name = class_name.replace("-", "_") + ".yaml"
    defaults_path = _DEFAULTS_DIR / class_file_name
    if defaults_path.exists():
        merged = _load_yaml(defaults_path)
    else:
        logger.warning(
            "Fichier defaults introuvable : %s — tokens registre utilises", defaults_path
        )
        merged = {name: spec.default for name, spec in TOKEN_REGISTRY.items()}

    # 2. Surcharger avec les valeurs utilisateur
    if user_yaml is not None:
        user_data = _load_yaml(user_yaml)
        for key, value in user_data.items():
            if key not in TOKEN_REGISTRY:
                logger.warning("Token inconnu ignore : '%s'", key)
                continue
            merged[key] = value

    # 3. Valider chaque token vs le registre (min/max)
    validated: dict[str, object] = {}
    for name, spec in TOKEN_REGISTRY.items():
        value = merged.get(name, spec.default)
        if spec.min is not None and spec.max is not None:
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                if value < spec.min or value > spec.max:
                    logger.warning(
                        "%s=%s hors bornes [%s, %s] — source: %s — defaut %s utilise",
                        name,
                        value,
                        spec.min,
                        spec.max,
                        spec.source,
                        spec.default,
                    )
                    value = spec.default
        validated[name] = value

    return ResolvedTokenSet.model_validate(validated)
