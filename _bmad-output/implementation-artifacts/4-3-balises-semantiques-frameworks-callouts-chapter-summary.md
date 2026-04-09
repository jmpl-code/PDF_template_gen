# Story 4.3: Balises semantiques (frameworks, callouts, chapter-summary)

Status: review

## Story

As a auteur,
I want utiliser des balises `:::framework`, `:::callout`, `:::chapter-summary` dans mon Markdown,
So that les encadres et frameworks sont visuellement distincts du texte.

## Acceptance Criteria (BDD)

1. **Given** du Markdown contenant `:::framework`, `:::callout`, `:::chapter-summary`
   **When** le parser traite le contenu via le plugin semantique markdown-it-py
   **Then** des noeuds `FrameworkNode`, `CalloutNode`, `ChapterSummaryNode` sont crees dans l'AST
   **And** chaque noeud porte `source_file` et `line_number` conformement au pattern existant

2. **Given** un AST contenant des noeuds semantiques
   **When** le renderer PDF genere le fichier `.typ`
   **Then** chaque type produit un encadre Typst visuellement distinct (bordure, fond, espacement)
   **And** le contenu interne est correctement echappe via `escape_typst()`

3. **Given** un AST contenant des noeuds semantiques
   **When** le renderer EPUB genere le HTML/CSS
   **Then** chaque type produit un `<div class="...">` avec un style CSS distinct
   **And** le CSS est inclus dans le fichier `epub.css` genere

4. **Given** du Markdown contenant une balise non reconnue (ex: `:::unknown`)
   **When** le parser traite le contenu
   **Then** un warning est emis via `logger.warning()` (pas une erreur)
   **And** le contenu est ignore sans bloquer le pipeline

## Tasks / Subtasks

