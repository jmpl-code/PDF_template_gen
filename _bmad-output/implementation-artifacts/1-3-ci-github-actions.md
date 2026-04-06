# Story 1.3 : CI GitHub Actions

Status: review

## Story

As a auteur-developpeur,
I want un pipeline CI qui execute ruff, mypy et pytest a chaque push,
so that la qualite du code est verifiee automatiquement.

## Acceptance Criteria

1. **Given** le projet avec sa structure (Story 1.2), **When** un push est effectue sur le depot, **Then** GitHub Actions execute `ruff check`, `mypy`, et `pytest`
2. **And** le workflow fonctionne sur Python 3.10+ et les trois OS (Windows, macOS, Linux)
3. **And** le pipeline echoue si un check ne passe pas

## Tasks / Subtasks

- [x] Task 1 : Creer le fichier workflow GitHub Actions (AC: #1, #2, #3)
  - [x] 1.1 Creer `.github/workflows/python-ci.yml` avec trigger on push et pull_request
  - [x] 1.2 Configurer la matrice OS : `[ubuntu-latest, macos-latest, windows-latest]`
  - [x] 1.3 Configurer la matrice Python : `["3.10", "3.11", "3.12", "3.13"]`
  - [x] 1.4 Configurer les etapes : checkout, setup-uv (avec python-version), `uv sync`, ruff check, mypy, pytest
  - [x] 1.5 S'assurer que chaque etape echoue le pipeline en cas d'erreur (pas de `continue-on-error`)
- [x] Task 2 : Valider le workflow localement (AC: #1, #3)
  - [x] 2.1 Verifier que `uv run ruff check .` passe sans erreur
  - [x] 2.2 Verifier que `uv run mypy src/bookforge/` passe sans erreur
  - [x] 2.3 Verifier que `uv run pytest` passe (31 tests existants)
- [x] Task 3 : Tester le workflow sur les 3 OS (AC: #2)
  - [x] 3.1 Valider la syntaxe YAML du workflow (pas d'erreurs de parsing)
  - [x] 3.2 Verifier la compatibilite cross-platform des commandes (pas de commandes bash-only)

## Dev Notes

### Contexte technique

- **Package manager** : `uv` (pas pip). Utiliser `astral-sh/setup-uv@v6` pour l'installer dans CI
- **Build backend** : Hatchling (pas uv_build)
- **Python min** : `>=3.10` (defini dans pyproject.toml)
- **.python-version** : 3.13 (version locale de dev)
- **30 tests** actuellement en place et passants

### Workflows existants

Le depot contient deja 5 workflows Node.js dans `.github/workflows/` :
- `quality.yaml` — prettier, eslint, markdownlint (Node.js uniquement)
- `publish.yaml` — publication npm
- `docs.yaml` — build documentation Astro + deploy GitHub Pages
- `discord.yaml` — notifications Discord
- `coderabbit-review.yaml` — review IA CodeRabbit

**IMPORTANT** : Creer un NOUVEAU fichier `python-ci.yml` dedie au Python. Ne PAS modifier `quality.yaml` existant.

### Commandes CI exactes

```bash
uv sync                        # Installe deps + dev deps depuis uv.lock
uv run ruff check .            # Lint (scope: src/bookforge/**/*.py, tests/**/*.py via pyproject.toml)
uv run mypy src/bookforge/     # Type check strict (python_version = "3.10")
uv run pytest                  # Tests (testpaths = ["tests"])
```

### Configuration outils (deja dans pyproject.toml)

- **Ruff** : line-length=100, rules E/F/W/I/N/UP, include scoped to bookforge+tests
- **mypy** : strict=true, python_version="3.10"
- **pytest** : testpaths=["tests"]

### Pattern du workflow

```yaml
name: Python CI

on:
  push:
    branches: [main]
    paths:
      - "src/bookforge/**"
      - "tests/**"
      - "pyproject.toml"
      - "uv.lock"
      - ".github/workflows/python-ci.yml"
  pull_request:
    paths:
      - "src/bookforge/**"
      - "tests/**"
      - "pyproject.toml"
      - "uv.lock"
      - ".github/workflows/python-ci.yml"

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v6
      - run: uv sync
      - run: uv run ruff check .

  typecheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v6
      - run: uv sync
      - run: uv run mypy src/bookforge/

  test:
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ["3.10", "3.11", "3.12", "3.13"]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - uses: astral-sh/setup-uv@v6
      - run: uv sync
      - run: uv run pytest
```

### Decisions architecturales

- **Lint et typecheck** sur ubuntu-latest uniquement (resultats identiques sur tous OS)
- **Tests** sur matrice complete OS x Python (detecter les incompatibilites cross-platform)
- `uv sync` utilise `uv.lock` pour le determinisme (NFR5)
- `setup-python` avant `setup-uv` pour les jobs tests (force la version Python de la matrice)
- Pas de cache uv pour simplifier le premier setup (peut etre ajoute plus tard)

### Anti-patterns a eviter

- Ne PAS utiliser `pip install` — toujours `uv sync`
- Ne PAS utiliser `shell: bash` sur les commandes cross-platform — laisser le default
- Ne PAS ajouter `continue-on-error: true` — le pipeline DOIT echouer
- Ne PAS utiliser `uv run python -m pytest` — `uv run pytest` suffit
- Ne PAS modifier les workflows Node.js existants

### Apprentissages des stories precedentes

- **Story 1.1** : Ruff scope `include` limite a `src/bookforge/**/*.py` et `tests/**/*.py` pour eviter de linter les fichiers BMad
- **Story 1.1** : `requires-python` corrige manuellement a `>=3.10` (uv genere la version locale)
- **Story 1.1** : Build system = Hatchling (pas uv_build comme genere par defaut)
- **Story 1.2** : 30 tests passants, zero erreurs ruff, structure complete des modules

### Project Structure Notes

- Le workflow doit coexister avec les workflows Node.js existants
- Filtrage par `paths:` pour ne declencher que sur les fichiers Python pertinents
- Le projet est un monorepo avec Node.js (BMad) et Python (BookForge)

### References

- [Source: _bmad-output/planning-artifacts/architecture.md — Section "Configuration as Code", lignes 561-567]
- [Source: _bmad-output/planning-artifacts/architecture.md — Section "Pattern Enforcement", lignes 549-553]
- [Source: _bmad-output/planning-artifacts/architecture.md — Section "Selected Starter", lignes 213-246]
- [Source: _bmad-output/planning-artifacts/epics.md — Epic 1, Story 1.3]
- [Source: _bmad-output/implementation-artifacts/1-1-initialisation-du-projet-avec-le-starter-template.md — Dev Notes, Debug Log]
- [Source: _bmad-output/implementation-artifacts/1-2-structure-des-modules-et-erreurs-de-base.md — Completion Notes]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

- Story dev notes referenciaient `astral-sh/setup-uv@v6` et `actions/checkout@v4`, mais la doc Context7 confirme que les versions actuelles sont `@v7` et `@v5` respectivement — workflow cree avec les versions a jour.
- `setup-uv@v7` integre nativement le parametre `python-version`, rendant `actions/setup-python` inutile pour les jobs test.
- 31 tests (et non 30 comme prevu dans la story) — Story 1.2 en avait cree 1 de plus que documente.

### Completion Notes List

- Workflow `.github/workflows/python-ci.yml` cree avec 3 jobs : lint (ruff), typecheck (mypy), test (matrice 3 OS x 4 Python)
- Validation locale OK : ruff clean, mypy 0 issues (35 fichiers), pytest 31/31 passed
- Syntaxe YAML validee via PyYAML
- Toutes les commandes sont cross-platform (uv sync, uv run ruff/mypy/pytest)
- Aucun `continue-on-error` — pipeline echoue sur tout check rate

### File List

- `.github/workflows/python-ci.yml` (new)

### Change Log

- 2026-04-06 : Creation du workflow CI Python avec matrice OS x Python, jobs lint/typecheck/test
