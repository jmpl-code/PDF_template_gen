# Story 2.3 : Renderer PDF — Template Typst de base

Status: done

## Story

As a auteur,
I want que l'AST soit transforme en fichier Typst et compile en PDF,
so that j'obtiens un premier rendu PDF de mon manuscrit.

## Acceptance Criteria

1. **Given** un `BookNode` (AST) valide, **When** le renderer genere un fichier `.typ` et appelle `typst compile` via `run_external()`, **Then** un PDF valide est produit avec typographie conforme (interligne 120-140%, polices embarquees)
2. **And** le fichier `.typ` intermediaire est conserve pour debug
3. **And** les memes entrees produisent le meme PDF (determinisme NFR5)
4. **And** si Typst n'est pas installe, une `RenderError` claire est levee
5. **And** les golden files de test verifient la stabilite du `.typ` genere

## Tasks / Subtasks

- [x] Task 1 : Implementer le template Typst de base dans `templates/typst/base.typ` (AC: #1)
  - [x] 1.1 Configuration page : format 6x9 pouces (standard KDP), marges asymetriques (inside/outside pour reliure)
  - [x] 1.2 Configuration typographie : police serif (New Computer Modern), taille 11pt, interligne 1.3em (~130%), justifie
  - [x] 1.3 Configuration headings : styles h1-h4 avec espacement avant/apres
  - [x] 1.4 Placeholders Typst pour le contenu injecte par Python (commentaire de fin)

- [x] Task 2 : Implementer le generateur `.typ` dans `src/bookforge/renderers/pdf.py` (AC: #1, #2, #3)
  - [x] 2.1 Fonction `render_pdf(book: BookNode, output_dir: Path) -> Path` : point d'entree principal
  - [x] 2.2 Fonction `generate_typst(book: BookNode, output_path: Path) -> Path` : genere le fichier `.typ` a partir de l'AST
  - [x] 2.3 Fonction `compile_typst(typ_path: Path, pdf_path: Path) -> Path` : appelle `typst compile` via `run_external()`
  - [x] 2.4 Parcours de l'AST : `BookNode` -> chapitres -> noeuds enfants (HeadingNode, ParagraphNode, ImageNode, TableNode)
  - [x] 2.5 Echappement du contenu texte pour Typst (caracteres speciaux : `#`, `@`, `$`, `<`, `>`, backtick, `_`, `*`, `~`, `\`)
  - [x] 2.6 Conservation du fichier `.typ` intermediaire dans `output_dir` pour debug

- [x] Task 3 : Mettre a jour `src/bookforge/renderers/__init__.py` (AC: #1)
  - [x] 3.1 Exporter `render_pdf` depuis le module renderers

- [x] Task 4 : Ecrire les tests dans `tests/test_renderer_pdf.py` (AC: #1, #2, #3, #4, #5)
  - [x] 4.1 `test_generate_typst_valid_ast_produces_typ_file()` — verifie que le `.typ` est cree
  - [x] 4.2 `test_generate_typst_content_matches_golden_file()` — golden file pour stabilite du `.typ`
  - [x] 4.3 `test_generate_typst_escapes_special_characters()` — caracteres Typst echappes
  - [x] 4.4 `test_compile_typst_missing_binary_raises_render_error()` — RenderError si typst absent
  - [x] 4.5 `test_render_pdf_produces_valid_pdf()` — integration si Typst installe (marque `@pytest.mark.skipif` si Typst absent)
  - [x] 4.6 `test_generate_typst_deterministic_output()` — memes entrees = meme `.typ`
  - [x] 4.7 `test_generate_typst_preserves_intermediate_file()` — `.typ` conserve apres compilation
  - [x] 4.8 `test_generate_typst_all_node_types_rendered()` — HeadingNode, ParagraphNode, ImageNode, TableNode presents dans le `.typ`

- [x] Task 5 : Creer les fixtures et golden files (AC: #5)
  - [x] 5.1 Creer golden file `tests/fixtures/golden/minimal.typ` — reference du `.typ` genere a partir de la fixture minimal
  - [x] 5.2 Reutiliser la fixture `tests/fixtures/books/minimal/` existante (book.yaml + chapitres + images)

## Dev Notes

### Contexte technique

- **Typst** : binaire standalone, appele via subprocess. Commande : `typst compile input.typ output.pdf`
- **run_external()** : defini dans `src/bookforge/external.py` — wrapper subprocess avec gestion d'erreurs uniforme. Retourne `subprocess.CompletedProcess[str]`. Leve `RenderError` si commande introuvable ou echec
- **Erreurs** : `RenderError` dans `bookforge/errors.py` (exit_code=2)
- **Module cible** : `src/bookforge/renderers/pdf.py` (existe avec docstring placeholder)
- **Template cible** : `templates/typst/base.typ` (existe avec commentaire placeholder)
- **Prerequis** : Story 2.2 (BookNode, ChapterNode, HeadingNode, ParagraphNode, ImageNode, TableNode) — DONE

### Decision architecturale 2 : Interface Python -> Typst

**Choix :** Generation de fichiers `.typ` + appel `typst compile` en subprocess
**Rationale :** Controle total du template, fichier `.typ` intermediaire debuggable, subprocess fiable cross-platform, zero dependance supplementaire

**Pattern :**
```python
from bookforge.external import run_external

def compile_typst(typ_path: Path, pdf_path: Path) -> Path:
    run_external(
        ["typst", "compile", str(typ_path), str(pdf_path)],
        description="Compilation Typst vers PDF",
    )
    return pdf_path
```

### Dependances de module (architecture.md)

`renderers/` depend de : `ast_nodes`, `tokens` (futur), `external`, `errors`
`renderers/` NE DOIT PAS dependre de : `parser`, `quality`, `judge`

### Strategie de generation du `.typ`

La generation est un **parcours sequentiel de l'AST** :

1. **Preambule** : inclure le template `base.typ` ou inliner la configuration page/text/par
2. **BookNode** : titre du livre (metadata)
3. **ChapterNode** : saut de page + titre chapitre (heading level 1)
4. **HeadingNode** : heading Typst (`= `, `== `, `=== `, etc.) selon le level
5. **ParagraphNode** : texte brut (echappe)
6. **ImageNode** : `#image("chemin/absolu.png")` — utiliser `src` (deja absolu depuis le parser)
7. **TableNode** : `#table(columns: N, ..cells)` — headers + rows

### Syntaxe Typst cle (recherche Context7)

```typst
// Configuration page format livre 6x9 pouces KDP
#set page(
  width: 6in,
  height: 9in,
  margin: (inside: 2cm, outside: 1.5cm, top: 2.5cm, bottom: 2cm),
)

// Typographie professionnelle (Bringhurst)
#set text(
  font: "New Computer Modern",
  size: 11pt,
  lang: "fr",
  region: "FR",
)
#set par(
  justify: true,
  leading: 1.3em,         // interligne ~130% du corps (AC #1)
  first-line-indent: 1em, // alinea standard
)

// Cesure automatique francaise
#set text(hyphenate: true)

// Headings
#show heading: set block(above: 1.4em, below: 1em)

// Table des matieres (sera Story 2.4)
// #outline()

// Saut de page chapitre
#pagebreak()
= Titre du chapitre

// Image centree
#align(center)[#image("chemin.png", width: 80%)]

// Table
#table(
  columns: 3,
  [Header 1], [Header 2], [Header 3],
  [Cell 1],   [Cell 2],   [Cell 3],
)
```

**Commande CLI Typst :**
```bash
typst compile input.typ output.pdf
typst c input.typ output.pdf          # alias court
```

**Options utiles :**
- `--font-path <dir>` : dossier de polices supplementaires
- `--root <dir>` : racine pour la resolution des chemins relatifs dans le `.typ`

### Echappement des caracteres speciaux Typst

Le contenu texte injecte dans le `.typ` doit echapper les caracteres speciaux de Typst :

| Caractere | Signification Typst | Echappement |
|---|---|---|
| `#` | Code/fonction | `\#` |
| `$` | Math mode | `\$` |
| `@` | Reference | `\@` |
| `<` `>` | Label | `\<` `\>` |
| `` ` `` | Code inline | `` \` `` |
| `_` | Emphasis | `\_` |
| `*` | Strong | `\*` |
| `~` | Non-breaking space | `\~` |
| `\` | Escape | `\\` |

**Fonction d'echappement :**
```python
_TYPST_ESCAPE_MAP = str.maketrans({
    "\\": "\\\\",
    "#": "\\#",
    "$": "\\$",
    "@": "\\@",
    "<": "\\<",
    ">": "\\>",
    "`": "\\`",
    "_": "\\_",
    "*": "\\*",
    "~": "\\~",
})

def escape_typst(text: str) -> str:
    return text.translate(_TYPST_ESCAPE_MAP)
```

### Implementation `renderers/pdf.py` — Structure

```python
"""Renderer PDF via typst compile (Story 2.3)."""

import logging
from pathlib import Path

from bookforge.ast_nodes import (
    ASTNode, BookNode, ChapterNode, HeadingNode,
    ImageNode, ParagraphNode, TableNode,
)
from bookforge.errors import RenderError
from bookforge.external import run_external

logger = logging.getLogger("bookforge.renderers.pdf")

TYPST_TEMPLATE = '''... preambule Typst ...'''

def escape_typst(text: str) -> str:
    """Echappe les caracteres speciaux Typst."""
    ...

def _render_node(node: ASTNode) -> str:
    """Convertit un noeud AST en code Typst."""
    if isinstance(node, HeadingNode):
        prefix = "=" * node.level + " "
        return f"{prefix}{escape_typst(node.text)}\n"
    elif isinstance(node, ParagraphNode):
        return f"{escape_typst(node.text)}\n\n"
    elif isinstance(node, ImageNode):
        return f'#align(center)[#image("{node.src}", width: 80%)]\n\n'
    elif isinstance(node, TableNode):
        ...  # table Typst
    else:
        logger.warning("Unknown node type: %s", type(node).__name__)
        return ""

def _render_chapter(chapter: ChapterNode) -> str:
    """Genere le Typst pour un chapitre."""
    lines = [f"#pagebreak()\n= {escape_typst(chapter.title)}\n\n"]
    for child in chapter.children:
        lines.append(_render_node(child))
    return "".join(lines)

def generate_typst(book: BookNode, output_path: Path) -> Path:
    """Genere un fichier .typ depuis l'AST."""
    typ_path = output_path.with_suffix(".typ")
    content_parts = [TYPST_TEMPLATE]
    for chapter in book.chapters:
        content_parts.append(_render_chapter(chapter))
    typ_path.write_text("".join(content_parts), encoding="utf-8")
    logger.debug("Generated .typ file: %s", typ_path)
    return typ_path

def compile_typst(typ_path: Path, pdf_path: Path) -> Path:
    """Compile un fichier .typ en PDF via Typst."""
    run_external(
        ["typst", "compile", str(typ_path), str(pdf_path)],
        description="Compilation Typst vers PDF",
    )
    if not pdf_path.exists():
        raise RenderError(f"PDF non genere : {pdf_path}")
    return pdf_path

def render_pdf(book: BookNode, output_dir: Path) -> Path:
    """Point d'entree : AST -> .typ -> PDF."""
    output_dir.mkdir(parents=True, exist_ok=True)
    typ_path = output_dir / "livre-interieur.typ"
    pdf_path = output_dir / "livre-interieur.pdf"
    generate_typst(book, typ_path)
    compile_typst(typ_path, pdf_path)
    logger.debug("PDF generated: %s", pdf_path)
    return pdf_path
```

### Scope precis de cette story

**DANS le scope :**
- Rendu de base : chapitres, headings, paragraphes, images, tables
- Configuration page/typographie professionnelle
- Compilation via subprocess Typst
- Fichier `.typ` intermediaire conserve
- Tests unitaires + golden file `.typ`

**HORS scope (stories suivantes) :**
- Table des matieres (Story 2.4)
- Pages liminaires : titre, copyright, dedicace (Story 2.4)
- Pages de garde de chapitre stylisees (Story 2.5)
- En-tetes/pieds de page (Story 2.5)
- Protection anti-coupure images (Story 2.6)
- Couverture (Story 2.7)
- Export metadonnees KDP (Story 2.8)
- CLI / logging / progression (Story 2.9)
- Balises semantiques `:::framework` etc. (Epic 4)
- Design tokens YAML (Epic 4)

### Anti-patterns a eviter

- **NE PAS** utiliser `os.path` — `pathlib.Path` uniquement
- **NE PAS** appeler subprocess directement — utiliser `run_external()` de `external.py`
- **NE PAS** utiliser `shell=True` dans subprocess
- **NE PAS** implementer la TDM, les pages liminaires ou en-tetes/pieds de page — Stories 2.4 et 2.5
- **NE PAS** implementer de systeme de design tokens — c'est Epic 4
- **NE PAS** hardcoder des chemins Windows — `pathlib.Path` gere le cross-platform
- **NE PAS** utiliser `print()` — tout passe par `logging.getLogger("bookforge.renderers.pdf")`
- **NE PAS** ajouter de dependance Python supplementaire — Typst est un binaire externe, aucun package pip n'est necessaire

### Patterns du projet etablis (stories 1.1-2.2)

- **Nommage tests** : `test_<quoi>_<condition>_<attendu>()` (ex: `test_generate_typst_valid_ast_produces_typ_file`)
- **Fixtures** : dans `tests/fixtures/`, jamais inline
- **Imports** : ordre stdlib -> third-party -> bookforge (Ruff enforce)
- **Type hints** : systematiques, mypy strict=true
- **Docstrings** : une ligne en francais en haut du module
- **Logging** : `logging.getLogger("bookforge.<module>")`, jamais `print()`
- **Messages utilisateur** : en francais via exceptions (`RenderError`)
- **Logging interne** : en anglais
- **Noeuds AST** : frozen dataclasses, enfants en `tuple`, `source_file` + `line_number` sur chaque noeud
- **Tests existants** : 48 tests passants — aucun ne doit etre modifie ou casse

### Structure des fichiers a creer/modifier

```
templates/typst/
└── base.typ                 # MODIFIER : implementer le template Typst complet

src/bookforge/renderers/
├── __init__.py              # MODIFIER : exporter render_pdf
├── pdf.py                   # MODIFIER : implementer generate_typst, compile_typst, render_pdf

tests/
├── fixtures/
│   └── golden/
│       └── minimal.typ      # CREER : golden file du .typ genere
└── test_renderer_pdf.py     # CREER
```

### Apprentissages des stories precedentes

- **Story 2.2** : `BookNode`, `ChapterNode`, `HeadingNode`, `ParagraphNode`, `ImageNode`, `TableNode` disponibles via `from bookforge.ast_nodes import ...`
- **Story 2.2** : `parse_book(config, book_dir) -> BookNode` disponible pour les tests d'integration
- **Story 2.2** : Les chemins images dans `ImageNode.src` sont deja resolus en absolu
- **Story 2.2** : `token.attrGet()` retourne `str | int | float | None` — cast explicite necessaire pour mypy
- **Story 2.2** : 48 tests total, ruff clean, mypy 0 erreurs
- **Story 1.2** : `run_external(cmd, description) -> CompletedProcess[str]` — wrapper subprocess fiable
- **Story 1.2** : `RenderError` pour les erreurs subprocess (exit_code=2)

### Git intelligence

- Dernier commit : `94b48aff fix(bookforge): address code review — add source_file/line_number to BookNode`
- 48 tests existants, ruff clean, mypy 0 erreurs
- `src/bookforge/renderers/pdf.py` existe avec docstring placeholder
- `templates/typst/base.typ` existe avec commentaire placeholder
- Typst n'est PAS dans les dependances pip — c'est un binaire externe

### Dependances de cette story

- **Prerequis** : Story 2.2 (BookNode + parser) — DONE
- **Bloque** : Story 2.4 (TDM + pages liminaires), Story 2.5 (pages de garde + en-tetes), Story 2.6 (images), toutes les stories suivantes de l'Epic 2

### Project Structure Notes

- Les fichiers `renderers/pdf.py` et `templates/typst/base.typ` existent deja avec placeholder — les enrichir, ne pas les recreer
- `renderers/__init__.py` existe (vide) — ajouter les exports
- Le dossier `tests/fixtures/golden/` existe deja (cree en Story 2.2) — y ajouter `minimal.typ`
- Le fichier `test_renderer_pdf.py` n'existe pas encore — le creer
- Les fixtures `tests/fixtures/books/minimal/` existent (book.yaml + chapitres + images)

### References

- [Source: _bmad-output/planning-artifacts/architecture.md — Decision 2 : Interface Python -> Typst, lignes 304-308]
- [Source: _bmad-output/planning-artifacts/architecture.md — Structure Pattern Subprocess, lignes 444-461]
- [Source: _bmad-output/planning-artifacts/architecture.md — Project Structure renderers/, lignes 606-610]
- [Source: _bmad-output/planning-artifacts/architecture.md — Data Flow, lignes 703-743]
- [Source: _bmad-output/planning-artifacts/architecture.md — Module Boundaries, lignes 663-683]
- [Source: _bmad-output/planning-artifacts/epics.md — Epic 2, Story 2.3, lignes 287-301]
- [Source: _bmad-output/planning-artifacts/prd.md — FR6, FR15, FR33, FR34, NFR1, NFR5]
- [Source: _bmad-output/implementation-artifacts/2-2-parser-markdown-vers-ast.md — Completion Notes, AST API]
- [Source: Context7/Typst docs — page setup, text config, CLI compile]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

- Typst sandboxe les acces fichier : chemins absolus d'images sur un drive different du .typ echouent avec `--root`. Solution : chemins relatifs au .typ + pas de `--root` (Typst utilise le repertoire du .typ par defaut)
- `str.maketrans` avec dict accepte des strings multicaracteres pour les valeurs de remplacement — fonctionne pour l'echappement `\\` -> `\\\\`
- Premier chapitre sans `#pagebreak()`, chapitres suivants avec — evite une page blanche initiale
- [C1] `_render_chapter` emettait `= {title}` en doublon avec le HeadingNode level 1 dans children — supprime
- [C2] Fallback chemin absolu pour images hors repertoire causait des erreurs Typst silencieuses — remplace par RenderError explicite
- [M2] `_load_template()` via `Path(__file__)` fragile si installe via pip — remplace par template inline `_BASE_TEMPLATE`

### Completion Notes List

- Template Typst inline `_BASE_TEMPLATE` : page 6x9in KDP, marges asymetriques reliure, New Computer Modern 11pt, interligne 1.3em, justify, headings h1-h4 styles, marqueur `// --- BEGIN CONTENT ---`
- `escape_typst()` : echappement de 10 caracteres speciaux Typst via `str.maketrans`
- `_render_node()` : dispatch par type AST (HeadingNode, ParagraphNode, ImageNode, TableNode) avec logging enrichi (source_file + line_number)
- `_render_image()` : chemins relatifs au .typ, RenderError si image hors repertoire
- `_render_table()` : generation `#table(columns: N, ...)` avec guard empty table/rows
- `_render_chapter()` : pagebreak entre chapitres (sauf premier), titre rendu uniquement par HeadingNode (pas de doublon)
- `generate_typst()` : template inline + genere contenu pour tous les chapitres
- `compile_typst()` : appel `typst compile` via `run_external()`
- `render_pdf()` : orchestrateur AST -> .typ -> PDF, cree output_dir, conserve .typ
- 24 tests (10 escape, 10 generate, 2 compile, 2 render) — tous passent
- Golden file `minimal.typ` pour stabilite du .typ genere
- Ruff clean, mypy 0 erreurs, 72 tests total (48 existants + 24 nouveaux)
- Code review Gemini : 6 findings corriges (2 critical, 2 medium, 2 low)

### File List

- `templates/typst/base.typ` (modified — reference, template inline dans pdf.py)
- `src/bookforge/renderers/pdf.py` (modified)
- `src/bookforge/renderers/__init__.py` (modified)
- `tests/test_renderer_pdf.py` (new)
- `tests/fixtures/golden/minimal.typ` (new)

### Change Log

- 2026-04-06 : Implementation complete Story 2.3 — Renderer PDF via Typst (template + generateur + compilation + 22 tests)
- 2026-04-06 : Code review Gemini — 6 findings corriges : [C1] doublon titre chapitre, [C2] RenderError image hors repertoire, [M1] guard empty table, [M2] template inline, [L1] marqueur BEGIN CONTENT, [L2] logging enrichi. +2 tests (24 total)
