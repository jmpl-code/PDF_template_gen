# Story 2.6 : Integration des images et diagrammes

Status: review

## Story

As a auteur,
I want que les images et diagrammes soient integres sans coupure de page, redimensionnes et centres,
So that les visuels sont lisibles et bien positionnes dans le PDF final.

## Acceptance Criteria

1. **Given** un AST contenant des `ImageNode` avec chemins resolus **When** le renderer produit le PDF **Then** les images sont centrees horizontalement
2. **Given** une image plus large que la zone de texte **When** le renderer produit le PDF **Then** l'image est redimensionnee pour tenir dans les marges (largeur max = zone de texte)
3. **Given** une image en bas de page **When** le renderer produit le PDF **Then** l'image n'est jamais coupee par un saut de page (protection anti-coupure via `#block(breakable: false)`)
4. **Given** une image avec un ratio d'aspect quelconque **When** le renderer produit le PDF **Then** le ratio d'aspect est conserve (Typst preserve le ratio quand seul `width` est defini)
5. **Given** une image avec un texte alternatif non vide **When** le renderer produit le PDF **Then** le texte alternatif est affiche comme legende sous l'image via `#figure(caption: [...])`
6. **Given** une image sans texte alternatif **When** le renderer produit le PDF **Then** l'image est affichee sans legende

## Tasks / Subtasks

