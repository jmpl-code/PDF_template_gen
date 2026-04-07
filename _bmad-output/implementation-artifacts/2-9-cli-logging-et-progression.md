# Story 2.9 : CLI, logging et progression

Status: done

## Story

As a auteur,
I want lancer le pipeline via une commande unique avec progression visible et logging structuré,
So that je suis informé de l'avancement et des éventuels problèmes.

## Acceptance Criteria

1. **Given** un `book.yaml` valide et les fichiers Markdown **When** je lance `python -m bookforge book.yaml` **Then** le pipeline s'exécute bout-en-bout (parse -> render -> export) sans appel réseau (mode offline)
2. **And** la progression est affichée par phase (parsing, rendering, export)
3. **And** les warnings sont loggés avec timestamp, sévérité, composant source et message descriptif
4. **And** le code de sortie est 0 en cas de succès, 1 pour erreur d'entrée, 2 pour erreur de rendu
5. **And** le pipeline fonctionne sur Windows, macOS et Linux (pathlib partout)

## Tasks / Subtasks

- [x] Task 1 — Implémenter `pipeline.py` comme orchestrateur (AC: #1)
  - [x] 1.1 Créer la fonction `run_pipeline(book_path, output_dir, progress_callback)` orchestrant les 3 phases MVP0
  - [x] 1.2 Phase 1 — Parse : appeler `load_book_config()` + `parse_markdown_file()` + `tokens_to_ast()`
  - [x] 1.3 Phase 2 — Render : appeler `render_pdf()` + `render_cover()`
  - [x] 1.4 Phase 3 — Export : appeler `organize_output()` avec métadonnées KDP
  - [x] 1.5 Invoquer `progress_callback(phase, percent)` à chaque transition de phase
- [x] Task 2 — Étoffer `cli.py` avec Typer (AC: #1, #2, #4)
  - [x] 2.1 Ajouter options `--output-dir` (défaut: `output/`), `--lang` (stub, non utilisé MVP0), `--judge` (stub flag), `--preview` (stub flag)
  - [x] 2.2 Configurer le logging root `bookforge` avec `logging.basicConfig()` : format `%(asctime)s %(levelname)-5s [%(name)s] %(message)s`
  - [x] 2.3 Implémenter `progress_callback` qui affiche `[Phase X/3] {phase}... {percent}%` sur stderr
  - [x] 2.4 Wraper `run_pipeline()` dans un try/except `BookForgeError` → `raise typer.Exit(code=e.exit_code)`
  - [x] 2.5 Assurer que le module est exécutable via `python -m bookforge book.yaml` (`__main__.py`)
- [x] Task 3 — Logging structuré (AC: #3)
  - [x] 3.1 Vérifier que chaque module existant utilise `logging.getLogger("bookforge.<module>")` — tous conformes
  - [x] 3.2 Le format de logging inclut timestamp, sévérité, composant source (via le nom du logger)
- [x] Task 4 — Tests (AC: #1-5)
  - [x] 4.1 `test_pipeline.py` — test d'intégration pipeline complet avec fixture `minimal/`
  - [x] 4.2 `test_pipeline.py` — test erreur d'entrée (book.yaml invalide) → `InputError`
  - [x] 4.3 `test_cli.py` — test exit code 0 en cas de succès (via `typer.testing.CliRunner`)
  - [x] 4.4 `test_cli.py` — test exit code 1 pour `InputError`
  - [x] 4.5 `test_cli.py` — test exit code 2 pour `RenderError`
  - [x] 4.6 `test_cli.py` — test que la progression est affichée sur stderr
  - [x] 4.7 `test_cli.py` — test `__main__.py` exécutable
  - [x] 4.8 Vérifier zéro régression — 136/136 tests passent (123 existants + 13 nouveaux)

### Review Findings

- [x] [Review][Defer] Artefacts intermédiaires (.typ, .pdf) laissés dans book_root — accepté pour MVP0, à nettoyer dans une story ultérieure
- [x] [Review][Patch] book_root == output_dir → guard ajouté dans pipeline.py avec InputError + test
- [x] [Review][Patch] `__main__.py` — ajouté `from __future__ import annotations`
- [x] [Review][Defer] organize_output non-atomique [src/bookforge/export.py] — deferred, pre-existing (Story 2.8)
- [x] [Review][Defer] Path traversal possible via chap_config.fichier [src/bookforge/config/validator.py] — deferred, pre-existing (Story 2.1)

## Dev Notes

### Fichiers existants à connaître

| Fichier | État actuel | Action story 2.9 |
|---------|-------------|-------------------|
| `src/bookforge/cli.py` | Stub Typer minimal (commande `build` vide) | **Étoffer** — ajouter options, logging config, try/except, progress |
| `src/bookforge/pipeline.py` | Placeholder (1 ligne docstring) | **Implémenter** — orchestrateur complet |
| `src/bookforge/errors.py` | Complet (BookForgeError, InputError, RenderError, LLMError avec exit_code) | **Ne pas modifier** |
| `src/bookforge/external.py` | Complet (run_external avec gestion RenderError) | **Ne pas modifier** |
| `src/bookforge/export.py` | Complet (export_metadata_kdp + organize_output) | **Appeler** depuis pipeline |
| `src/bookforge/config/validator.py` | Complet (parse_book_yaml) | **Appeler** depuis pipeline |
| `src/bookforge/parser/markdown.py` | Complet (parse_markdown) | **Appeler** depuis pipeline |
| `src/bookforge/parser/transform.py` | Complet (transform_to_ast) | **Appeler** depuis pipeline |
| `src/bookforge/renderers/pdf.py` | Complet (render_pdf) | **Appeler** depuis pipeline |
| `src/bookforge/renderers/cover.py` | Complet (render_cover) | **Appeler** depuis pipeline |
| `src/bookforge/__init__.py` | Contient `__version__` | **Ne pas modifier** |

### Architecture du pipeline

Le pipeline orchestre 3 phases MVP0 (sur les 5 prévues dans l'architecture) :

```
Phase 1 — Parse : book.yaml → BookConfig, Markdown → AST
Phase 2 — Render : AST → .typ → PDF (intérieur + couverture)
Phase 3 — Export : organiser le dossier de sortie (PDFs + metadata-kdp.json)
```

Les phases 3 (QA programmatique) et 4 (LLM-judge) de l'architecture sont **hors scope MVP0**. Les implémenter plus tard dans les Epics 6-7.

### Signature attendue de `run_pipeline()`

```python
# src/bookforge/pipeline.py

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable

from bookforge.config.schema import BookConfig

logger = logging.getLogger("bookforge.pipeline")

ProgressCallback = Callable[[str, int], None]

def run_pipeline(
    config: BookConfig,
    book_root: Path,
    output_dir: Path,
    progress_callback: ProgressCallback | None = None,
) -> Path:
    """Orchestre le pipeline parse → render → export.

    Returns:
        Le chemin du dossier de sortie.
    """
```

### Implémentation du CLI

```python
# src/bookforge/cli.py — Structure attendue

import sys
import logging
from pathlib import Path

import typer

from bookforge import __version__
from bookforge.errors import BookForgeError

logger = logging.getLogger("bookforge.cli")

app = typer.Typer(
    name="bookforge",
    help="Pipeline CLI transformant des manuscrits Markdown en PDF et EPUB conformes KDP.",
)

@app.command()
def build(
    book: Path = typer.Argument(..., help="Chemin vers le fichier book.yaml"),
    output_dir: Path = typer.Option(Path("output"), "--output-dir", "-o", help="Dossier de sortie"),
    lang: str = typer.Option("fr", "--lang", help="Langue (stub MVP0)"),
    judge: bool = typer.Option(False, "--judge", help="Activer LLM-judge (stub MVP0)"),
    preview: bool = typer.Option(False, "--preview", help="Preview rapide (stub MVP0)"),
) -> None:
    """Lancer le pipeline de génération à partir d'un fichier book.yaml."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-5s [%(name)s] %(message)s",
        stream=sys.stderr,
    )
    # ... parse config, appeler run_pipeline, gérer exit codes
```

### `__main__.py`

Créer `src/bookforge/__main__.py` pour permettre `python -m bookforge` :

```python
"""Permet l'exécution via python -m bookforge."""

from bookforge.cli import app

app()
```

### Gestion des exit codes

Le catch top-level dans `cli.py` :

```python
try:
    # ... run_pipeline
    sys.exit(0)
except BookForgeError as e:
    logger.error(str(e))
    raise typer.Exit(code=e.exit_code) from e
except Exception as e:
    logger.exception("Unexpected error: %s", e)
    raise typer.Exit(code=1) from e
```

**Important** : Utiliser `raise typer.Exit(code=N)` plutôt que `sys.exit(N)` pour que Typer gère proprement la sortie. `CliRunner` de Typer capture le code via `result.exit_code`.

### Progress callback

```python
def _progress(phase: str, percent: int) -> None:
    """Affiche la progression sur stderr."""
    phases = {"parsing": 1, "rendering": 2, "export": 3}
    phase_num = phases.get(phase, "?")
    typer.echo(f"[Phase {phase_num}/3] {phase}... {percent}%", err=True)
```

### Logging — Règles absolues

- Logger par module : `logging.getLogger("bookforge.<module>")`
- Logging interne en **anglais** (debug/info/warning)
- Messages utilisateur en **français** via exceptions (InputError, RenderError)
- **Jamais de `print()`** — tout passe par `logging` ou `typer.echo()` (pour la progression)
- `logging.basicConfig()` configuré **une seule fois** dans `cli.py`
- Le format inclut : timestamp (`%(asctime)s`), sévérité (`%(levelname)s`), composant source (`%(name)s`)

### Anti-patterns à éviter

1. **NE PAS** ajouter `rich` ou `tqdm` — utiliser `typer.echo()` pour la progression (pas de nouvelle dépendance)
2. **NE PAS** créer de classe Pipeline — une simple fonction `run_pipeline()` suffit
3. **NE PAS** implémenter les phases QA et LLM-judge — hors scope MVP0, les stubs `--judge` et `--preview` doivent juste logger un warning "not implemented yet"
4. **NE PAS** modifier `errors.py` — la hiérarchie d'exceptions est complète
5. **NE PAS** modifier les modules existants sauf pour corriger un logger manquant
6. **NE PAS** utiliser `os.path` — `pathlib.Path` uniquement
7. **NE PAS** utiliser `shell=True` dans subprocess — `run_external()` est déjà correct
8. **NE PAS** modifier le fixture `tests/fixtures/books/minimal/book.yaml`
9. **NE PAS** ajouter de dépendances externes — tout est déjà disponible (typer, logging, pathlib)
10. **NE PAS** utiliser `sys.exit()` directement — utiliser `raise typer.Exit(code=N)` pour la testabilité

### Tests — Approche

**Pipeline tests** (`tests/test_pipeline.py`) :
- Mocker `run_external()` pour éviter de dépendre de Typst installé
- Utiliser le fixture `tests/fixtures/books/minimal/` pour l'intégration
- Tester que `progress_callback` est appelé avec les bonnes phases
- Tester `InputError` si le book.yaml est invalide

**CLI tests** (`tests/test_cli.py`) :
- Utiliser `typer.testing.CliRunner` pour tester la CLI
- `result = runner.invoke(app, ["path/to/book.yaml"])` 
- Vérifier `result.exit_code` pour chaque scénario
- Mocker `run_pipeline()` pour isoler le CLI du pipeline
- Tester que la progression apparaît dans `result.stderr` (ou `result.output` selon la config du runner)

**Naming convention** : `test_<quoi>_<condition>_<attendu>()`

### Previous Story Intelligence (Story 2.8)

- **123 tests** passent — zéro régression attendue
- Pattern `from __future__ import annotations` en première ligne de chaque module
- `shutil.copy2()` pour copier les PDFs (préserve métadonnées)
- `mkdir(parents=True, exist_ok=True)` pour créer les dossiers
- Modules indépendants : export.py ne dépend que de `config/schema.py`
- Commit pattern : `feat(bookforge): implement Story X.Y — description`
- Les modules existants ont tous leur logger (`logging.getLogger("bookforge.<module>")`)
- `json.dumps()` avec `ensure_ascii=False, indent=2` pour les JSON

### Project Structure Notes

- `pipeline.py` au même niveau que `cli.py`, `export.py`, `errors.py`, `external.py` dans `src/bookforge/`
- `__main__.py` à créer dans `src/bookforge/` (même niveau)
- Module dependencies de `pipeline.py` : `config/`, `parser/`, `renderers/`, `export` — conforme au diagramme d'architecture
- Module dependencies de `cli.py` : `pipeline`, `errors` uniquement — **NE PAS importer** directement les renderers/parser/export

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.9] — User story et acceptance criteria
- [Source: _bmad-output/planning-artifacts/architecture.md#Pipeline] — Architecture 5 phases, pattern subprocess, logging
- [Source: _bmad-output/planning-artifacts/architecture.md#CLI] — Typer, exit codes, options CLI
- [Source: _bmad-output/planning-artifacts/prd.md#FR37] — Progression du pipeline
- [Source: _bmad-output/planning-artifacts/prd.md#FR49-50] — CLI et exit codes
- [Source: _bmad-output/planning-artifacts/prd.md#FR39] — Logging structuré
- [Source: _bmad-output/implementation-artifacts/2-8-export-metadonnees-kdp-et-dossier-de-sortie.md] — Previous story patterns et intelligence

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

- ruff I001 fixed in pipeline.py (import sorting)
- ruff UP035 fixed in pipeline.py (typing.Callable → collections.abc.Callable)
- ruff F401 fixed in test_cli.py (unused MagicMock import)
- ruff format applied to cli.py and test_pipeline.py

### Completion Notes List

- `pipeline.py` implémenté comme orchestrateur 3 phases (parse → render → export) avec progress callback
- Signature simplifiée : `run_pipeline(book_path, output_dir, progress_callback)` — le pipeline charge lui-même le BookConfig et construit l'AST
- Build dir = book_root (pas un sous-dossier) car le renderer Typst résout les images en relatif via `relative_to`
- `cli.py` étoffé : options --output-dir, --lang, --judge, --preview (stubs MVP0), logging structuré, exit codes via `typer.Exit`
- `__main__.py` créé pour `python -m bookforge`
- Tous les modules existants avaient déjà leur logger conforme — aucune correction nécessaire
- 13 nouveaux tests (5 pipeline + 8 CLI), 136/136 passent
- ruff clean, mypy clean, format clean

### File List

- **src/bookforge/pipeline.py** — Modified (placeholder → orchestrateur complet)
- **src/bookforge/cli.py** — Modified (stub → CLI complet avec options, logging, exit codes)
- **src/bookforge/__main__.py** — Created (entry point `python -m bookforge`)
- **tests/test_pipeline.py** — Created (5 tests d'intégration pipeline)
- **tests/test_cli.py** — Created (8 tests CLI : exit codes, progression, options, __main__)
