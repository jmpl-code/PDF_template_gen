"""Validation book.yaml et assets references (Story 2.1)."""

import logging
from pathlib import Path

import yaml
from pydantic import ValidationError

from bookforge.config.schema import BookConfig
from bookforge.errors import InputError

logger = logging.getLogger("bookforge.config")


def load_book_config(path: Path) -> BookConfig:
    """Charge et valide un fichier book.yaml.

    Args:
        path: Chemin vers le fichier book.yaml.

    Returns:
        Un objet BookConfig valide.

    Raises:
        InputError: Si le fichier est introuvable, invalide ou reference des chapitres manquants.
    """
    if not path.exists():
        raise InputError(f"Fichier introuvable : {path}")

    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        raise InputError(f"Erreur de syntaxe YAML dans '{path}' : {e}")

    if not isinstance(raw, dict):
        raise InputError(f"Le fichier '{path}' doit contenir un document YAML (dict)")

    try:
        config = BookConfig(**raw)
    except ValidationError as e:
        messages = []
        for err in e.errors():
            field = " -> ".join(str(loc) for loc in err["loc"])
            messages.append(f"  - {field} : {err['msg']}")
        raise InputError(f"Configuration invalide dans '{path}' :\n" + "\n".join(messages))

    # Valider existence des fichiers chapitres (chemins relatifs au book.yaml)
    book_dir = path.parent
    for chap in config.chapitres:
        chap_path = book_dir / chap.fichier
        if not chap_path.exists():
            raise InputError(
                f"Fichier chapitre introuvable : '{chap.fichier}' "
                f"(resolu en '{chap_path}')"
            )

    logger.debug("Book config loaded: %s (%d chapters)", config.titre, len(config.chapitres))
    return config
