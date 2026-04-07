# Story 2.7 : Couverture template statique

Status: done

## Story

As a auteur,
I want qu'une couverture de base soit generee depuis le titre, sous-titre et auteur,
So that j'ai une couverture utilisable des MVP0.

## Acceptance Criteria

1. **Given** les informations dans `book.yaml` (titre, sous_titre, auteur) **When** le pipeline genere la couverture **Then** un PDF de couverture est produit via un template Typst statique
2. **Given** un `BookConfig` valide avec titre et auteur **When** `render_cover()` est appele **Then** le fichier `couverture.pdf` est place dans le dossier de sortie
3. **Given** un `BookConfig` avec sous_titre **When** la couverture est generee **Then** le sous-titre est affiche lisiblement entre le titre et l'auteur
4. **Given** un `BookConfig` sans sous_titre (None) **When** la couverture est generee **Then** la couverture est produite avec seulement titre et auteur (pas de blanc excessif)
5. **Given** un titre contenant des caracteres speciaux Typst (#, $, @, etc.) **When** la couverture est generee **Then** les caracteres sont echappes correctement via `escape_typst()`
6. **Given** Typst non installe sur le systeme **When** `render_cover()` est appele **Then** une `RenderError` claire est levee (pattern identique a `compile_typst()`)
7. **Given** les memes entrees (book.yaml identique) **When** la couverture est generee deux fois **Then** les fichiers `.typ` produits sont identiques (determinisme)

## Tasks / Subtasks

- [x] Task 1 : Implementer `render_cover()` dans `src/bookforge/renderers/cover.py` (AC: #1, #2, #6)
  - [x] 1.1 Creer `generate_cover_typst(config: BookConfig, output_path: Path) -> Path` — genere le fichier `.typ` de couverture
  - [x] 1.2 Creer `compile_cover(typ_path: Path, pdf_path: Path) -> Path` — compile via `run_external()`
  - [x] 1.3 Creer `render_cover(config: BookConfig, output_dir: Path) -> Path` — point d'entree : .typ -> PDF
- [x] Task 2 : Creer le template Typst inline pour la couverture (AC: #1, #3, #4, #5)
  - [x] 2.1 Definir `_COVER_TEMPLATE` comme constante string inline (pattern identique a `_BASE_TEMPLATE` dans pdf.py)
  - [x] 2.2 Page setup : 6x9 pouces (format KDP identique au livre interieur)
  - [x] 2.3 Layout : titre en haut (36pt bold), sous-titre conditionnel (20pt), auteur en bas (18pt)
  - [x] 2.4 Fond : couleur sobre (blanc ou ivoire) — valeur hardcodee pour MVP0
- [x] Task 3 : Exporter `render_cover` dans `renderers/__init__.py` (AC: #1)
  - [x] 3.1 Ajouter `from bookforge.renderers.cover import render_cover` et mettre a jour `__all__`
- [x] Task 4 : Ajouter des tests dans `tests/test_cover.py` (AC: #1-#7)
  - [x] 4.1 `test_cover_generates_typ_file` — verifie que le .typ est cree
  - [x] 4.2 `test_cover_title_in_typ` — verifie que le titre est present dans le Typst genere
  - [x] 4.3 `test_cover_subtitle_present_when_defined` — verifie sous-titre inclus si non None
  - [x] 4.4 `test_cover_subtitle_absent_when_none` — verifie pas de sous-titre si None
  - [x] 4.5 `test_cover_author_in_typ` — verifie que l'auteur est present
  - [x] 4.6 `test_cover_special_chars_escaped` — verifie echappement des caracteres speciaux
  - [x] 4.7 `test_cover_deterministic_output` — meme config = meme .typ
  - [x] 4.8 `test_cover_typst_not_found_raises_render_error` — mock subprocess pour simuler Typst manquant
  - [x] 4.9 `test_cover_output_path_correct` — verifie que le fichier est nomme `couverture.pdf`
- [x] Task 5 : Passer linting et type-checking (AC: tous)
  - [x] 5.1 `ruff check src/ tests/` et `ruff format --check src/ tests/`
  - [x] 5.2 `mypy src/`
  - [x] 5.3 `pytest` — tous les tests passent (103 existants + 9 nouveaux = 112)

## Dev Notes

### Etat actuel du code

**Fichiers placeholder existants :**

`src/bookforge/renderers/cover.py` (ligne 1) :
```python
"""Generation de couverture via template Typst (Story 2.7)."""
```

`templates/typst/cover.typ` (ligne 1) :
```typst
// Template couverture — sera implemente en Story 2.7.
```

**IMPORTANT : Le template `cover.typ` dans `templates/` NE doit PAS etre utilise.** Le pattern etabli dans ce projet est le **template inline** : tout le Typst est genere directement dans le code Python comme constante string (voir `_BASE_TEMPLATE` dans `pdf.py`). Le fichier `templates/typst/cover.typ` reste un placeholder de documentation.

### Architecture cible

Le module `cover.py` est **independant** du renderer PDF interieur. Il ne partage aucun etat avec `pdf.py` sauf les utilitaires communs (`escape_typst`, `run_external`).

**Signature des fonctions :**

```python
# cover.py

def generate_cover_typst(config: BookConfig, output_path: Path) -> Path:
    """Genere le fichier .typ de couverture depuis BookConfig."""

def compile_cover(typ_path: Path, pdf_path: Path) -> Path:
    """Compile le .typ couverture en PDF via Typst."""

def render_cover(config: BookConfig, output_dir: Path) -> Path:
    """Point d'entree : BookConfig -> couverture.typ -> couverture.pdf."""
```

**Flux de donnees :**
```
BookConfig (titre, sous_titre, auteur)
    |
    v
generate_cover_typst() -> couverture.typ
    |
    v
compile_cover() via run_external(["typst", "compile", ...]) -> couverture.pdf
```

### Template Typst inline cible

Le template Typst pour la couverture MVP0 :

```typst
// Couverture statique — BookForge (Story 2.7)
// Format 6x9 pouces (KDP standard)

#set page(
  width: 6in,
  height: 9in,
  margin: (x: 1.5cm, y: 2cm),
)

#set text(
  font: "New Computer Modern",
  lang: "fr",
  region: "FR",
)

// Disposition verticale centree
#align(center)[
  #v(1fr)

  #text(size: 36pt, weight: "bold")[{TITRE}]

  {BLOC_SOUS_TITRE}

  #v(1fr)

  #text(size: 18pt)[{AUTEUR}]

  #v(2cm)
]
```

Ou `{BLOC_SOUS_TITRE}` est :
- Si sous_titre non None : `#v(1em)\n  #text(size: 20pt)[{SOUS_TITRE}]`
- Si sous_titre None : chaine vide (pas de v(1em) supplementaire)

### Pattern a suivre — copier de pdf.py

| Aspect | Pattern dans pdf.py | Appliquer dans cover.py |
|--------|---------------------|-------------------------|
| Template | `_BASE_TEMPLATE` constante string | `_COVER_TEMPLATE` constante string |
| Generation | `generate_typst(book, output_path, config)` | `generate_cover_typst(config, output_path)` |
| Compilation | `compile_typst(typ_path, pdf_path)` | `compile_cover(typ_path, pdf_path)` |
| Point d'entree | `render_pdf(book, output_dir, config)` | `render_cover(config, output_dir)` |
| Subprocess | `run_external(["typst", "compile", ...])` | Identique |
| Echappement | `escape_typst(text)` | Importer depuis `bookforge.renderers.pdf` |
| Logging | `logger = logging.getLogger("bookforge.renderers.pdf")` | `logger = logging.getLogger("bookforge.renderers.cover")` |
| Erreurs | `RenderError` pour echecs de compilation | Identique |
| Nommage sortie | `livre-interieur.typ` / `livre-interieur.pdf` | `couverture.typ` / `couverture.pdf` |

### Import de escape_typst

`escape_typst()` est definie dans `pdf.py`. Pour la reutiliser dans `cover.py` :

**Option recommandee :** Importer directement `from bookforge.renderers.pdf import escape_typst`. C'est acceptable car `cover.py` et `pdf.py` sont dans le meme package `renderers/`. Pas de dependance circulaire (pdf.py n'importe pas cover.py).

**Alternative (si le dev prefere) :** Deplacer `escape_typst()` et `_TYPST_ESCAPE_MAP` dans un module utilitaire `renderers/_typst_utils.py`. Ce refactoring est optionnel et hors scope strict — ne le faire que si ca simplifie les choses.

### BookConfig — pas de modification necessaire

`BookConfig` (dans `config/schema.py`) possede deja tous les champs necessaires :
- `titre: str` (obligatoire)
- `sous_titre: str | None` (optionnel)
- `auteur: str` (obligatoire)

**NE PAS ajouter de champs cover-specifiques** pour MVP0. Les champs existants suffisent.

### Fichiers a toucher

| Fichier | Action |
|---------|--------|
| `src/bookforge/renderers/cover.py` | Remplacer le placeholder par l'implementation complete |
| `src/bookforge/renderers/__init__.py` | Ajouter export `render_cover` |
| `tests/test_cover.py` | Creer — tests unitaires de la couverture |

### Fichiers a NE PAS toucher

| Fichier | Raison |
|---------|--------|
| `src/bookforge/config/schema.py` | BookConfig a deja tous les champs necessaires |
| `src/bookforge/renderers/pdf.py` | Module independant — pas de modification |
| `templates/typst/cover.typ` | Placeholder doc seulement — template inline dans cover.py |
| `src/bookforge/ast_nodes/` | Pas de nouveau noeud AST necessaire |
| `src/bookforge/external.py` | `run_external()` est deja complet |
| `tests/test_renderer_pdf.py` | Tests PDF existants — pas de regression a verifier ici |

### Patterns etablis (Stories 2.3-2.6 — a respecter)

- **Template inline** : Tout le Typst est genere inline, pas de fichiers `.typ` externes charges.
- **`escape_typst()`** : Obligatoire pour tout texte utilisateur (titre, sous-titre, auteur).
- **`pathlib.Path`** partout, jamais `os.path` ou concatenation de strings.
- **`run_external()`** : Wrapper uniforme pour subprocess Typst. Toujours l'utiliser.
- **Logging** : `logger.debug()` en anglais pour les developpeurs. Erreurs utilisateur en francais via exceptions `RenderError`.
- **Nommage tests** : `test_<quoi>_<condition>_<attendu>()`.
- **Linting** : `ruff check && ruff format --check && mypy src/` doivent tous passer.
- **103 tests existants** — ne pas les casser. Les nouveaux tests vont dans un fichier dedie `tests/test_cover.py`.

### Anti-patterns a eviter

1. **Ne PAS charger le template depuis un fichier externe** (`templates/typst/cover.typ`). Utiliser le pattern inline.
2. **Ne PAS ajouter de design tokens** — Ca releve de l'Epic 4. Hardcoder les valeurs pour MVP0.
3. **Ne PAS generer de thumbnail/JPEG** — Ca releve de Story 5.2 (Epic 5).
4. **Ne PAS generer de 4e de couverture ni de dos** — Stories 5.1-5.2.
5. **Ne PAS ajouter de dependance Pillow/PIL** — Pas necessaire pour MVP0 (PDF seulement).
6. **Ne PAS modifier BookConfig** — Les champs existants suffisent.
7. **Ne PAS integrer dans le pipeline CLI** — Story 2.9 fera l'integration CLI.
8. **Ne PAS creer de `CoverNode` ou noeud AST** — Pas necessaire, la couverture utilise directement `BookConfig`.
9. **Ne PAS utiliser `os.path`** — `pathlib.Path` partout.
10. **Ne PAS ajouter de numerotation de page** sur la couverture.

### Fixture de test

Reutiliser le fichier `tests/fixtures/books/minimal/book.yaml` qui contient :
```yaml
titre: "Mon Livre Business"
sous_titre: "Un guide pratique"
auteur: "JM"
genre: "business"
```

Pour les tests, creer un `BookConfig` directement en Python (pas besoin de lire le YAML) :
```python
config = BookConfig(
    titre="Mon Livre Business",
    sous_titre="Un guide pratique",
    auteur="JM",
    genre="business",
    chapitres=[ChapterConfig(titre="Ch1", fichier="ch1.md")],
)
```

Pour tester sans sous-titre :
```python
config_no_sub = BookConfig(
    titre="Mon Livre",
    auteur="JM",
    genre="business",
    chapitres=[ChapterConfig(titre="Ch1", fichier="ch1.md")],
)
```

### Scope MVP0 vs MVP1+

| Aspect | MVP0 (cette story) | MVP1+ (hors scope) |
|--------|---------------------|---------------------|
| Contenu | Titre + sous-titre + auteur | + pitch, bio, ISBN barcode |
| Format | PDF seul | + JPEG Kindle, thumbnail 150px |
| Couverture | Face uniquement | + dos + 4e de couverture |
| Tokens | Valeurs hardcodees | Design tokens YAML |
| Dimensions | 6x9 pouces fixe | Parametrique selon format |
| Pipeline | Appel independant | Integre dans CLI (Story 2.9) |

### Project Structure Notes

- Le module `cover.py` est dans `renderers/` a cote de `pdf.py` — alignement parfait avec l'architecture.
- Pas de nouveau module, pas de nouvelle dependance externe.
- Le seul import cross-module est `escape_typst` depuis `pdf.py` — acceptable dans le meme package.

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#renderers-cover] — Module couverture independant
- [Source: _bmad-output/planning-artifacts/architecture.md#Decision-2] — Interface Python -> Typst -> PDF via subprocess
- [Source: _bmad-output/planning-artifacts/prd.md#FR20] — Couverture parametrique depuis template
- [Source: _bmad-output/planning-artifacts/epics.md#Story-2.7] — AC Given/When/Then
- [Source: _bmad-output/planning-artifacts/epics.md#Epic-2] — Epic 2 objectifs et contexte
- [Source: _bmad-output/implementation-artifacts/2-6-integration-des-images-et-diagrammes.md] — Patterns etablis, 103 tests existants
- [Source: src/bookforge/renderers/pdf.py] — Pattern de reference pour template inline, escape_typst, compile_typst
- [Source: src/bookforge/external.py] — run_external() wrapper uniforme

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

- `escape_typst` importe depuis `pdf.py` — pas de duplication de code
- Template Typst inline `_COVER_TEMPLATE` avec placeholders `{titre}`, `{auteur}`, `{bloc_sous_titre}`
- Fond blanc par defaut (pas de couleur speciale pour MVP0 — la page Typst est blanche par defaut)

### Completion Notes List

- `generate_cover_typst()` genere le fichier `.typ` avec template inline 6x9 KDP
- `compile_cover()` compile via `run_external()` (meme pattern que `compile_typst()`)
- `render_cover()` point d'entree : cree le repertoire, genere .typ, compile en PDF
- Sous-titre conditionnel : inclus avec `#v(1em)` + `#text(size: 20pt)` si non None, omis sinon
- Echappement Typst via `escape_typst()` importe de `pdf.py` pour titre, sous-titre, auteur
- Export `render_cover` ajoute dans `renderers/__init__.py`
- 9 nouveaux tests dans `tests/test_cover.py`, 112/112 tests passent
- ruff check clean, ruff format clean, mypy clean (erreurs preexistantes dans `core-skills/` hors scope)

### File List

- `src/bookforge/renderers/cover.py` — Modified (implementation complete)
- `src/bookforge/renderers/__init__.py` — Modified (export render_cover)
- `tests/test_cover.py` — Created (9 tests)
