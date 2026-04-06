# Story 1.2 : Structure des modules et erreurs de base

Status: done

## Story

As a auteur-developpeur,
I want disposer de la structure complete des packages et des classes d'erreurs,
So that les stories suivantes peuvent implementer chaque module dans son emplacement defini.

## Acceptance Criteria

1. **Given** le projet initialise (Story 1.1)
   **When** je cree la structure des packages (`config/`, `parser/`, `ast_nodes/`, `tokens/`, `passes/`, `renderers/`, `quality/`, `judge/`) avec `__init__.py`
   **Then** tous les packages sont importables (`from bookforge.config import ...`)
   **And** `errors.py` definit `BookForgeError`, `InputError` (exit 1), `RenderError` (exit 2), `LLMError` (exit 3)
   **And** `external.py` definit `run_external()` avec le pattern subprocess uniforme (capture_output, text, check, jamais shell=True)
   **And** les tests verifient que chaque exception retourne le bon `exit_code`

## Tasks / Subtasks

- [x] Task 1 — Creer la hierarchie d'erreurs (AC: #1)
  - [x] 1.1 Creer `src/bookforge/errors.py` avec `BookForgeError(Exception)` portant un attribut `exit_code: int`
  - [x] 1.2 Definir `InputError(BookForgeError)` avec `exit_code = 1`
  - [x] 1.3 Definir `RenderError(BookForgeError)` avec `exit_code = 2`
  - [x] 1.4 Definir `LLMError(BookForgeError)` avec `exit_code = 3`
  - [x] 1.5 Ecrire tests dans `tests/test_errors.py` : verifier exit_code de chaque exception, heritage, messages en francais
