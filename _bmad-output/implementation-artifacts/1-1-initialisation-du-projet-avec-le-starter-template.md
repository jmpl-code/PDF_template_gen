# Story 1.1 : Initialisation du projet avec le starter template

Status: done

## Story

As a auteur-developpeur,
I want initialiser le projet BookForge avec la stack Typer + uv + Hatchling,
So that je dispose d'un squelette fonctionnel avec les dependances, le linting et les tests configures.

## Acceptance Criteria

1. **Given** un environnement avec Python >= 3.10, uv installe
   **When** je lance `uv init bookforge --lib` et les commandes d'ajout de dependances
   **Then** le projet contient `pyproject.toml` configure (Hatchling, Ruff, mypy, pytest), `uv.lock` genere, et la structure `src/bookforge/`
   **And** `uv run pytest` passe sans erreur
   **And** `uv run ruff check .` passe sans erreur

## Tasks / Subtasks

- [x] Task 1 — Initialiser le projet via uv (AC: #1)
  - [x] 1.1 Executer `uv init bookforge --lib` a la racine du depot
  - [x] 1.2 Verifier que `pyproject.toml`, `uv.lock` et `src/bookforge/__init__.py` sont generes
- [x] Task 2 — Configurer les dependances (AC: #1)
  - [x] 2.1 Ajouter les dependances runtime : `uv add typer pyyaml pydantic markdown-it-py matplotlib`
  - [x] 2.2 Ajouter les dependances dev : `uv add --dev pytest ruff mypy`
  - [x] 2.3 Verifier que `uv.lock` est regenere avec toutes les dependances
- [x] Task 3 — Configurer pyproject.toml (AC: #1)
  - [x] 3.1 Configurer le build system Hatchling (hatchling + hatch-vcs)
  - [x] 3.2 Definir les metadonnees projet (name, version, requires-python >= 3.10)
  - [x] 3.3 Configurer `[tool.ruff]` : line-length = 100, regles de linting
  - [x] 3.4 Configurer `[tool.mypy]` : python_version = "3.10", strict = true
  - [x] 3.5 Configurer `[tool.pytest.ini_options]` : testpaths = ["tests"]
  - [x] 3.6 Definir le script entry point CLI : `bookforge = "bookforge.cli:app"`
- [x] Task 4 — Creer la structure minimale src/bookforge/ (AC: #1)
  - [x] 4.1 Creer `src/bookforge/__init__.py` avec `__version__`
  - [x] 4.2 Creer `src/bookforge/cli.py` avec un Typer app minimal (commande placeholder)
- [x] Task 5 — Creer la structure de tests (AC: #1)
  - [x] 5.1 Creer `tests/__init__.py`
  - [x] 5.2 Creer `tests/conftest.py` vide (pret pour les fixtures)
  - [x] 5.3 Creer `tests/test_init.py` — verifie que `bookforge` est importable et que `__version__` existe
- [x] Task 6 — Valider le squelette (AC: #1)
  - [x] 6.1 Executer `uv run ruff check .` — doit passer sans erreur
  - [x] 6.2 Executer `uv run pytest` — doit passer sans erreur
  - [x] 6.3 Verifier que `uv run python -c "from bookforge import __version__; print(__version__)"` fonctionne

## Dev Notes

### Contexte du projet

BookForge est un pipeline CLI Python qui transforme des manuscrits Markdown en PDF (via Typst) et EPUB (via Pandoc) conformes aux standards KDP print-on-demand. Cette story pose les fondations du projet.

**IMPORTANT :** Le depot actuel est un projet Node.js (BMad Method). BookForge sera un projet Python **a la racine** du depot. Le `pyproject.toml` coexistera avec le `package.json` existant.

### Stack technique exacte

| Composant | Version | Role |
|-----------|---------|------|
| Python | >= 3.10 (3.12 recommande) | Runtime |
| uv | 0.11.x (derniere stable) | Gestionnaire de paquets et d'environnements |
| Hatchling | latest + hatch-vcs | Build system |
| Typer | >= 0.9.0 | Framework CLI |
| Pydantic | >= 2.12 | Validation config |
| markdown-it-py | latest | Parsing Markdown |
| matplotlib | latest | Generation couverture |
| PyYAML | latest | Parsing YAML |
| Ruff | latest (dev) | Linting + formatting |
| mypy | latest (dev) | Type checking |
| pytest | latest (dev) | Tests |

### Contraintes architecturales

- **Paths :** Utiliser `pathlib.Path` partout. Jamais `os.path` ni concatenation de strings.
- **Logging :** `logging.getLogger("bookforge.<module>")` — jamais `print()`.
- **Messages utilisateur :** En francais, via exceptions. Logging interne en anglais.
- **Imports :** Ordre enforce par Ruff : stdlib → third-party → bookforge.
- **Shell :** Jamais `shell=True` dans subprocess.
- **Determinisme :** Versions pinees via `uv.lock` (NFR5).
- **Cross-platform :** Doit fonctionner Windows, macOS, Linux (NFR14).

### Configuration pyproject.toml attendue

```toml
[build-system]
requires = ["hatchling", "hatch-vcs"]
build-backend = "hatchling.build"

[project]
name = "bookforge"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "typer",
    "matplotlib",
    "pyyaml",
    "pydantic>=2.12",
    "markdown-it-py",
]

[project.scripts]
bookforge = "bookforge.cli:app"

[dependency-groups]
dev = ["pytest", "ruff", "mypy"]

[tool.ruff]
line-length = 100

[tool.mypy]
python_version = "3.10"
strict = true

[tool.pytest.ini_options]
testpaths = ["tests"]
```

> Note : `uv add --dev` utilise les dependency-groups (PEP 735) par defaut. Adapter la syntaxe si uv genere `[project.optional-dependencies]` a la place.

### Structure de fichiers a creer

```
(racine du depot)
├── pyproject.toml
├── uv.lock
├── src/
│   └── bookforge/
│       ├── __init__.py      # __version__ = "0.1.0"
│       └── cli.py           # Typer app minimal
└── tests/
    ├── __init__.py
    ├── conftest.py
    └── test_init.py         # Test import + version
```

### Ce que cette story ne fait PAS

- Ne cree PAS la structure complete des modules (config/, parser/, etc.) → Story 1.2
- Ne cree PAS les classes d'erreurs (BookForgeError, etc.) → Story 1.2
- Ne cree PAS le CI GitHub Actions → Story 1.3
- Ne cree PAS `run_external()` → Story 1.2
- Ne cree PAS de fixtures de test complexes → Stories suivantes

### Pieges a eviter

1. **Ne pas utiliser `uv init` dans un sous-dossier** — Le projet Python doit etre a la racine pour que `uv run` fonctionne correctement avec le depot.
2. **Ne pas oublier hatch-vcs** dans les build-system requires si le versioning Git est souhaite.
3. **Ne pas ajouter de dependances non listees** — Le budget est de < 5 runtime (NFR13). Respecter la liste exacte.
4. **Ne pas creer de `setup.py` ou `setup.cfg`** — pyproject.toml est le fichier unique de configuration.
5. **Verifier que Ruff passe** avant de considerer la story comme terminee — inclut formatting et linting.
6. **Ne pas creer de `__main__.py`** pour l'instant — le point d'entree CLI sera configure via `[project.scripts]`.

### Project Structure Notes

- Le `pyproject.toml` BookForge coexiste avec `package.json` (Node.js/BMad) a la racine.
- Le dossier `src/bookforge/` est distinct de `src/bmm-skills/` et `src/core-skills/` existants.
- Le dossier `tests/` pour BookForge (pytest) est distinct de `test/` existant (Node.js).
- `.gitignore` existant devrait deja ignorer `__pycache__/`, `.venv/`, etc. Verifier et completer si necessaire.

### References

- [Source: _bmad-output/planning-artifacts/architecture.md — Section "Decision 1: Language & Runtime", "Decision 3: Build System", "Decision 5: Dependency Management"]
- [Source: _bmad-output/planning-artifacts/architecture.md — Section "Arborescence cible"]
- [Source: _bmad-output/planning-artifacts/architecture.md — Section "Conventions de nommage"]
- [Source: _bmad-output/planning-artifacts/epics.md — Epic 1, Story 1.1]
- [Source: _bmad-output/planning-artifacts/prd.md — NFR13 (dependances < 5), NFR14 (cross-platform), NFR15 (installation 3 commandes)]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

- `uv init --lib --name bookforge` utilise `uv_build` par defaut, remplace par Hatchling manuellement dans pyproject.toml
- `ruff check .` captait les fichiers Python du projet BMad existant — ajoute `include` dans `[tool.ruff]` pour limiter au scope BookForge
- `requires-python` genere par uv a `>=3.13` (version locale), corrige a `>=3.10` comme specifie dans l'architecture
- `.gitignore` complete avec `.venv/`, `.mypy_cache/`, `*.egg-info/`, `dist/`

### Completion Notes List

- Projet initialise via `uv init --lib` a la racine du depot
- Build system configure avec Hatchling + hatch-vcs
- 5 dependances runtime installees : typer 0.24.1, pydantic 2.12.5, markdown-it-py 4.0.0, matplotlib 3.10.8, pyyaml 6.0.3
- 3 dependances dev installees : pytest 9.0.2, ruff 0.15.9, mypy 1.20.0
- Entry point CLI configure : `bookforge = "bookforge.cli:app"`
- Ruff, mypy, pytest configures dans pyproject.toml
- 3 tests unitaires creees et passent (import, version, format semver)
- `uv run ruff check .` passe sans erreur
- `uv run pytest` passe — 3/3 tests OK

### Change Log

- 2026-04-06 : Implementation initiale Story 1.1 — squelette projet BookForge

### File List

- pyproject.toml (nouveau)
- uv.lock (nouveau)
- src/bookforge/__init__.py (modifie — __version__)
- src/bookforge/cli.py (nouveau)
- tests/__init__.py (nouveau)
- tests/conftest.py (nouveau)
- tests/test_init.py (nouveau)
- .gitignore (modifie — ajout entrees Python)
