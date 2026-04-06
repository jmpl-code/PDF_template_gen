# Story 2.1 : Parsing et validation de book.yaml

Status: review

## Story

As a auteur,
I want definir mon livre via `book.yaml` et recevoir des messages d'erreur clairs si la config est invalide,
so that je sais exactement quoi corriger avant de lancer le pipeline.

## Acceptance Criteria

1. **Given** un fichier `book.yaml` avec titre, sous-titre, auteur, genre, chapitres, **When** le systeme parse et valide la configuration via Pydantic v2, **Then** un objet `BookConfig` valide est retourne avec tous les champs types
2. **And** si un champ obligatoire manque, une `InputError` est levee avec un message en francais indiquant le champ manquant
3. **And** si un fichier chapitre reference n'existe pas, une `InputError` est levee avec le chemin du fichier

## Tasks / Subtasks

- [x] Task 1 : Implementer les modeles Pydantic dans `config/schema.py` (AC: #1)
  - [x] 1.1 Creer le modele `ChapterConfig` (titre, fichier .md)
  - [x] 1.2 Creer le modele `BookConfig` (titre, sous-titre, auteur, genre, chapitres, ISBN optionnel, dedicace optionnelle)
  - [x] 1.3 Configurer les messages d'erreur Pydantic en francais
- [x] Task 2 : Implementer la validation dans `config/validator.py` (AC: #1, #2, #3)
  - [x] 2.1 Fonction `load_book_config(path: Path) -> BookConfig` : lire YAML, valider via Pydantic
  - [x] 2.2 Validation existence des fichiers chapitres references (chemins relatifs au book.yaml)
  - [x] 2.3 Wrapper les `ValidationError` Pydantic en `InputError` avec messages francais actionnables
- [x] Task 3 : Exporter dans `config/__init__.py` (AC: #1)
  - [x] 3.1 Exporter `BookConfig`, `ChapterConfig`, `load_book_config`
- [x] Task 4 : Ecrire les tests (AC: #1, #2, #3)
  - [x] 4.1 Creer la fixture `tests/fixtures/books/minimal/book.yaml` (config valide minimale)
  - [x] 4.2 Creer la fixture `tests/fixtures/books/minimal/chapitre-01.md` (chapitre minimal)
  - [x] 4.3 Creer des fixtures broken : `tests/fixtures/books/broken/missing-title.yaml`, `missing-chapters.yaml`, `missing-file-ref.yaml`
  - [x] 4.4 `test_config_valid_book_yaml_returns_book_config()`
  - [x] 4.5 `test_config_missing_required_field_raises_input_error()`
  - [x] 4.6 `test_config_missing_chapter_file_raises_input_error()`
  - [x] 4.7 `test_config_optional_fields_default_none()`
  - [x] 4.8 `test_config_chapter_paths_resolved_relative_to_yaml()`

## Dev Notes

### Contexte technique

- **Pydantic** : v2.12.5+ (deja dans `pyproject.toml`). Utiliser `BaseModel`, `field_validator`, `model_validator`
- **PyYAML** : v6.0.3+ (deja dans `pyproject.toml`). Utiliser `yaml.safe_load()`
- **Erreurs** : `InputError` definie dans `bookforge/errors.py` (exit_code=1)
- **Modules cibles** : `src/bookforge/config/schema.py` et `src/bookforge/config/validator.py` (fichiers existants, actuellement vides sauf docstring)
- **Export** : `src/bookforge/config/__init__.py` (actuellement vide sauf docstring)

### Schema `book.yaml` attendu (FR1)

```yaml
# book.yaml — exemple minimal
titre: "Mon Livre Business"
sous_titre: "Un guide pratique"      # optionnel
auteur: "JM"
genre: "business"
isbn: "978-2-1234-5678-9"            # optionnel
dedicace: "A tous les entrepreneurs" # optionnel

chapitres:
  - titre: "Introduction"
    fichier: "chapitres/01-introduction.md"
  - titre: "Chapitre 1"
    fichier: "chapitres/02-chapitre-1.md"
```

### Implementation `config/schema.py`

```python
from pathlib import Path
from pydantic import BaseModel, field_validator

class ChapterConfig(BaseModel):
    titre: str
    fichier: str  # chemin relatif au book.yaml, resolu en Path par le validator

class BookConfig(BaseModel):
    titre: str
    sous_titre: str | None = None
    auteur: str
    genre: str
    isbn: str | None = None
    dedicace: str | None = None
    chapitres: list[ChapterConfig]

    @field_validator('chapitres')
    @classmethod
    def chapitres_non_vide(cls, v: list[ChapterConfig]) -> list[ChapterConfig]:
        if not v:
            raise ValueError("La liste des chapitres ne peut pas etre vide")
        return v
```

**Points critiques :**
- Cles `book.yaml` en `snake_case` (convention architecture : `font_size`, `margin_inner`)
- `chapitres` : liste non vide (au moins 1 chapitre requis)
- Champs optionnels avec `| None = None` (syntaxe Python 3.10+)
- **NE PAS** ajouter de champs non specifies dans les AC (pas de `description`, `mots_cles`, `categories` — ceux-ci viendront dans une story ulterieure FR19)

### Implementation `config/validator.py`

```python
import logging
from pathlib import Path
import yaml
from pydantic import ValidationError
from bookforge.config.schema import BookConfig
from bookforge.errors import InputError

logger = logging.getLogger("bookforge.config")

def load_book_config(path: Path) -> BookConfig:
    """Charge et valide un fichier book.yaml."""
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
        # Traduire les erreurs Pydantic en messages francais actionnables
        messages = []
        for err in e.errors():
            field = " -> ".join(str(loc) for loc in err["loc"])
            messages.append(f"  - {field} : {err['msg']}")
        raise InputError(
            f"Configuration invalide dans '{path}' :\n" + "\n".join(messages)
        )
    # Valider existence des fichiers chapitres
    book_dir = path.parent
    for chap in config.chapitres:
        chap_path = book_dir / chap.fichier
        if not chap_path.exists():
            raise InputError(
                f"Fichier chapitre introuvable : '{chap.fichier}' "
                f"(resolu en '{chap_path}')"
            )
    return config
```

**Points critiques :**
- Chemins relatifs resolus par rapport au **parent du book.yaml** (pas le CWD)
- `pathlib.Path` partout, jamais `os.path` (convention architecture)
- `yaml.safe_load()` (securite — jamais `yaml.load()`)
- Encoding `utf-8` explicite pour cross-platform (Windows = cp1252 par defaut)
- Logger : `logging.getLogger("bookforge.config")` (convention : un logger par module)
- Messages utilisateur en francais via `InputError`, logging interne en anglais

### Anti-patterns a eviter

- **NE PAS** utiliser `os.path` — `pathlib.Path` uniquement
- **NE PAS** utiliser `yaml.load()` — `yaml.safe_load()` uniquement (securite)
- **NE PAS** utiliser `print()` — logging ou exceptions uniquement
- **NE PAS** ajouter de `try/except` generique — catcher specifiquement `ValidationError` et `YAMLError`
- **NE PAS** ajouter des champs FR19 (description, mots_cles, categories) — hors scope story 2.1
- **NE PAS** creer de classes `@dataclass` pour la config — Pydantic `BaseModel` uniquement (decision architecture #4)
- **NE PAS** faire de validation DPI ou d'images ici — c'est la responsabilite du parser (story 2.2) et quality (FR31)

### Patterns du projet etablis (stories 1.1-1.3)

- **Nommage tests** : `test_<quoi>_<condition>_<attendu>()` (ex: `test_parser_missing_image_raises_input_error`)
- **Fixtures** : dans `tests/fixtures/`, jamais inline
- **Imports** : ordre stdlib → third-party → bookforge (Ruff enforce)
- **Classes de test** : regroupees par `class TestXxx:` quand logique (cf. `test_errors.py`)
- **Type hints** : systematiques, mypy strict=true
- **Docstrings** : une ligne en francais en haut du module, pas de docstring sur chaque fonction de test

### Structure des fichiers a creer/modifier

```
src/bookforge/config/
├── __init__.py          # MODIFIER : exporter BookConfig, ChapterConfig, load_book_config
├── schema.py            # MODIFIER : implementer les modeles Pydantic
└── validator.py         # MODIFIER : implementer load_book_config()

tests/
├── fixtures/
│   └── books/
│       ├── minimal/
│       │   ├── book.yaml         # CREER
│       │   └── chapitres/
│       │       └── 01-introduction.md  # CREER
│       └── broken/
│           ├── missing-title.yaml      # CREER
│           ├── missing-chapters.yaml   # CREER
│           └── missing-file-ref.yaml   # CREER
└── test_config.py                # CREER
```

### Apprentissages des stories precedentes

- **Story 1.1** : Ruff scope `include` limite a `src/bookforge/**/*.py` et `tests/**/*.py` — pas de souci de linting sur les fichiers non-Python
- **Story 1.1** : `requires-python = ">=3.10"` — syntaxe `str | None` autorisee
- **Story 1.2** : 31 tests passants, structure complete des modules en place, `errors.py` et `external.py` fonctionnels
- **Story 1.2** : Pattern `BookForgeError` avec `exit_code` comme attribut de classe (pas de `__init__` custom pour exit_code)
- **Story 1.3** : CI fonctionnelle, `uv run ruff check .`, `uv run mypy src/bookforge/`, `uv run pytest` — tout doit passer apres implementation
- **Story 1.3** : 31 tests existants — les nouveaux tests s'ajoutent, aucun test existant ne doit etre modifie

### Git intelligence

- Dernier commit : `cf240179 feat(bookforge): implement Epic 1` — commit monolithique pour tout l'Epic 1
- Structure existante : tous les fichiers `config/schema.py`, `config/validator.py`, `config/__init__.py` existent avec un docstring placeholder
- Aucune dependance nouvelle a ajouter (Pydantic et PyYAML deja dans pyproject.toml)

### Dependances de cette story

- **Prerequis** : Story 1.2 (structure modules + errors.py) — DONE
- **Bloque** : Story 2.2 (parser Markdown) — a besoin de `BookConfig` pour les chemins chapitres

### Project Structure Notes

- Les fichiers cibles existent deja avec un docstring placeholder — les enrichir, ne pas les recreer
- Le dossier `tests/fixtures/books/` n'existe pas encore — le creer avec la structure minimal/ et broken/
- La convention projet est monorepo (Node.js + Python) — travailler uniquement dans `src/bookforge/` et `tests/`

### References

- [Source: _bmad-output/planning-artifacts/architecture.md — Decision 4 : Validation config Pydantic v2, lignes 318-322]
- [Source: _bmad-output/planning-artifacts/architecture.md — Naming Patterns, lignes 405-424]
- [Source: _bmad-output/planning-artifacts/architecture.md — Communication Patterns, lignes 476-498]
- [Source: _bmad-output/planning-artifacts/architecture.md — Project Structure, lignes 555-640]
- [Source: _bmad-output/planning-artifacts/epics.md — Epic 2, Story 2.1, lignes 258-269]
- [Source: _bmad-output/planning-artifacts/prd.md — FR1, FR5, FR49-50]
- [Source: _bmad-output/implementation-artifacts/1-3-ci-github-actions.md — Apprentissages stories precedentes]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

- mypy exigeait `types-pyyaml` pour les stubs PyYAML — ajout en dep dev (`uv add --dev types-pyyaml`)
- 39 tests total (31 existants + 8 nouveaux), zero regression

### Completion Notes List

- `config/schema.py` : modeles Pydantic v2 `BookConfig` et `ChapterConfig` avec `field_validator` pour chapitres non vide
- `config/validator.py` : `load_book_config()` charge YAML, valide via Pydantic, verifie existence fichiers chapitres, messages d'erreur en francais
- `config/__init__.py` : exports `BookConfig`, `ChapterConfig`, `load_book_config`
- 8 tests couvrant les 3 AC : config valide, champs optionnels, resolution chemins, champ manquant, chapitres manquants, fichier reference manquant, fichier inexistant, chapitres vide
- Ajout `types-pyyaml` en dep dev pour mypy strict
- Ruff clean, mypy 0 erreurs, pytest 39/39 passed

### File List

- `src/bookforge/config/schema.py` (modified)
- `src/bookforge/config/validator.py` (modified)
- `src/bookforge/config/__init__.py` (modified)
- `tests/test_config.py` (new)
- `tests/fixtures/books/minimal/book.yaml` (new)
- `tests/fixtures/books/minimal/chapitres/01-introduction.md` (new)
- `tests/fixtures/books/broken/missing-title.yaml` (new)
- `tests/fixtures/books/broken/missing-chapters.yaml` (new)
- `tests/fixtures/books/broken/missing-file-ref.yaml` (new)
- `pyproject.toml` (modified — types-pyyaml dev dep)
- `uv.lock` (modified)

### Change Log

- 2026-04-06 : Implementation complete Story 2.1 — parsing et validation book.yaml via Pydantic v2