- [x] Task 2 — Creer `run_external()` (AC: #1)
  - [x] 2.1 Creer `src/bookforge/external.py` avec `run_external(cmd: list[str], description: str) -> subprocess.CompletedProcess`
  - [x] 2.2 Implementer : `subprocess.run(cmd, capture_output=True, text=True, check=True)` enveloppe dans try/except
  - [x] 2.3 `FileNotFoundError` → `RenderError(f"{description}: commande '{cmd[0]}' introuvable")`
  - [x] 2.4 `CalledProcessError` → `RenderError(f"{description}: {e.stderr.strip()}")`
  - [x] 2.5 Ecrire tests dans `tests/test_external.py` : commande valide, commande introuvable, commande echouant
- [x] Task 3 — Creer les packages avec `__init__.py` (AC: #1)
  - [x] 3.1 Creer `src/bookforge/config/__init__.py`
  - [x] 3.2 Creer `src/bookforge/parser/__init__.py`
  - [x] 3.3 Creer `src/bookforge/ast_nodes/__init__.py`
  - [x] 3.4 Creer `src/bookforge/tokens/__init__.py`
  - [x] 3.5 Creer `src/bookforge/passes/__init__.py`
  - [x] 3.6 Creer `src/bookforge/renderers/__init__.py`
  - [x] 3.7 Creer `src/bookforge/quality/__init__.py`
  - [x] 3.8 Creer `src/bookforge/judge/__init__.py`
- [x] Task 4 — Creer les fichiers placeholder des modules (AC: #1)
  - [x] 4.1 Creer les fichiers vides dans chaque package selon l'arborescence architecture (schema.py, validator.py, markdown.py, etc.)
  - [x] 4.2 Creer `src/bookforge/pipeline.py` (placeholder)
  - [x] 4.3 Creer `src/bookforge/tokens/defaults/` avec `business_manual.yaml` placeholder
  - [x] 4.4 Creer `templates/typst/` avec fichiers `.typ` placeholder (base.typ, cover.typ, etc.)
  - [x] 4.5 Creer `tests/fixtures/` avec sous-dossiers (books/minimal/, books/full/, books/broken/, golden/, tokens/)
- [x] Task 5 — Tests d'importabilite de tous les packages (AC: #1)
  - [x] 5.1 Ecrire `tests/test_packages.py` verifiant que chaque package est importable
  - [x] 5.2 Verifier que `from bookforge.errors import BookForgeError, InputError, RenderError, LLMError` fonctionne
  - [x] 5.3 Verifier que `from bookforge.external import run_external` fonctionne
- [x] Task 6 — Validation finale (AC: #1)
  - [x] 6.1 `uv run ruff check .` passe sans erreur
  - [x] 6.2 `uv run pytest` — tous les tests passent (anciens + nouveaux)

## Dev Notes

### Contexte

Cette story construit la structure complete du projet BookForge sur le squelette cree en Story 1.1. Apres cette story, chaque module aura son emplacement defini et les stories suivantes pourront implementer directement dedans.

### Apprentissages de Story 1.1

- **Ruff scope** : le `[tool.ruff]` utilise `include = ["src/bookforge/**/*.py", "tests/**/*.py"]` pour ne pas linter les fichiers BMad existants.
- **Build system** : Hatchling + hatch-vcs (pas uv_build).
- **pyproject.toml** : deja configure avec ruff (line-length=100, regles E/F/W/I/N/UP), mypy strict, pytest testpaths=["tests"].
- **Fichiers existants** : `src/bookforge/__init__.py` (version), `src/bookforge/cli.py` (Typer app), `tests/test_init.py` (3 tests).

### Hierarchie d'erreurs — Implementation exacte

```python
class BookForgeError(Exception):
    """Erreur de base BookForge."""
    exit_code: int = 1

    def __init__(self, message: str) -> None:
        super().__init__(message)

class InputError(BookForgeError):
    """Erreur d'entree utilisateur (config invalide, fichier manquant)."""
    exit_code = 1

class RenderError(BookForgeError):
    """Erreur de rendu (subprocess, template)."""
    exit_code = 2

class LLMError(BookForgeError):
    """Erreur LLM (API, timeout)."""
    exit_code = 3
```

**Regles :**
- Messages utilisateur en **francais**, actionnables, via ces exceptions.
- Jamais `print()` — logging interne en anglais via `logging.getLogger("bookforge.<module>")`.
- Jamais de `Exception` generique.

### Pattern `run_external()` — Implementation exacte

```python
import subprocess
from bookforge.errors import RenderError

def run_external(cmd: list[str], description: str) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, check=True)
    except FileNotFoundError:
        raise RenderError(f"{description}: commande '{cmd[0]}' introuvable")
    except subprocess.CalledProcessError as e:
        raise RenderError(f"{description}: {e.stderr.strip()}")
```

**Regles :**
- Toujours `capture_output=True, text=True, check=True`.
- Jamais `shell=True`.
- Fichier : `src/bookforge/external.py`.
- Toutes les stories suivantes DOIVENT utiliser `run_external()` pour appeler Typst, Pandoc, etc.

### Arborescence complete a creer

```
src/bookforge/
├── __init__.py          # (existe deja)
├── cli.py               # (existe deja)
├── errors.py            # NEW — hierarchie d'erreurs
├── external.py          # NEW — run_external()
├── pipeline.py          # NEW — placeholder
│
├── config/
│   ├── __init__.py
│   ├── schema.py        # placeholder (Pydantic models — Story 2.1)
│   └── validator.py     # placeholder (validation book.yaml — Story 2.1)
│
├── parser/
│   ├── __init__.py
│   ├── markdown.py      # placeholder (markdown-it-py — Story 2.2)
│   ├── semantic.py      # placeholder (balises :::framework — Story 4.3)
│   └── transform.py     # placeholder (MD tokens → AST — Story 2.2)
│
├── ast_nodes/
│   ├── __init__.py
│   ├── base.py          # placeholder (ASTNode base — Story 2.2)
│   ├── content.py       # placeholder (ParagraphNode, ImageNode — Story 2.2)
│   ├── semantic.py      # placeholder (FrameworkNode, CalloutNode — Story 4.3)
│   └── structure.py     # placeholder (BookNode, ChapterNode — Story 2.2)
│
├── tokens/
│   ├── __init__.py
│   ├── registry.py      # placeholder (TokenSpec — Story 4.1)
│   ├── resolver.py      # placeholder (ResolvedTokenSet — Story 4.1)
│   └── defaults/
│       └── business_manual.yaml  # placeholder
│
├── passes/
│   ├── __init__.py
│   ├── pdf_transform.py   # placeholder (AST → Typst — Story 2.3)
│   └── epub_transform.py  # placeholder (AST → Pandoc input — Story 3.1)
│
├── renderers/
│   ├── __init__.py
│   ├── pdf.py           # placeholder (Typst compile — Story 2.3)
│   ├── epub.py          # placeholder (Pandoc — Story 3.1)
│   └── cover.py         # placeholder (couverture — Story 2.7)
│
├── quality/
│   ├── __init__.py
│   ├── checks.py        # placeholder (DPI, orphelines — Story 7.1)
│   └── reporter.py      # placeholder (rapports QA — Story 7.1)
│
└── judge/
    ├── __init__.py
    ├── protocol.py      # placeholder (Protocol Python — Story 6.1)
    ├── gemini.py         # placeholder (implementation Gemini — Story 6.1)
    ├── mock.py           # placeholder (mock pour tests — Story 6.1)
    └── loop.py           # placeholder (boucle auto — Story 7.2)

templates/typst/
├── base.typ             # placeholder
├── business_manual.typ  # placeholder
├── chapter_page.typ     # placeholder
└── cover.typ            # placeholder

tests/fixtures/
├── books/
│   ├── minimal/         # placeholder (book.yaml + 1 chapitre)
│   ├── full/            # placeholder
│   └── broken/          # placeholder (cas d'erreurs)
├── golden/              # placeholder (snapshots reference)
└── tokens/              # placeholder (YAML valides/invalides)
```

### Ce que cette story ne fait PAS

- N'implemente PAS la logique des modules (schema.py reste vide) → Stories 2.x+
- Ne cree PAS le CI GitHub Actions → Story 1.3
- N'ajoute PAS de nouvelles dependances → Tout est deja installe en 1.1
- Les fichiers placeholder contiennent juste un docstring decrivant le role futur du module

### Pieges a eviter

1. **Ne pas oublier `__init__.py`** dans chaque sous-package — sinon les imports echouent.
2. **Placeholders = docstring uniquement** — pas de code mort ni d'implementations factices.
3. **Ne pas toucher `cli.py`** — il ne doit pas encore importer les modules placeholders.
4. **`run_external` importe depuis `errors`** — attention a l'ordre des imports circulaires (il n'y en a pas ici, mais le verifier).
5. **Tests parametrises** pour les erreurs — utiliser `@pytest.mark.parametrize` pour tester les 3 sous-classes.

### Project Structure Notes

- Les fichiers placeholder dans `templates/typst/` et `tests/fixtures/` ne sont pas des modules Python.
- Le dossier `tokens/defaults/` contient un fichier YAML, pas du Python.
- Attention : `tests/fixtures/` est distinct de `tests/` pour les fichiers de test pytest.

### References

- [Source: _bmad-output/planning-artifacts/architecture.md — Section "Arborescence cible"]
- [Source: _bmad-output/planning-artifacts/architecture.md — Section "Strategie d'erreurs"]
- [Source: _bmad-output/planning-artifacts/architecture.md — Section "Pattern subprocess uniforme"]
- [Source: _bmad-output/planning-artifacts/architecture.md — Section "Conventions de nommage"]
- [Source: _bmad-output/planning-artifacts/epics.md — Epic 1, Story 1.2]
- [Source: _bmad-output/implementation-artifacts/1-1-*.md — Dev Agent Record, Debug Log]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

- Aucun probleme rencontre — implementation directe sans blocage
- 8 packages crees avec 22 fichiers placeholder Python (docstring uniquement)
- Pattern run_external() implemente exactement comme specifie dans l'architecture

### Completion Notes List

- `errors.py` : hierarchie BookForgeError → InputError(1) / RenderError(2) / LLMError(3) — 11 tests
- `external.py` : run_external() avec gestion FileNotFoundError et CalledProcessError — 5 tests
- 8 packages crees : config, parser, ast_nodes, tokens, passes, renderers, quality, judge
- 22 fichiers placeholder Python avec docstrings decrivant le role futur
- `pipeline.py` placeholder a la racine du package
- `tokens/defaults/business_manual.yaml` placeholder
- 4 templates Typst placeholder dans `templates/typst/`
- 5 dossiers fixtures dans `tests/fixtures/` (books/minimal, books/full, books/broken, golden, tokens)
- 11 tests d'importabilite (9 packages + errors + external)
- Total : 30 tests passent, ruff check OK, zero regression

### Change Log

- 2026-04-06 : Implementation Story 1.2 — structure modules, erreurs, run_external

### File List

- src/bookforge/errors.py (nouveau)
- src/bookforge/external.py (nouveau)
- src/bookforge/pipeline.py (nouveau)
- src/bookforge/config/__init__.py (nouveau)
- src/bookforge/config/schema.py (nouveau)
- src/bookforge/config/validator.py (nouveau)
- src/bookforge/parser/__init__.py (nouveau)
- src/bookforge/parser/markdown.py (nouveau)
- src/bookforge/parser/semantic.py (nouveau)
- src/bookforge/parser/transform.py (nouveau)
- src/bookforge/ast_nodes/__init__.py (nouveau)
- src/bookforge/ast_nodes/base.py (nouveau)
- src/bookforge/ast_nodes/content.py (nouveau)
- src/bookforge/ast_nodes/semantic.py (nouveau)
- src/bookforge/ast_nodes/structure.py (nouveau)
- src/bookforge/tokens/__init__.py (nouveau)
- src/bookforge/tokens/registry.py (nouveau)
- src/bookforge/tokens/resolver.py (nouveau)
- src/bookforge/tokens/defaults/business_manual.yaml (nouveau)
- src/bookforge/passes/__init__.py (nouveau)
- src/bookforge/passes/pdf_transform.py (nouveau)
- src/bookforge/passes/epub_transform.py (nouveau)
- src/bookforge/renderers/__init__.py (nouveau)
- src/bookforge/renderers/pdf.py (nouveau)
- src/bookforge/renderers/epub.py (nouveau)
- src/bookforge/renderers/cover.py (nouveau)
- src/bookforge/quality/__init__.py (nouveau)
- src/bookforge/quality/checks.py (nouveau)
- src/bookforge/quality/reporter.py (nouveau)
- src/bookforge/judge/__init__.py (nouveau)
- src/bookforge/judge/protocol.py (nouveau)
- src/bookforge/judge/gemini.py (nouveau)
- src/bookforge/judge/mock.py (nouveau)
- src/bookforge/judge/loop.py (nouveau)
- templates/typst/base.typ (nouveau)
- templates/typst/business_manual.typ (nouveau)
- templates/typst/chapter_page.typ (nouveau)
- templates/typst/cover.typ (nouveau)
- tests/test_errors.py (nouveau)
- tests/test_external.py (nouveau)
- tests/test_packages.py (nouveau)
- tests/fixtures/books/minimal/.gitkeep (nouveau)
- tests/fixtures/books/full/.gitkeep (nouveau)
- tests/fixtures/books/broken/.gitkeep (nouveau)
- tests/fixtures/golden/.gitkeep (nouveau)
- tests/fixtures/tokens/.gitkeep (nouveau)
