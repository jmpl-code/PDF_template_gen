"""Pattern subprocess uniforme pour appels externes (Typst, Pandoc, etc.)."""

import subprocess

from bookforge.errors import RenderError


def run_external(cmd: list[str], description: str) -> subprocess.CompletedProcess[str]:
    """Execute une commande externe avec gestion d'erreurs uniforme.

    Args:
        cmd: Commande et arguments (ex: ["typst", "compile", "book.typ"]).
        description: Description pour les messages d'erreur (ex: "Compilation Typst").

    Returns:
        Le resultat de la commande.

    Raises:
        RenderError: Si la commande est introuvable ou echoue.
    """
    if not cmd:
        raise RenderError(f"{description}: commande vide")
    try:
        return subprocess.run(cmd, capture_output=True, text=True, check=True)
    except FileNotFoundError:
        raise RenderError(f"{description}: commande '{cmd[0]}' introuvable")
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() or e.stdout.strip() or "echec de la commande (sans message)"
        raise RenderError(f"{description}: {error_msg}")
