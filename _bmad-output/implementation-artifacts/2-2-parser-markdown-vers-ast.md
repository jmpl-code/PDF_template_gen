# Story 2.2 : Parser Markdown vers AST

Status: review

## Story

As a auteur,
I want que mes fichiers Markdown soient parses en un AST structure,
so that le contenu est represente de maniere exploitable par les renderers.

## Acceptance Criteria

1. **Given** des fichiers Markdown references dans `book.yaml`, **When** le parser traite les fichiers via markdown-it-py, **Then** un `BookNode` (AST frozen) est produit avec `ChapterNode`, `HeadingNode`, `ParagraphNode`, `ImageNode`, `TableNode`
2. **And** chaque noeud porte `source_file` et `line_number` pour la tracabilite
3. **And** les chemins d'images sont resolus en absolu relatifs au fichier Markdown source
4. **And** si une image referencee n'existe pas, une `InputError` est levee
5. **And** les golden files de test verifient la stabilite de l'AST produit

## Tasks / Subtasks

- [x] Task 1 : Definir les noeuds AST dans `ast_nodes/` (AC: #1, #2)
  - [x] 1.1 `ast_nodes/base.py` : type union `ASTNode`, type alias pour les enfants
  - [x] 1.2 `ast_nodes/content.py` : `ParagraphNode`, `ImageNode`, `TableNode` (frozen dataclasses avec `source_file`, `line_number`)
  - [x] 1.3 `ast_nodes/structure.py` : `BookNode`, `ChapterNode`, `HeadingNode` (frozen dataclasses, enfants en `tuple`)
  - [x] 1.4 `ast_nodes/__init__.py` : exporter tous les noeuds
- [x] Task 2 : Implementer le parser markdown-it-py dans `parser/markdown.py` (AC: #1)
  - [x] 2.1 Fonction `parse_markdown_file(path: Path) -> list[Token]` : lire un fichier .md et retourner les tokens markdown-it-py
  - [x] 2.2 Configurer markdown-it-py en mode `commonmark` avec support tables
- [x] Task 3 : Implementer la transformation tokens -> AST dans `parser/transform.py` (AC: #1, #2, #3, #4)
  - [x] 3.1 Fonction `tokens_to_ast(tokens: list[Token], source_file: Path) -> list[ASTNode]` : convertir les tokens en noeuds AST
  - [x] 3.2 Mapper les types de tokens : `paragraph_open` -> `ParagraphNode`, `heading_open` -> `HeadingNode`, `image` -> `ImageNode`, `table_open` -> `TableNode`
  - [x] 3.3 Extraire `line_number` depuis `token.map` (paire [line_start, line_end])
  - [x] 3.4 Resoudre les chemins d'images en absolu relatifs au fichier Markdown source
  - [x] 3.5 Lever `InputError` si une image referencee n'existe pas
- [x] Task 4 : Implementer le point d'entree dans `parser/__init__.py` (AC: #1, #3, #4)
  - [x] 4.1 Fonction `parse_book(config: BookConfig) -> BookNode` : iterer les chapitres, parser chaque .md, assembler le BookNode
  - [x] 4.2 Resoudre les chemins chapitres relatifs au book.yaml (via `BookConfig`)
- [x] Task 5 : Ecrire les tests et golden files (AC: #1, #2, #3, #4, #5)
  - [x] 5.1 Creer fixture `tests/fixtures/books/minimal/chapitres/01-introduction.md` enrichi (headings, paragraphes, image, table)
  - [x] 5.2 Creer fixture image `tests/fixtures/books/minimal/images/diagram.png` (fichier PNG minimal)
  - [x] 5.3 Creer golden file `tests/fixtures/golden/minimal-ast.json` (representation JSON de l'AST attendu)
  - [x] 5.4 `test_parser_valid_markdown_returns_book_node()`
  - [x] 5.5 `test_parser_nodes_carry_source_file_and_line_number()`
  - [x] 5.6 `test_parser_image_paths_resolved_absolute()`
  - [x] 5.7 `test_parser_missing_image_raises_input_error()`
  - [x] 5.8 `test_parser_golden_file_ast_stability()`
  - [x] 5.9 `test_parser_heading_levels_preserved()`
  - [x] 5.10 `test_parser_table_parsed_correctly()`

## Dev Notes

### Contexte technique

- **markdown-it-py** : v4.0.0+ (deja dans `pyproject.toml`). Parser CommonMark robuste avec support extensions
- **Erreurs** : `InputError` definie dans `bookforge/errors.py` (exit_code=1)
- **Modules cibles** : `src/bookforge/ast_nodes/` (4 fichiers) et `src/bookforge/parser/` (3 fichiers) — tous existent avec docstring placeholder
- **Prerequis** : `BookConfig` et `ChapterConfig` de Story 2.1 (DONE) — utiliser `from bookforge.config import BookConfig`

### Architecture AST — Decision 1

L'AST BookForge est un **hybride** : markdown-it-py (front-end parsing) → dataclasses custom typees (IR).

**Regles imperatives (architecture.md) :**
- Tous les noeuds `@dataclass(frozen=True)` — immutabilite du triplet architectural
- Enfants en `tuple[ASTNode, ...]`, jamais `list`
- Chaque noeud porte `source_file: Path` + `line_number: int` pour la tracabilite erreurs
- Nommage : suffixe `Node` obligatoire (`ChapterNode`, `ParagraphNode`, etc.)

### Noeuds AST a implementer

```python
# ast_nodes/base.py
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Union

# Type union de tous les noeuds (defini apres les imports circulaires resolus)
ASTNode = Union["HeadingNode", "ParagraphNode", "ImageNode", "TableNode"]

# ast_nodes/structure.py
@dataclass(frozen=True)
class HeadingNode:
    level: int                        # 1-6
    text: str
    source_file: Path
    line_number: int

@dataclass(frozen=True)
class ChapterNode:
    title: str
    children: tuple[ASTNode, ...]
    source_file: Path
    line_number: int

@dataclass(frozen=True)
class BookNode:
    title: str
    chapters: tuple[ChapterNode, ...]

# ast_nodes/content.py
@dataclass(frozen=True)
class ParagraphNode:
    text: str
    source_file: Path
    line_number: int

@dataclass(frozen=True)
class ImageNode:
    src: Path                         # Chemin ABSOLU resolu
    alt: str
    source_file: Path
    line_number: int

@dataclass(frozen=True)
class TableNode:
    headers: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]
    source_file: Path
    line_number: int
```

### API markdown-it-py

```python
from markdown_it import MarkdownIt

# Initialiser avec CommonMark + tables
md = MarkdownIt("commonmark").enable("table")
tokens = md.parse(markdown_text)

# Chaque token a :
# - token.type : "paragraph_open", "heading_open", "image", "table_open", etc.
# - token.tag : "p", "h1", "img", "table", etc.
# - token.nesting : 1 (open), 0 (self-closing), -1 (close)
# - token.map : [line_start, line_end] ou None
# - token.children : list[Token] pour les tokens inline
# - token.content : texte brut pour certains types
# - token.attrs : dict pour les attributs (ex: image src, alt)
```

**Points critiques :**
- Les tokens `inline` contiennent des `children` avec le texte reel
- Les tokens `heading_open` ont un `tag` "h1"-"h6" → extraire le level
- Les tokens `image` sont des enfants de tokens `inline`, avec `attrs["src"]` et `children[0].content` (alt)
- Les tokens `table_open` / `thead_open` / `tbody_open` / `tr_open` / `th_open` / `td_open` structurent les tables
- `token.map` donne `[line_start, line_end]` (0-indexed) → utiliser `line_start + 1` pour 1-indexed

### Implementation `parser/markdown.py`

```python
import logging
from pathlib import Path
from markdown_it import MarkdownIt
from markdown_it.token import Token
from bookforge.errors import InputError

logger = logging.getLogger("bookforge.parser")

def parse_markdown_file(path: Path) -> list[Token]:
    """Parse un fichier Markdown et retourne les tokens markdown-it-py."""
    if not path.exists():
        raise InputError(f"Fichier Markdown introuvable : {path}")
    text = path.read_text(encoding="utf-8")
    md = MarkdownIt("commonmark").enable("table")
    return md.parse(text)
```

### Implementation `parser/transform.py` — Strategie de transformation

La transformation est un **parcours sequentiel** des tokens (pas recursif) :
1. Iterer les tokens au top-level
2. Pour `heading_open` : lire le token inline suivant pour le texte
3. Pour `paragraph_open` : lire le token inline suivant pour le texte
4. Pour `image` (dans les enfants inline) : extraire src, alt, resoudre chemin
5. Pour `table_open` : collecter tous les tokens jusqu'a `table_close`, extraire headers et rows
6. `line_number` = `token.map[0] + 1` si `token.map` existe, sinon 0

**Resolution chemins images :**
- `src` est relatif au fichier .md source
- Resoudre : `source_file.parent / src` → `.resolve()` pour absolu
- Verifier existence → `InputError` si manquant

### Implementation `parser/__init__.py`

```python
from pathlib import Path
from bookforge.config import BookConfig
from bookforge.ast_nodes import BookNode, ChapterNode
from bookforge.parser.markdown import parse_markdown_file
from bookforge.parser.transform import tokens_to_ast

def parse_book(config: BookConfig, book_dir: Path) -> BookNode:
    """Parse tous les chapitres d'un livre et retourne l'AST complet."""
    chapters = []
    for chap in config.chapitres:
        chap_path = (book_dir / chap.fichier).resolve()
        tokens = parse_markdown_file(chap_path)
        children = tokens_to_ast(tokens, chap_path)
        chapter = ChapterNode(
            title=chap.titre,
            children=tuple(children),
            source_file=chap_path,
            line_number=1,
        )
        chapters.append(chapter)
    return BookNode(title=config.titre, chapters=tuple(chapters))
```

**Point critique :** `book_dir` est le parent du fichier `book.yaml`, passe par le caller (cli ou pipeline).

### Golden files de test (AC #5)

Format JSON serialise de l'AST pour verifier la stabilite :
```json
{
  "type": "BookNode",
  "title": "Mon Livre Business",
  "chapters": [
    {
      "type": "ChapterNode",
      "title": "Introduction",
      "children": [
        {"type": "HeadingNode", "level": 1, "text": "Introduction", "line_number": 1},
        {"type": "ParagraphNode", "text": "Contenu...", "line_number": 3}
      ]
    }
  ]
}
```

Implementer une fonction utilitaire `ast_to_dict(node)` dans les tests pour serialiser l'AST en dict comparable, en excluant les chemins absolus (non portables).

### Anti-patterns a eviter

- **NE PAS** utiliser `SyntaxTreeNode` de markdown-it-py — on construit notre propre AST custom (decision architecture #1)
- **NE PAS** utiliser `os.path` — `pathlib.Path` uniquement
- **NE PAS** utiliser `list` pour les enfants AST — `tuple` uniquement (immutabilite)
- **NE PAS** utiliser `@dataclass` sans `frozen=True` — tous les noeuds sont immutables
- **NE PAS** parser les balises semantiques (`:::framework`, etc.) — c'est MVP1 (Story 4.3, `parser/semantic.py`)
- **NE PAS** ajouter de noeuds semantiques (`CalloutNode`, `FrameworkNode`) — hors scope story 2.2
- **NE PAS** gerer les inline styles (bold, italic) dans l'AST — le texte brut suffit pour MVP0

### Patterns du projet etablis (stories 1.1-2.1)

- **Nommage tests** : `test_<quoi>_<condition>_<attendu>()` (ex: `test_parser_missing_image_raises_input_error`)
- **Fixtures** : dans `tests/fixtures/`, jamais inline
- **Imports** : ordre stdlib → third-party → bookforge (Ruff enforce)
- **Classes de test** : regroupees par `class TestXxx:` quand logique
- **Type hints** : systematiques, mypy strict=true
- **Docstrings** : une ligne en francais en haut du module
- **Logging** : `logging.getLogger("bookforge.<module>")`, jamais `print()`
- **Messages utilisateur** : en francais via `InputError`
- **Logging interne** : en anglais

### Structure des fichiers a creer/modifier

```
src/bookforge/ast_nodes/
├── __init__.py          # MODIFIER : exporter tous les noeuds
├── base.py              # MODIFIER : type union ASTNode
├── content.py           # MODIFIER : ParagraphNode, ImageNode, TableNode
└── structure.py         # MODIFIER : BookNode, ChapterNode, HeadingNode

src/bookforge/parser/
├── __init__.py          # MODIFIER : exporter parse_book
├── markdown.py          # MODIFIER : parse_markdown_file()
└── transform.py         # MODIFIER : tokens_to_ast()

tests/
├── fixtures/
│   ├── books/
│   │   └── minimal/
│   │       ├── chapitres/
│   │       │   └── 01-introduction.md  # MODIFIER : enrichir avec headings, paragraphes, image, table
│   │       └── images/
│   │           └── diagram.png         # CREER : fichier PNG minimal
│   └── golden/
│       └── minimal-ast.json            # CREER : golden file AST
└── test_parser.py                      # CREER
```

### Apprentissages des stories precedentes

- **Story 2.1** : `BookConfig` et `ChapterConfig` disponibles via `from bookforge.config import BookConfig`
- **Story 2.1** : Chemins chapitres resolus relatifs au parent du book.yaml
- **Story 2.1** : `types-pyyaml` ajoute en dep dev pour mypy strict — verifier si `types-markdown-it-py` est necessaire
- **Story 2.1** : 39 tests passants — les nouveaux s'ajoutent, aucun existant ne doit etre modifie
- **Story 1.2** : Pattern `InputError` pour erreurs utilisateur, `RenderError` pour erreurs subprocess
- **Story 1.2** : `external.py` avec `run_external()` — pas utilise dans cette story

### Git intelligence

- Dernier commit : `d0a68b0a feat(bookforge): implement Story 2.1 — parsing et validation de book.yaml`
- 39 tests existants, ruff clean, mypy 0 erreurs
- Tous les fichiers ast_nodes/ et parser/ existent avec docstring placeholder
- `markdown-it-py>=4.0.0` deja dans pyproject.toml

### Dependances de cette story

- **Prerequis** : Story 2.1 (BookConfig + load_book_config) — DONE
- **Bloque** : Story 2.3 (renderer PDF) — a besoin du BookNode pour generer le .typ

### Project Structure Notes

- Les fichiers cibles existent deja avec un docstring placeholder — les enrichir, ne pas les recreer
- Le dossier `tests/fixtures/golden/` n'existe pas encore — le creer
- La fixture `tests/fixtures/books/minimal/chapitres/01-introduction.md` existe deja (story 2.1) — la modifier pour ajouter plus de contenu
- Le dossier `tests/fixtures/books/minimal/images/` n'existe pas encore — le creer

### References

- [Source: _bmad-output/planning-artifacts/architecture.md — Decision 1 : Representation AST, lignes 298-302]
- [Source: _bmad-output/planning-artifacts/architecture.md — Structure Patterns AST, lignes 428-442]
- [Source: _bmad-output/planning-artifacts/architecture.md — Project Structure ast_nodes/, lignes 588-592]
- [Source: _bmad-output/planning-artifacts/architecture.md — Project Structure parser/, lignes 582-586]
- [Source: _bmad-output/planning-artifacts/architecture.md — Decision 8 : Gestion assets, lignes 375-380]
- [Source: _bmad-output/planning-artifacts/epics.md — Epic 2, Story 2.2, lignes 271-285]
- [Source: _bmad-output/planning-artifacts/prd.md — FR2, FR4, FR6]
- [Source: _bmad-output/implementation-artifacts/2-1-parsing-et-validation-de-book-yaml.md — Completion Notes]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

- `token.attrGet()` retourne `str | int | float | None` — necessite cast `str()` explicite pour mypy strict
- `from __future__ import annotations` causait F821 avec `Union["HeadingNode", ...]` car ruff ne peut pas resoudre les forward refs entre modules — utilise `TYPE_CHECKING` guard a la place
- 2 tests supplementaires (immutabilite, tuples) ajoutes en bonus au-dela de la story pour valider les invariants architecturaux
- 48 tests total (39 existants + 9 nouveaux), zero regression

### Completion Notes List

- 6 noeuds AST frozen dataclasses : `BookNode`, `ChapterNode`, `HeadingNode`, `ParagraphNode`, `ImageNode`, `TableNode`
- Type union `ASTNode` avec `TYPE_CHECKING` guard pour compatibilite ruff/mypy
- `parse_markdown_file()` : markdown-it-py CommonMark + tables → tokens
- `tokens_to_ast()` : transformation sequentielle tokens → noeuds AST avec resolution images et validation existence
- `parse_book()` : point d'entree assemblant le BookNode depuis BookConfig
- 9 tests couvrant les 5 AC + golden file pour stabilite AST
- Ruff clean, mypy 0 erreurs, pytest 48/48 passed

### File List

- `src/bookforge/ast_nodes/base.py` (modified)
- `src/bookforge/ast_nodes/content.py` (modified)
- `src/bookforge/ast_nodes/structure.py` (modified)
- `src/bookforge/ast_nodes/__init__.py` (modified)
- `src/bookforge/parser/markdown.py` (modified)
- `src/bookforge/parser/transform.py` (modified)
- `src/bookforge/parser/__init__.py` (modified)
- `tests/test_parser.py` (new)
- `tests/fixtures/books/minimal/chapitres/01-introduction.md` (modified — enrichi)
- `tests/fixtures/books/minimal/images/diagram.png` (new)
- `tests/fixtures/golden/minimal-ast.json` (new)

### Change Log

- 2026-04-06 : Implementation complete Story 2.2 — parser Markdown vers AST via markdown-it-py