- [x] Task 1 — Definir les noeuds AST semantiques (AC: #1)
  - [x] 1.1 Implementer `FrameworkNode`, `CalloutNode`, `ChapterSummaryNode` dans `src/bookforge/ast_nodes/semantic.py` — frozen dataclasses avec `content: str`, `source_file: Path`, `line_number: int`
  - [x] 1.2 Ajouter les 3 types au type union `ASTNode` dans `src/bookforge/ast_nodes/base.py`
  - [x] 1.3 Exporter les 3 types dans `src/bookforge/ast_nodes/__init__.py` (imports + `__all__`)

- [x] Task 2 — Implementer le plugin markdown-it-py pour conteneurs semantiques (AC: #1, #4)
  - [x] 2.1 Implementer le plugin dans `src/bookforge/parser/semantic.py` utilisant le pattern `container` de markdown-it-py pour reconnaitre `:::framework`, `:::callout`, `:::chapter-summary`
  - [x] 2.2 Le plugin doit generer des tokens avec un type identifiable (ex: `semantic_framework_open`, `semantic_framework_close`)
  - [x] 2.3 Les balises non reconnues (ex: `:::unknown`) doivent emettre `logger.warning("Unknown semantic tag '%s' at line %d", tag, line)` et etre ignorees

- [x] Task 3 — Integrer le plugin dans le parser (AC: #1)
  - [x] 3.1 Dans `src/bookforge/parser/markdown.py`, enregistrer le plugin semantique sur l'instance `MarkdownIt` avant `md.parse(text)`
  - [x] 3.2 Dans `src/bookforge/parser/transform.py`, ajouter le traitement des tokens conteneur dans `tokens_to_ast()` pour creer les noeuds semantiques correspondants

- [x] Task 4 — Renderer PDF : encadres Typst (AC: #2)
  - [x] 4.1 Dans `src/bookforge/renderers/pdf.py`, ajouter des cas dans `_render_node()` pour `FrameworkNode`, `CalloutNode`, `ChapterSummaryNode`
  - [x] 4.2 Produire du Typst utilisant `#block()` avec bordure, fond colore et espacement distincts par type
  - [x] 4.3 Le contenu interne est echappe via `escape_typst()`

- [x] Task 5 — Renderer EPUB : divs + CSS (AC: #3)
  - [x] 5.1 Dans `src/bookforge/renderers/epub.py`, ajouter des cas dans `_render_node_to_markdown()` pour les noeuds semantiques
  - [x] 5.2 Produire des `<div class="framework">`, `<div class="callout">`, `<div class="chapter-summary">` avec le contenu a l'interieur
  - [x] 5.3 Ajouter les styles CSS distincts dans la generation du fichier `epub.css` (bordure, fond, padding, marge par type)

- [x] Task 6 — Tests unitaires et integration (AC: #1, #2, #3, #4)
  - [x] 6.1 Tests AST : verifier que les 3 noeuds sont frozen, portent source_file/line_number, et sont dans le type union ASTNode
  - [x] 6.2 Tests parser : Markdown avec `:::framework ... :::` produit un `FrameworkNode` dans l'AST (idem callout, chapter-summary)
  - [x] 6.3 Tests parser : balise `:::unknown` produit un warning et est ignoree
  - [x] 6.4 Tests renderer PDF : les noeuds semantiques produisent du Typst valide avec `#block`
  - [x] 6.5 Tests renderer EPUB : les noeuds semantiques produisent des `<div class="...">` avec contenu
  - [x] 6.6 Tests integration pipeline : un livre contenant des balises semantiques se compile sans erreur
  - [x] 6.7 Creer fixture `tests/fixtures/books/with_semantic/` avec un chapitre contenant les 3 types de balises

## Dev Notes

### Fichiers stubs DEJA en place (NE PAS recrer)

Deux fichiers stubs existent deja et contiennent uniquement un docstring :
- `src/bookforge/parser/semantic.py` — docstring : `"""Plugin markdown-it-py pour balises semantiques :::framework, :::callout (Story 4.3)."""`
- `src/bookforge/ast_nodes/semantic.py` — docstring : `"""Noeuds semantiques : FrameworkNode, CalloutNode, ChapterSummaryNode (Story 4.3)."""`

**Implementer dans ces fichiers existants, ne pas creer de nouveaux fichiers.**

### Pattern AST node a suivre (copier exactement)

```python
# Voir src/bookforge/ast_nodes/content.py pour le pattern
@dataclass(frozen=True)
class FrameworkNode:
    content: str          # Texte interne du bloc :::framework ... :::
    source_file: Path
    line_number: int
```

Regles :
- `frozen=True` obligatoire (triplet immuable)
- Champs `source_file: Path` et `line_number: int` obligatoires
- `content` est une string (le texte brut a l'interieur du conteneur)
- Pas de champ `children` — le contenu interne est du texte brut, pas un sous-AST

### Type union ASTNode — Modification requise

Fichier `src/bookforge/ast_nodes/base.py` actuel :
```python
ASTNode = Union[
    "HeadingNode",
    "ParagraphNode",
    "ImageNode",
    "TableNode",
]
```

Ajouter les 3 types semantiques a la fin du Union.

### Plugin markdown-it-py — Approche recommandee

markdown-it-py supporte les plugins de type `container` via le package `mdit-py-plugins`. Verifier si `mdit-py-plugins` est deja installe ou utiliser le pattern plugin natif.

**Option A (preferee) — Plugin natif markdown-it-py :**
Ecrire un plugin custom qui intercepte les blocs `:::tag ... :::` en utilisant une regle de block parse. Le format attendu :

```markdown
:::framework
Contenu du framework ici.
Plusieurs lignes possibles.
:::
```

**Option B — mdit-py-plugins container :**
Si `mdit-py-plugins` est disponible, utiliser `container_plugin` qui gere deja la syntaxe `:::`.

**Decision :** Verifier d'abord si `mdit-py-plugins` est dans `pyproject.toml`. Si non, implementer un plugin natif pour respecter la contrainte NFR13 (< 5 deps runtime). L'ajout de `mdit-py-plugins` est acceptable car c'est une extension directe de `markdown-it-py` (meme ecosysteme).

### Integration dans le parser — Points d'insertion

**`src/bookforge/parser/markdown.py` :**
```python
# AVANT:
md = MarkdownIt("commonmark").enable("table")

# APRES:
from bookforge.parser.semantic import semantic_plugin
md = MarkdownIt("commonmark").enable("table")
semantic_plugin(md)  # Enregistre le plugin conteneur
```

**`src/bookforge/parser/transform.py` :**
Dans `tokens_to_ast()`, ajouter des cas pour les tokens generes par le plugin (ex: `container_framework_open` / `container_framework_close`). Extraire le contenu entre open/close et creer le noeud correspondant.

### Rendu PDF Typst — Specifications visuelles

Chaque type doit etre visuellement distinct. Utiliser le pattern Typst `#block()` :

```typst
// :::framework
#block(
  width: 100%,
  inset: 12pt,
  radius: 4pt,
  stroke: rgb("#2563eb") + 1.5pt,
  fill: rgb("#eff6ff"),
)[
  #text(weight: "bold", size: 10pt)[Framework]
  #v(4pt)
  Contenu du framework...
]

// :::callout
#block(
  width: 100%,
  inset: 12pt,
  radius: 4pt,
  stroke: (left: rgb("#f59e0b") + 3pt),
  fill: rgb("#fffbeb"),
)[
  Contenu du callout...
]

// :::chapter-summary
#block(
  width: 100%,
  inset: 12pt,
  radius: 0pt,
  stroke: (top: rgb("#6b7280") + 1pt, bottom: rgb("#6b7280") + 1pt),
  fill: rgb("#f9fafb"),
)[
  #text(weight: "bold", size: 10pt, style: "italic")[Resume du chapitre]
  #v(4pt)
  Contenu du resume...
]
```

**Important :** Le contenu interne doit etre echappe via `escape_typst()` (deja dans `pdf.py` ligne 165).

### Rendu EPUB — CSS specifications

```css
/* Framework box */
.framework {
  border: 2px solid #2563eb;
  background-color: #eff6ff;
  padding: 1em;
  margin: 1.5em 0;
  border-radius: 4px;
}
.framework::before {
  content: "Framework";
  display: block;
  font-weight: bold;
  margin-bottom: 0.5em;
  font-size: 0.9em;
}

/* Callout box */
.callout {
  border-left: 4px solid #f59e0b;
  background-color: #fffbeb;
  padding: 1em;
  margin: 1.5em 0;
}

/* Chapter summary */
.chapter-summary {
  border-top: 1px solid #6b7280;
  border-bottom: 1px solid #6b7280;
  background-color: #f9fafb;
  padding: 1em;
  margin: 1.5em 0;
  font-style: italic;
}
.chapter-summary::before {
  content: "Resume du chapitre";
  display: block;
  font-weight: bold;
  font-style: normal;
  margin-bottom: 0.5em;
  font-size: 0.9em;
}
```

**Integration :** Ajouter ces styles dans la fonction qui genere le CSS EPUB (`_build_css_from_tokens()` dans `epub.py`).

### Rendu EPUB — Format HTML dans le Markdown Pandoc

Le renderer EPUB produit du Markdown pour Pandoc. Les divs doivent utiliser la syntaxe HTML brute :
```html
<div class="framework">

Contenu du framework...

</div>
```

Les lignes vides avant/apres le contenu sont necessaires pour que Pandoc interprete le contenu comme du Markdown a l'interieur du div.

### Balises non reconnues — Comportement

```python
KNOWN_SEMANTIC_TAGS = {"framework", "callout", "chapter-summary"}

if tag not in KNOWN_SEMANTIC_TAGS:
    logger.warning("Unknown semantic tag '%s' at line %d in %s", tag, line, source_file)
    # Ne pas creer de noeud, ignorer le bloc
```

### Ce que Story 4.2 a implemente (contexte)

- `document_class` + `tokens` dans `BookConfig` avec alias YAML `class`
- `resolve_tokens()` integre dans `run_pipeline()`, tokens passes aux renderers
- 184 tests passent, ruff clean, mypy clean
- Pattern de commit : `feat(bookforge): implement Story X.Y — <description>`

### Anti-patterns a eviter

- **NE PAS** creer de sous-AST pour le contenu interne des blocs — le contenu est du texte brut (`str`), pas un arbre de noeuds. Les balises semantiques sont des conteneurs de texte, pas des conteneurs de structure.
- **NE PAS** ajouter de tokens au `TOKEN_REGISTRY` pour les couleurs des encadres — les couleurs sont hardcodees dans les renderers pour MVP1. La customisation via tokens viendra en Epic 8 (Polish).
- **NE PAS** modifier `tokens/registry.py`, `tokens/resolver.py`, ou `tokens/defaults/` — aucun changement requis.
- **NE PAS** modifier `pipeline.py` — les renderers gerent deja les noeuds polymorphiquement.
- **NE PAS** ajouter de nouvelles dependances sans verifier le budget (5/5 slots utilises). Si `mdit-py-plugins` est necessaire, c'est acceptable car c'est une extension de `markdown-it-py`.
- **NE PAS** casser les 184 tests existants.
- **NE PAS** utiliser `print()` — tout passe par `logging.getLogger("bookforge.<module>")`.
- **NE PAS** utiliser `os.path` — `pathlib.Path` partout.

### Conventions de nommage

| Element | Convention | Exemple |
|---|---|---|
| Noeud AST | `PascalCase` + suffixe `Node` | `FrameworkNode` |
| Fichier Python | `snake_case.py` | `semantic.py` |
| Fonction plugin | `snake_case` | `semantic_plugin(md)` |
| Classe CSS EPUB | `kebab-case` | `chapter-summary` |
| Logger | `bookforge.<module>` | `bookforge.parser.semantic` |
| Test | `test_<what>_<condition>_<expected>()` | `test_parser_framework_block_creates_node()` |

### Fixtures de test a creer

```
tests/fixtures/books/with_semantic/
  book.yaml           # Minimal : title, author, chapters_dir
  chapitres/
    01-introduction.md  # Contient :::framework, :::callout, :::chapter-summary
```

Contenu du chapitre de test :
```markdown
# Introduction

Paragraphe normal.

:::framework
Les 5 forces de Porter permettent d'analyser la structure concurrentielle d'un secteur.
:::

Texte entre les blocs.

:::callout
Attention : cette methode ne s'applique qu'aux marches matures.
:::

:::chapter-summary
Ce chapitre a presente les bases de l'analyse concurrentielle et le framework de Porter.
:::
```

### Backward compatibility — Critique

Les fichiers Markdown existants ne contiennent pas de balises `:::`. Le parser doit continuer a fonctionner exactement comme avant pour tout Markdown sans balises semantiques. Les fixtures existantes (`minimal/`, `full/`, `broken/`, `with_class/`) ne doivent pas etre modifiees.

### Git Intelligence

- Pattern de commit : `feat(bookforge): implement Story X.Y — <description>`
- Dernier commit : `44e8b5c4` — Story 4.2
- 184 tests passent, ruff clean, mypy clean
- Les 2 stories precedentes de l'Epic 4 ont chacune fait 1-2 commits

### Project Structure Notes

- Fichiers stubs deja en place : `parser/semantic.py`, `ast_nodes/semantic.py`
- Tous les changements dans `src/bookforge/` et `tests/`
- Pas de modification aux templates Typst (`templates/typst/`) — les encadres sont generes dynamiquement par le renderer
- Pas de modification a `pyproject.toml` sauf si ajout de `mdit-py-plugins`

### References

- [Source: _bmad-output/planning-artifacts/epics.md — Epic 4, Story 4.3]
- [Source: _bmad-output/planning-artifacts/architecture.md — Decision 1 "AST Representation: markdown-it-py + custom dataclasses"]
- [Source: _bmad-output/planning-artifacts/architecture.md — "Token Model 8 Categories: Special Elements"]
- [Source: _bmad-output/planning-artifacts/architecture.md — Project Structure "parser/semantic.py"]
- [Source: _bmad-output/planning-artifacts/architecture.md — "Implementation Patterns: AST Nodes frozen immutable"]
- [Source: _bmad-output/planning-artifacts/prd.md — FR3 "Balises semantiques"]
- [Source: _bmad-output/implementation-artifacts/4-2-classe-de-document-et-jeu-de-tokens-predefini.md — Dev Notes, Completion Notes]
- [Source: src/bookforge/ast_nodes/content.py — Pattern dataclass frozen]
- [Source: src/bookforge/renderers/pdf.py — _render_node(), escape_typst()]
- [Source: src/bookforge/renderers/epub.py — _render_node_to_markdown(), _build_css_from_tokens()]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

### Completion Notes List

- 3 noeuds AST semantiques implementes (`FrameworkNode`, `CalloutNode`, `ChapterSummaryNode`) — frozen dataclasses avec source_file/line_number
- Plugin markdown-it-py natif ecrit (pas de dependance `mdit-py-plugins`) — regle de block `semantic_container` enregistree avant `fence`
- Tokens generes : `semantic_<tag>_open` / `semantic_<tag>_close` avec contenu dans `token.content`
- Balises inconnues (`:::unknown`) emettent un warning et sont ignorees (le bloc est skippe)
- Renderer PDF : 3 fonctions `_render_framework()`, `_render_callout()`, `_render_chapter_summary()` avec `#block()` Typst, styles visuels distincts (couleurs, bordures, fond)
- Renderer EPUB : `<div class="...">` avec CSS semantique (`_SEMANTIC_CSS`) ajoute aux deux modes (statique `_KINDLE_CSS` et dynamique `_build_css_from_tokens()`)
- 26 tests couvrant AST, parser, renderers PDF/EPUB, et integration pipeline
- Fixture `with_semantic/` creee avec les 3 types de balises
- 210/210 tests passent (184 existants + 26 nouveaux), zero regression, ruff clean

### Change Log

- 2026-04-07: Implementation Story 4.3 — balises semantiques (frameworks, callouts, chapter-summary)

### File List

- src/bookforge/ast_nodes/semantic.py (modified — implementation FrameworkNode, CalloutNode, ChapterSummaryNode)
- src/bookforge/ast_nodes/base.py (modified — ajout 3 types au union ASTNode)
- src/bookforge/ast_nodes/__init__.py (modified — export 3 types semantiques)
- src/bookforge/parser/semantic.py (modified — plugin markdown-it-py natif pour :::tag)
- src/bookforge/parser/markdown.py (modified — enregistrement du plugin semantique)
- src/bookforge/parser/transform.py (modified — traitement tokens semantiques dans tokens_to_ast)
- src/bookforge/renderers/pdf.py (modified — rendu Typst #block pour 3 types semantiques)
- src/bookforge/renderers/epub.py (modified — rendu div + CSS semantique pour 3 types)
- tests/test_semantic.py (new — 26 tests AST, parser, renderers, integration)
- tests/fixtures/books/with_semantic/book.yaml (new — fixture livre avec balises semantiques)
- tests/fixtures/books/with_semantic/chapitres/01-introduction.md (new — chapitre avec :::framework, :::callout, :::chapter-summary)
