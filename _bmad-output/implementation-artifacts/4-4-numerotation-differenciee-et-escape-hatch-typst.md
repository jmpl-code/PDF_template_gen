# Story 4.4: Numerotation differenciee et escape hatch Typst

Status: review

## Story

As a auteur,
I want une numerotation romaine pour les pages liminaires et arabe pour le corps, et pouvoir injecter du Typst natif si necessaire,
So that j'ai un controle fin sur des cas specifiques sans etre limite par les tokens.

## Acceptance Criteria (BDD)

1. **Given** un livre rendu avec `config` (pages liminaires presentes)
   **When** le renderer PDF genere le fichier `.typ`
   **Then** les pages liminaires utilisent une numerotation en chiffres romains minuscules (`#set page(numbering: "i")`)
   **And** le compteur de page est reinitialise a `1` au debut du corps
   **And** le corps utilise une numerotation arabe (`numbering: "1"`)

2. **Given** un `book.yaml` contenant un champ `typst_raw: "..."`
   **When** le parser de configuration charge `book.yaml`
   **Then** `BookConfig.typst_raw` contient la chaine fournie
   **And** le renderer PDF injecte ce contenu tel quel dans le fichier `.typ` genere (pas d'echappement)
   **And** l'injection se fait apres le template de base et avant les pages liminaires / contenu

3. **Given** un `book.yaml` sans champ `typst_raw` (ou `null`)
   **When** le pipeline s'execute
   **Then** aucun contenu brut n'est injecte et le comportement existant est strictement preserve (retro-compatibilite)

4. **Given** un `typst_raw` syntaxiquement invalide (ex: `#set foo(`)
   **When** `compile_typst()` est invoque
   **Then** une `RenderError` est levee avec un message explicite mentionnant explicitement que l'echec peut provenir du champ `typst_raw`
   **And** le message inclut le stderr de Typst (pas de crash ni d'exception non geree)

## Tasks / Subtasks

- [x] Task 1 — Ajouter `typst_raw` au schema de configuration (AC: #2, #3)
  - [x] 1.1 Ajouter `typst_raw: str | None = None` dans `src/bookforge/config/schema.py` (classe `BookConfig`) — placer apres `tokens: str | None = None`
  - [x] 1.2 Pas d'alias YAML necessaire : le champ s'appelle directement `typst_raw` dans `book.yaml`
  - [x] 1.3 Pas de validation de contenu (c'est un escape hatch — la validation se fait au moment de la compilation Typst)

- [x] Task 2 — Numerotation romaine pour les pages liminaires (AC: #1)
  - [x] 2.1 Dans `src/bookforge/renderers/pdf.py`, modifier `_render_front_matter()` : remplacer `#set page(numbering: none)` par `#set page(numbering: "i")` pour produire i, ii, iii...
  - [x] 2.2 Verifier que `_render_running_headers()` reinitialise bien le compteur via `#counter(page).update(1)` avant le premier chapitre (deja present)
  - [x] 2.3 Verifier que `_render_running_headers()` passe `numbering: "1"` dans le `#set page(...)` (deja present ligne 388)

- [x] Task 3 — Injection du `typst_raw` dans le fichier `.typ` (AC: #2, #3)
  - [x] 3.1 Dans `generate_typst()` (`src/bookforge/renderers/pdf.py`), apres l'ecriture du `template` et avant `_render_front_matter(config)`, injecter `config.typst_raw` s'il est non-None et non-vide
  - [x] 3.2 Encadrer l'injection par des commentaires `// --- BEGIN typst_raw (escape hatch) ---` / `// --- END typst_raw ---` pour le debogage
  - [x] 3.3 Le contenu est injecte TEL QUEL (pas d'echappement via `escape_typst()`) — c'est precisement le but d'un escape hatch
  - [x] 3.4 Si `config is None` (chemin retro-compatible sans BookConfig), ne rien injecter

- [x] Task 4 — Enrichir le message d'erreur de `compile_typst` (AC: #4)
  - [x] 4.1 Dans `compile_typst()` (`src/bookforge/renderers/pdf.py`), wrapper `run_external(...)` dans un `try/except RenderError`
  - [x] 4.2 Si `config.typst_raw` est defini (passer le flag au niveau `compile_typst`) ET qu'une `RenderError` remonte, relever une nouvelle `RenderError` dont le message prefixe l'erreur par : `"Echec de compilation Typst — verifiez le champ 'typst_raw' de book.yaml. Details : <message original>"`
  - [x] 4.3 Si `typst_raw` n'est pas defini, laisser l'erreur remonter telle quelle (comportement actuel)
  - [x] 4.4 Propager `typst_raw` depuis `render_pdf()` vers `compile_typst()` via un parametre `has_typst_raw: bool = False`

- [x] Task 5 — Tests unitaires et integration (AC: #1, #2, #3, #4)
  - [x] 5.1 Test renderer : `generate_typst(book, path, config=...)` produit `#set page(numbering: "i")` dans la section front matter (remplace l'ancien test `numbering: none`)
  - [x] 5.2 Test renderer : le `.typ` genere contient bien l'ordre `numbering: "i"` ... `#counter(page).update(1)` ... `numbering: "1"` ... `= <premier chapitre>`
  - [x] 5.3 Test schema : `BookConfig(titre=..., typst_raw="#set text(fill: red)")` est valide et expose `typst_raw`
  - [x] 5.4 Test schema : `typst_raw` absent → `config.typst_raw is None`
  - [x] 5.5 Test renderer : `generate_typst` avec `config.typst_raw = "#let foo = 42"` injecte le contenu TEL QUEL (presence de `#let foo = 42` dans `.typ`, pas d'echappement)
  - [x] 5.6 Test renderer : injection placee apres le template et avant la page de titre
  - [x] 5.7 Test retro-compatibilite : `config.typst_raw = None` → pas de bloc `BEGIN typst_raw` dans le `.typ`
  - [x] 5.8 Test erreur : invoquer `compile_typst` avec un `.typ` invalide et `has_typst_raw=True` leve une `RenderError` mentionnant `typst_raw` (mock `run_external` pour lever une `RenderError` simulee)
  - [x] 5.9 Test erreur : meme test avec `has_typst_raw=False` ne mentionne pas `typst_raw`
  - [x] 5.10 Test integration pipeline : livre avec `typst_raw` dans `book.yaml` compile et injecte le contenu
  - [x] 5.11 Creer fixture `tests/fixtures/books/with_typst_raw/` avec un `book.yaml` minimal contenant un champ `typst_raw` benin

- [x] Task 6 — Mettre a jour le test existant affecte par le changement de numerotation
  - [x] 6.1 Adapter `tests/test_renderer_pdf.py::test_generate_typst_page_numbering_reset` : remplacer l'assertion `"#set page(numbering: none)"` par `'#set page(numbering: "i")'`
  - [x] 6.2 Adapter `test_front_matter_no_header_footer` et `test_multi_chapter_headers_footers` : idem
  - [x] 6.3 Verifier toute autre reference a `numbering: none` dans la suite de tests (`test_generate_typst_no_front_matter_without_config` adapte aussi)

## Dev Notes

### Contexte : pourquoi cette story existe

Story 4.4 ferme l'Epic 4 en livrant deux FRs distincts groupes dans la meme story pour leur petite taille individuelle :
- **FR14** (MVP1) : numerotation romaine/arabe differenciee — pur changement de template Typst (~2 lignes)
- **FR27** (MVP1) : escape hatch Typst — permet a l'auteur d'injecter du Typst natif pour les cas non couverts par les tokens

Ces deux fonctionnalites n'ont pas d'interaction entre elles ; implementer dans l'ordre propose (numerotation avant escape hatch) minimise les risques de regression.

### Etat actuel du code (NE PAS recrer)

Le pipeline de numerotation est **deja partiellement en place** dans `src/bookforge/renderers/pdf.py` :

- `_render_front_matter(config)` ligne 348 : ecrit actuellement `#set page(numbering: none)` au debut des pages liminaires → **a remplacer par `#set page(numbering: "i")`**
- `_render_running_headers(config)` ligne 382 : ecrit deja `numbering: "1"` + `#counter(page).update(1)` → **aucun changement requis ici**

La sequence finale dans le `.typ` doit etre :

```typst
// pages liminaires
#set page(numbering: "i")    // <-- CHANGEMENT (etait: none)

#align(center + horizon)[...]   // title page
#pagebreak()
...                              // copyright, dedicace, outline
#pagebreak()

// --- En-tetes/pieds + bascule en arabe ---
#set page(numbering: "1", header: ..., footer: ...)
#counter(page).update(1)         // deja present

// premier chapitre
= Introduction
...
```

### Escape hatch — Point d'injection exact

Dans `generate_typst()` (ligne ~431), le flux est :

```python
template = _build_template_from_tokens(tokens) if tokens is not None else _BASE_TEMPLATE
content_parts: list[str] = [template, "\n"]
# <<< INJECTER typst_raw ICI >>>
has_chapter_pages = config is not None
if config is not None:
    content_parts.append(_render_front_matter(config))
    content_parts.append(_render_running_headers(config))
for i, chapter in enumerate(book.chapters):
    ...
```

Code d'injection a inserer exactement a ce point :

```python
if config is not None and config.typst_raw:
    content_parts.append(
        "// --- BEGIN typst_raw (escape hatch — Story 4.4) ---\n"
    )
    content_parts.append(config.typst_raw)
    if not config.typst_raw.endswith("\n"):
        content_parts.append("\n")
    content_parts.append("// --- END typst_raw ---\n\n")
```

**Important** : injection APRES le template (les `#set` globaux) et AVANT `_render_front_matter` — ainsi l'auteur peut surcharger/completer la config du template.

### Enrichissement de l'erreur `compile_typst`

Signature actuelle : `compile_typst(typ_path: Path, pdf_path: Path) -> Path`

Modifier pour accepter un flag indiquant la presence d'un escape hatch, sans casser l'appelant externe :

```python
def compile_typst(
    typ_path: Path,
    pdf_path: Path,
    *,
    has_typst_raw: bool = False,
) -> Path:
    try:
        run_external(
            ["typst", "compile", str(typ_path), str(pdf_path)],
            description="Compilation Typst vers PDF",
        )
    except RenderError as e:
        if has_typst_raw:
            raise RenderError(
                "Echec de compilation Typst — verifiez le champ 'typst_raw' "
                f"de book.yaml. Details : {e}"
            )
        raise
    return pdf_path
```

`render_pdf()` passe ensuite `has_typst_raw=bool(config and config.typst_raw)`.

**Ne pas** essayer de parser le stderr Typst pour detecter la ligne fautive — c'est fragile et hors scope MVP1. Un message indicatif suffit.

### Schema Pydantic — Ajout minimal

Fichier `src/bookforge/config/schema.py` — ajouter UNE seule ligne dans `BookConfig` :

```python
class BookConfig(BaseModel):
    ...
    document_class: str = Field(default="business-manual", alias="class", ...)
    tokens: str | None = None
    typst_raw: str | None = None   # <-- NOUVEAU (Story 4.4, FR27)
```

Pas de validator custom : tout contenu string est accepte, la validation semantique est deleguee a Typst.

### Fixture a creer

`tests/fixtures/books/with_typst_raw/book.yaml` :

```yaml
titre: Livre avec escape hatch
auteur: Test
genre: business
chapitres:
  - titre: Introduction
    fichier: chapitres/01-introduction.md
typst_raw: |
  // Injection Typst native
  #let accent = rgb("#2563eb")
```

Et `tests/fixtures/books/with_typst_raw/chapitres/01-introduction.md` minimal :

```markdown
# Introduction

Paragraphe de test avec escape hatch Typst.
```

### Tests existants a ne pas casser

Story 4.3 a ajoute 26 tests → suite totale 210 tests, ruff clean, mypy clean. Ne pas reduire ce nombre. Les tests affectes par le changement de numerotation sont listes en Task 6 — les autres doivent passer sans modification.

Tests a auditer specifiquement pour `numbering: none` (recherche `grep`) :
- `tests/test_renderer_pdf.py::test_generate_typst_page_numbering_reset` (ligne ~678)
- `tests/test_renderer_pdf.py::test_front_matter_no_header_footer` (ligne ~885)
- `tests/test_renderer_pdf.py::test_numbering_reset_*` (ligne ~923)

Toutefois, `test_generate_typst_no_front_matter_without_config` (ligne ~695) verifie `"#set page(numbering: none)" not in content` quand pas de config — **celui-la reste correct** puisque sans config aucune numerotation n'est ecrite.

### Anti-patterns a eviter

- **NE PAS** echapper `typst_raw` avec `escape_typst()` — le but est precisement d'injecter du Typst brut
- **NE PAS** tenter de parser/valider la syntaxe `typst_raw` cote Python — c'est un escape hatch, la validation est deleguee a Typst
- **NE PAS** ajouter de nouvelles dependances (budget toujours a 5/5)
- **NE PAS** injecter `typst_raw` dans le template EPUB (`renderers/epub.py`) — FR27 est specifique au backend PDF/Typst. Si l'auteur veut customiser l'EPUB, c'est une future story (hors scope)
- **NE PAS** modifier `tokens/registry.py`, `tokens/resolver.py`, `tokens/defaults/` — aucun changement requis
- **NE PAS** modifier `pipeline.py` — le flux existant transporte deja `config` jusqu'a `render_pdf`
- **NE PAS** modifier `templates/typst/*.typ` — ces fichiers sont historiques, le renderer utilise les templates inline generes par `_build_template_from_tokens()`
- **NE PAS** utiliser `print()` — logger via `logging.getLogger("bookforge.renderers.pdf")`
- **NE PAS** utiliser `os.path` — `pathlib.Path` partout
- **NE PAS** casser les 210 tests existants (hormis les 3 a adapter en Task 6)

### Conventions de nommage

| Element | Convention | Exemple |
|---|---|---|
| Champ Pydantic | `snake_case` | `typst_raw` |
| Flag fonction | `snake_case` prefix `has_` | `has_typst_raw` |
| Test | `test_<what>_<condition>_<expected>` | `test_generate_typst_injects_typst_raw` |
| Commentaire injection | `// --- BEGIN/END typst_raw ---` | (voir code ci-dessus) |
| Logger | `bookforge.renderers.pdf` (existant) | — |

### Learnings de Story 4.3 (contexte)

- 3 nouveaux noeuds AST (frozen dataclasses) ajoutes avec pattern `source_file` + `line_number`
- Plugin markdown-it-py natif ajoute sans dependance `mdit-py-plugins`
- 26 tests ajoutes → 210/210 passent, ruff clean, mypy clean
- Pattern de commit stable : `feat(bookforge): implement Story X.Y — <description>`
- Dernier commit Epic 4 : `90e87ddc` (Story 4.3)
- Tous les renderers gerent deja les noeuds polymorphiquement via `_render_node()` — aucune plomberie a ajouter dans `pipeline.py`

### Pipeline end-to-end (rappel)

```
book.yaml → load_book_config() → BookConfig (avec typst_raw)
        → parse markdown → BookNode (AST)
        → resolve_tokens() → ResolvedTokenSet
        → render_pdf(book, output_dir, config, tokens)
            → generate_typst(book, typ_path, config, tokens)
                → _build_template_from_tokens(tokens)
                → INJECT config.typst_raw (nouveau)
                → _render_front_matter(config) → "#set page(numbering: \"i\")"
                → _render_running_headers(config) → bascule en "1" + reset compteur
                → _render_chapter(...) × N
            → compile_typst(typ_path, pdf_path, has_typst_raw=bool(config.typst_raw))
                → try/except RenderError → enrichir si has_typst_raw
```

### Project Structure Notes

- Tous les changements dans `src/bookforge/config/schema.py`, `src/bookforge/renderers/pdf.py`, `tests/`
- Pas de modification a `pipeline.py`, `parser/`, `ast_nodes/`, `tokens/`, `renderers/epub.py`
- Pas de modification a `templates/typst/*.typ` (template inline dans `pdf.py`)
- Nouvelle fixture : `tests/fixtures/books/with_typst_raw/`
- Pas de modification a `pyproject.toml`

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 4.4](../planning-artifacts/epics.md) — Acceptance criteria BDD
- [Source: _bmad-output/planning-artifacts/prd.md#FR14](../planning-artifacts/prd.md) — Numerotation romaine/arabe differenciee [MVP1]
- [Source: _bmad-output/planning-artifacts/prd.md#FR27](../planning-artifacts/prd.md) — Escape hatch moteur de rendu [MVP1]
- [Source: _bmad-output/planning-artifacts/architecture.md#Design tokens](../planning-artifacts/architecture.md) — FR25-27 : tokens YAML → templates, classes, escape hatch
- [Source: src/bookforge/renderers/pdf.py:348](../../src/bookforge/renderers/pdf.py#L348) — `_render_front_matter()` a modifier
- [Source: src/bookforge/renderers/pdf.py:382](../../src/bookforge/renderers/pdf.py#L382) — `_render_running_headers()` deja correct
- [Source: src/bookforge/renderers/pdf.py:431](../../src/bookforge/renderers/pdf.py#L431) — `generate_typst()` point d'injection
- [Source: src/bookforge/renderers/pdf.py:459](../../src/bookforge/renderers/pdf.py#L459) — `compile_typst()` a enrichir
- [Source: src/bookforge/config/schema.py:13](../../src/bookforge/config/schema.py#L13) — `BookConfig` : ajouter `typst_raw`
- [Source: src/bookforge/external.py:8](../../src/bookforge/external.py#L8) — `run_external()` leve deja `RenderError` avec stderr
- [Source: src/bookforge/errors.py:19](../../src/bookforge/errors.py#L19) — `RenderError(exit_code=2)`
- [Source: _bmad-output/implementation-artifacts/4-3-balises-semantiques-frameworks-callouts-chapter-summary.md](./4-3-balises-semantiques-frameworks-callouts-chapter-summary.md) — Story precedente : patterns dataclasses, tests, conventions

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

- Run `uv run pytest -q` : 223/223 tests passent (210 baseline Story 4.3 + 13 nouveaux)
- Run `uv run ruff check .` : All checks passed
- Run `uv run mypy src/bookforge` : Success, no issues found in 37 source files
- Les 36 erreurs mypy pre-existantes dans `tests/` (avant Story 4.4) n'ont pas ete introduites par cette story — `mypy strict` est configure pour `src/bookforge` uniquement

### Completion Notes List

- **FR14** (numerotation romaine/arabe) livre : `_render_front_matter()` ecrit desormais `#set page(numbering: "i")` (au lieu de `numbering: none`), puis `_render_running_headers()` bascule en `numbering: "1"` et reinitialise le compteur via `#counter(page).update(1)` — inchange.
- **FR27** (escape hatch Typst) livre : nouveau champ `BookConfig.typst_raw: str | None = None`, injecte tel quel (aucun echappement) entre le template et les pages liminaires, encadre par les marqueurs `// --- BEGIN/END typst_raw (escape hatch — Story 4.4) ---` pour le debogage.
- `compile_typst()` expose maintenant un kwarg `has_typst_raw: bool = False`. Quand `True`, toute `RenderError` remontee par `run_external` est re-levee avec un prefixe explicite : `"Echec de compilation Typst — verifiez le champ 'typst_raw' de book.yaml. Details : ..."`. Quand `False`, comportement 100% inchange (retro-compat stricte).
- `render_pdf()` calcule automatiquement le flag : `has_typst_raw = bool(config is not None and config.typst_raw)`.
- **13 nouveaux tests** ajoutes (`TestStory44NumerotationEtEscapeHatch` dans `test_renderer_pdf.py` + `test_pipeline_with_typst_raw_injects_in_typ` dans `test_pipeline.py`) couvrant : numerotation romaine, ordre romain→arabe→reset→chapitre, schema par defaut, schema avec valeur, injection verbatim sans echappement, position d'injection, retro-compat `None`, retro-compat chaine vide, erreur enrichie, erreur non enrichie, propagation du flag via `render_pdf` (avec et sans config), integration pipeline end-to-end.
- **4 tests existants adaptes** (`test_generate_typst_page_numbering_reset`, `test_generate_typst_no_front_matter_without_config`, `test_front_matter_no_header_footer`, `test_multi_chapter_headers_footers`) pour refleter `numbering: "i"` au lieu de `numbering: none`.
- **Fixture `with_typst_raw/`** creee avec `book.yaml` contenant un `typst_raw: |` bloc YAML multi-ligne benin (`#let accent = rgb("#2563eb")`) et un chapitre `01-introduction.md` minimal.
- Retro-compat verifiee sur toutes les fixtures existantes : `minimal`, `with_class`, `with_semantic`, `full`, `broken` — toutes les suites passent sans regression.
- Aucune nouvelle dependance ajoutee (budget `< 5 deps runtime` respecte).
- Aucune modification a `pipeline.py`, `parser/`, `ast_nodes/`, `tokens/`, `renderers/epub.py`, `templates/typst/*.typ`.

### Change Log

- 2026-04-09: Implementation Story 4.4 — numerotation romaine/arabe differenciee (FR14) + escape hatch Typst via `typst_raw` dans `book.yaml` (FR27). Erreur de compilation enrichie quand `typst_raw` est present.

### File List

- src/bookforge/config/schema.py (modified — ajout `typst_raw: str | None = None` dans `BookConfig`)
- src/bookforge/renderers/pdf.py (modified — `_render_front_matter` utilise `numbering: "i"`, `generate_typst` injecte `typst_raw`, `compile_typst` accepte `has_typst_raw` et enrichit les erreurs, `render_pdf` propage le flag)
- tests/test_renderer_pdf.py (modified — 4 tests existants adaptes a `numbering: "i"` + nouvelle classe `TestStory44NumerotationEtEscapeHatch` avec 12 tests)
- tests/test_pipeline.py (modified — ajout `test_pipeline_with_typst_raw_injects_in_typ`)
- tests/fixtures/books/with_typst_raw/book.yaml (new — fixture d'integration avec champ `typst_raw` benin)
- tests/fixtures/books/with_typst_raw/chapitres/01-introduction.md (new — chapitre minimal associe)
- _bmad-output/implementation-artifacts/sprint-status.yaml (modified — story 4-4 : backlog → ready-for-dev → in-progress → review)
- _bmad-output/implementation-artifacts/4-4-numerotation-differenciee-et-escape-hatch-typst.md (new — story spec, Dev Agent Record rempli)