- [x] Task 1 : Modifier `_render_image()` dans `renderers/pdf.py` (AC: #1, #2, #3, #4, #5, #6)
  - [x] 1.1 Remplacer le rendu actuel `#align(center)[#image(...)]` par un bloc `#figure` + `#block(breakable: false)`
  - [x] 1.2 Utiliser `width: 80%` par defaut (images s'adaptent aux marges, ratio preserve par Typst)
  - [x] 1.3 Ajouter `caption: [alt_text]` si `image.alt` est non vide ; omettre caption sinon
  - [x] 1.4 Gerer le `#block(breakable: false)` pour la protection anti-coupure de page
- [x] Task 2 : Mettre a jour le golden file `tests/fixtures/golden/minimal.typ` (AC: #1)
  - [x] 2.1 Regenerer le golden file avec le nouveau format de sortie image
  - [x] 2.2 Verifier que le golden file inclut la structure `#block(breakable: false)[#figure(...)]`
- [x] Task 3 : Mettre a jour le golden file `tests/fixtures/golden/minimal-ast.json` si necessaire
- [x] Task 4 : Ajouter des tests dans `tests/test_renderer_pdf.py` (AC: #1-#6)
  - [x] 4.1 `test_image_centered_in_figure` — verifie que le Typst contient `#figure` avec `#image`
  - [x] 4.2 `test_image_breakable_false` — verifie la presence de `#block(breakable: false)`
  - [x] 4.3 `test_image_with_alt_has_caption` — verifie `caption:` present quand `alt` non vide
  - [x] 4.4 `test_image_without_alt_no_caption` — verifie pas de `caption:` quand `alt` est vide
  - [x] 4.5 `test_image_width_constraint` — verifie `width: 80%` dans le code Typst genere
  - [x] 4.6 `test_image_path_forward_slashes` — verifie que les chemins utilisent `/` (cross-platform, deja teste mais confirmer avec nouveau format)
  - [x] 4.7 `test_image_outside_typ_dir_raises_render_error` — verifie l'erreur quand image hors repertoire (test existant, confirmer non-regression)
- [x] Task 5 : Passer linting et type-checking (AC: tous)
  - [x] 5.1 `ruff check src/ tests/` et `ruff format --check src/ tests/`
  - [x] 5.2 `mypy src/`
  - [x] 5.3 `pytest` — tous les tests passent (96 existants + 7 nouveaux = 103)

## Dev Notes

### Etat actuel du code

**Fichier principal a modifier : `src/bookforge/renderers/pdf.py`**

La fonction `_render_image()` (ligne 110-121) genere actuellement :
```python
def _render_image(image: ImageNode, typ_dir: Path) -> str:
    try:
        rel_path = image.src.resolve().relative_to(typ_dir.resolve())
    except ValueError:
        raise RenderError(...)
    src_str = str(rel_path).replace("\\", "/")
    return f'#align(center)[#image("{src_str}", width: 80%)]\n\n'
```

**Ce qui produit :**
```typst
#align(center)[#image("images/diagram.png", width: 80%)]
```

**Ce qu'il faut produire (avec alt text) :**
```typst
#block(breakable: false)[
  #figure(
    image("images/diagram.png", width: 80%),
    caption: [Diagramme exemple],
  )
]
```

**Ce qu'il faut produire (sans alt text) :**
```typst
#block(breakable: false)[
  #figure(
    image("images/diagram.png", width: 80%),
  )
]
```

### Decisions techniques

1. **`#block(breakable: false)`** : Empeche Typst de couper l'image entre deux pages. Si l'image ne tient pas en bas de page, elle est deplacee en haut de la page suivante.
2. **`#figure()`** : Element semantique Typst qui centre automatiquement son contenu et gere les legendes. Pas besoin de `#align(center)` explicite — `#figure` centre par defaut.
3. **`width: 80%`** : Conserve la largeur actuelle. Typst preserve le ratio d'aspect quand seul `width` est specifie. 80% laisse une marge visuelle agreable autour de l'image.
4. **`caption`** conditionnel : Si `image.alt` est non vide, ajouter `caption: [escaped_alt]`. Sinon, omettre le parametre caption entierement.
5. **Echappement** : Le texte alt doit passer par `escape_typst()` pour eviter les injections de markup Typst.

### Code cible pour `_render_image()`

```python
def _render_image(image: ImageNode, typ_dir: Path) -> str:
    """Genere le code Typst pour une image avec protection anti-coupure."""
    try:
        rel_path = image.src.resolve().relative_to(typ_dir.resolve())
    except ValueError:
        raise RenderError(
            f"L'image '{image.src}' est hors du repertoire de sortie "
            f"'{typ_dir}' — deplacez-la ou utilisez un chemin accessible"
        )
    src_str = str(rel_path).replace("\\", "/")
    caption_line = ""
    if image.alt:
        caption_line = f"\n    caption: [{escape_typst(image.alt)}],"
    return (
        "#block(breakable: false)[\n"
        "  #figure(\n"
        f'    image("{src_str}", width: 80%),{caption_line}\n'
        "  )\n"
        "]\n\n"
    )
```

### Patterns etablis (Story 2.5 — a respecter)

- **Template inline** : Tout le Typst est genere inline dans `pdf.py`, pas de fichiers externes.
- **Fonctions `_render_*()`** : Chaque element retourne un `str` de code Typst.
- **`escape_typst()`** : Obligatoire pour tout texte utilisateur (titres, alt text).
- **`pathlib.Path`** partout, jamais `os.path` ou concatenation de strings.
- **Forward slashes** : `str(path).replace("\\", "/")` pour compatibilite Typst cross-platform.
- **Backward compatibility** : `config` optionnel dans `generate_typst()`. Ne pas casser les 96 tests existants.
- **Logging** : `logger.debug()` en anglais pour les developpeurs. Erreurs utilisateur en francais via exceptions.
- **Nommage tests** : `test_<quoi>_<condition>_<attendu>()`.
- **Linting** : `ruff check && ruff format --check && mypy src/` doivent tous passer.

### Fichiers a toucher

| Fichier | Action |
|---------|--------|
| `src/bookforge/renderers/pdf.py` | Modifier `_render_image()` (lignes 110-121) |
| `tests/test_renderer_pdf.py` | Ajouter classe `TestImageIntegration` avec 5-7 tests |
| `tests/fixtures/golden/minimal.typ` | Regenerer avec le nouveau format image |
| `templates/typst/base.typ` | PAS de modification (reference seulement) |

### Fixture de test existante

- `tests/fixtures/books/minimal/images/diagram.png` — PNG 69 octets, valide
- Le Markdown source contient `![Diagramme exemple](../images/diagram.png)`
- Le `ImageNode` resultant a `alt="Diagramme exemple"` et `src` resolu en absolu
- Le golden file `minimal.typ` devra refleter le nouveau format `#block(breakable: false)[#figure(...)]`

### Anti-patterns a eviter

1. **Ne PAS ajouter de logique de DPI** — Ca releve de Story 7.1 (quality/checks.py), pas du renderer.
2. **Ne PAS creer de fichiers Typst externes** — Maintenir le pattern inline.
3. **Ne PAS utiliser `#image(fit: "contain")`** — `width: 80%` avec ratio preserve par defaut est suffisant.
4. **Ne PAS ajouter de numerotation de figures** — Hors scope (potentiellement Epic 4).
5. **Ne PAS modifier `ImageNode`** — La dataclass est figee et suffisante (`src`, `alt`, `source_file`, `line_number`).
6. **Ne PAS modifier `_extract_image()` dans `parser/transform.py`** — Le parsing d'images est complet (Story 2.2).

### Project Structure Notes

- Alignement avec la structure du projet : modification limitee a `renderers/pdf.py` et aux tests.
- Pas de nouveau module, pas de nouvelle dependance.
- Le changement est retrocompatible : `_render_image()` est une fonction interne appelee par `_render_node()`.

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#Decision-8] — Gestion des assets, chemins relatifs resolus au parsing
- [Source: _bmad-output/planning-artifacts/architecture.md#AST-Nodes] — ImageNode dans ast_nodes/content.py
- [Source: _bmad-output/planning-artifacts/architecture.md#Error-Handling] — RenderError pour erreurs de rendu
- [Source: _bmad-output/planning-artifacts/prd.md#FR9] — Integration images sans coupure, redimensionnees et centrees
- [Source: _bmad-output/planning-artifacts/prd.md#FR4] — Referencier images depuis Markdown
- [Source: _bmad-output/planning-artifacts/epics.md#Story-2.6] — AC Given/When/Then
- [Source: _bmad-output/implementation-artifacts/2-5-pages-de-garde-de-chapitre-et-en-tetes-pieds-de-page.md] — Patterns etablis, anti-patterns, 96 tests existants

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

- 2 tests existants adaptes pour le nouveau format image (filtre `image("` au lieu de `#image("`)
- Le golden AST (`minimal-ast.json`) n'a pas necessite de modification — `ImageNode` inchange

### Completion Notes List

- `_render_image()` remplace `#align(center)[#image(...)]` par `#block(breakable: false)[#figure(image(...))]`
- Protection anti-coupure de page via `#block(breakable: false)`
- Centrage semantique via `#figure()` (remplace `#align(center)`)
- Legende conditionnelle : `caption: [alt_text]` si alt non vide, omis sinon
- Echappement Typst du texte alt via `escape_typst()`
- 7 nouveaux tests dans `TestImageIntegration`, 2 tests existants adaptes
- 103/103 tests passent, ruff clean, mypy clean

### File List

- `src/bookforge/renderers/pdf.py` — Modified (docstring + `_render_image()`)
- `tests/test_renderer_pdf.py` — Modified (2 tests adaptes + 7 nouveaux tests)
- `tests/fixtures/golden/minimal.typ` — Modified (nouveau format image)
