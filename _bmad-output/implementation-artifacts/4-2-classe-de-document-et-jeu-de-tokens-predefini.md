# Story 4.2 : Classe de document et jeu de tokens predefini

Status: done

## Story

As a auteur,
I want choisir une classe de document (`business-manual`) qui precharge un jeu de tokens coherent,
So that j'obtiens un rendu professionnel sans configuration manuelle.

## Acceptance Criteria (BDD)

1. **Given** `book.yaml` avec `class: business-manual`
   **When** le pipeline charge la configuration
   **Then** les tokens par defaut de la classe sont charges depuis `defaults/business_manual.yaml`
   **And** un `ResolvedTokenSet` valide est produit

2. **Given** `book.yaml` avec `class: business-manual` et un fichier `tokens.yaml` dans le meme repertoire
   **When** le pipeline charge la configuration
   **Then** les tokens auteur surchargent les tokens de classe
   **And** le `ResolvedTokenSet` final contient les valeurs auteur pour les cles presentes et les defauts de classe pour les autres

3. **Given** un `ResolvedTokenSet` resolus (classe + surcharges)
   **When** le renderer PDF genere le fichier `.typ`
   **Then** les valeurs des tokens sont appliquees (font_size, marges, line_height, heading sizes)
   **And** le rendu est identique a ce que produirait un appel direct avec les memes tokens

4. **Given** un `ResolvedTokenSet` resolus (classe + surcharges)
   **When** le renderer EPUB genere le CSS
   **Then** les valeurs des tokens sont appliquees (font_size, line_height, heading ratios, par_indent)

5. **Given** `book.yaml` sans champ `class`
   **When** le pipeline charge la configuration
   **Then** la classe par defaut `business-manual` est utilisee (backward compatibility)
   **And** le comportement est identique a avant cette story

6. **Given** `book.yaml` avec `class: unknown-class`
   **When** le pipeline charge la configuration
   **Then** un warning est emis indiquant que la classe est inconnue
   **And** les tokens par defaut du registre (`TOKEN_REGISTRY`) sont utilises comme fallback

## Tasks / Subtasks

- [x] Task 1 — Ajouter le champ `class` a BookConfig (AC: #1, #5, #6)
  - [x] 1.1 Ajouter `document_class: str = "business-manual"` a `BookConfig` dans `src/bookforge/config/schema.py`
  - [x] 1.2 Ajouter `tokens: str | None = None` a `BookConfig` pour le chemin optionnel vers un fichier `tokens.yaml` auteur
  - [x] 1.3 Valider que `document_class` est en kebab-case (regex `^[a-z][a-z0-9]*(-[a-z0-9]+)*$`)

- [x] Task 2 — Integrer resolve_tokens() dans le pipeline (AC: #1, #2, #3, #4, #5)
  - [x] 2.1 Dans `run_pipeline()` de `src/bookforge/pipeline.py`, apres le chargement de la config :
    - Determiner le chemin `user_yaml` : si `config.tokens` est defini, resoudre le chemin relatif a `book_root` ; sinon, verifier si `book_root / "tokens.yaml"` existe
    - Appeler `resolve_tokens(user_yaml=user_yaml, class_name=config.document_class)`
  - [x] 2.2 Passer le `ResolvedTokenSet` aux appels `render_pdf()` et `render_epub()` via le parametre `tokens=`
  - [x] 2.3 Logger les tokens resolus au niveau DEBUG : `"Tokens resolved for class '%s'", config.document_class`

- [x] Task 3 — Tests unitaires BookConfig (AC: #1, #5, #6)
  - [x] 3.1 Test `test_book_config_with_class` — BookConfig accepte `class: business-manual`
  - [x] 3.2 Test `test_book_config_default_class` — Sans champ `class`, utilise `business-manual`
  - [x] 3.3 Test `test_book_config_with_tokens_path` — BookConfig accepte `tokens: custom-tokens.yaml`
  - [x] 3.4 Test `test_book_config_class_validation` — Rejet des noms de classe invalides (espaces, majuscules)

- [x] Task 4 — Tests integration pipeline (AC: #1, #2, #3, #4, #5, #6)
  - [x] 4.1 Creer fixture `tests/fixtures/books/with_class/book.yaml` avec `class: business-manual`
  - [x] 4.2 Creer fixture `tests/fixtures/books/with_class/tokens.yaml` avec quelques surcharges (ex: `font_size: 12`)
  - [x] 4.3 Creer fixture `tests/fixtures/books/with_class/chapitres/01-introduction.md` (chapitre minimal)
  - [x] 4.4 Test `test_pipeline_with_class_resolves_tokens` — verifier que le `.typ` genere contient les tokens de classe
  - [x] 4.5 Test `test_pipeline_with_class_and_user_tokens` — verifier que les surcharges auteur sont appliquees dans le `.typ`
  - [x] 4.6 Test `test_pipeline_without_class_backward_compat` — verifier que le pipeline sans `class` fonctionne comme avant
  - [x] 4.7 Test `test_pipeline_unknown_class_warns` — verifier le warning et le fallback pour une classe inconnue

- [x] Task 5 — Mettre a jour l'exemple book.yaml (AC: #1)
  - [x] 5.1 Ajouter le champ `class` dans `docs/book.yaml.example` avec commentaire explicatif

## Dev Notes

### Ce que Story 4.1 a deja implementer (NE PAS refaire)

Tout le systeme de tokens est DEJA en place et fonctionnel :
- `TokenSpec` + `TOKEN_REGISTRY` dans `src/bookforge/tokens/registry.py` — 15 tokens, 4 categories
- `ResolvedTokenSet` + `resolve_tokens()` dans `src/bookforge/tokens/resolver.py` — charge defaults classe, surcharge utilisateur, validation bornes
- `defaults/business_manual.yaml` — valeurs par defaut completes
- `_build_template_from_tokens()` dans `src/bookforge/renderers/pdf.py` — generation Typst dynamique
- `_build_css_from_tokens()` dans `src/bookforge/renderers/epub.py` — generation CSS dynamique
- Les renderers `render_pdf()` et `render_epub()` acceptent deja `tokens: ResolvedTokenSet | None`
- Securite : `_safe_dim()`, `_safe_font()`, `_safe_css_dim()` — validation regex
- 13 tests dans `tests/test_tokens.py` couvrant tous les cas

**Cette story ne touche PAS les fichiers tokens/. L'objectif est uniquement l'integration dans le pipeline.**

### Changements requis — Vue synthetique

| Fichier | Changement | Raison |
|---|---|---|
| `src/bookforge/config/schema.py` | Ajouter `document_class` et `tokens` a `BookConfig` | AC #1, #5 |
| `src/bookforge/pipeline.py` | Appeler `resolve_tokens()` et passer aux renderers | AC #1-#4 |
| `tests/test_config.py` | Tests du champ `document_class` | AC #1, #5, #6 |
| `tests/test_pipeline.py` | Tests integration pipeline + tokens | AC #1-#6 |
| `tests/fixtures/books/with_class/` | Nouvelles fixtures | Support tests |
| `docs/book.yaml.example` | Ajouter champ `class` | Documentation |

### Choix du nom de champ : `document_class` (pas `class`)

`class` est un mot reserve Python. Utiliser `document_class` dans le modele Pydantic avec un alias YAML :

```python
document_class: str = Field(
    default="business-manual",
    alias="class",
    pattern=r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$",
)
```

Cela permet d'ecrire `class: business-manual` dans le YAML tout en utilisant `config.document_class` dans le code Python.

**Important :** Configurer `model_config = ConfigDict(populate_by_name=True)` dans BookConfig pour que les deux noms fonctionnent.

### Integration pipeline — Code cible

```python
# Dans run_pipeline(), apres config = load_book_config(book_path)
from bookforge.tokens import resolve_tokens

# Determiner le chemin tokens.yaml auteur
user_tokens_path: Path | None = None
if config.tokens:
    user_tokens_path = book_root / config.tokens
    if not user_tokens_path.exists():
        raise InputError(f"Fichier tokens introuvable : {user_tokens_path}")
else:
    auto_path = book_root / "tokens.yaml"
    if auto_path.exists():
        user_tokens_path = auto_path

tokens = resolve_tokens(user_yaml=user_tokens_path, class_name=config.document_class)
logger.debug("Tokens resolved for class '%s'", config.document_class)

# Passer aux renderers
interior_pdf = render_pdf(book, book_root, config=config, tokens=tokens)
epub_path = render_epub(book, book_root, config=config, tokens=tokens)
```

### Signatures actuelles des renderers (DEJA en place depuis 4.1)

```python
# pdf.py
def render_pdf(book, output_dir, config=None, tokens=None) -> Path

# epub.py  
def render_epub(book, output_dir, config=None, tokens=None) -> Path
```

Aucune modification de signature necessaire. Il suffit de passer `tokens=tokens`.

### Conventions de nommage classe de document

- `book.yaml` : `class: business-manual` (kebab-case)
- Code Python : `config.document_class` (snake_case)
- Fichier defaults : `defaults/business_manual.yaml` (snake_case, conversion `-` → `_` deja geree dans `resolve_tokens()`)

### Anti-patterns a eviter

- **NE PAS** modifier les fichiers `tokens/registry.py`, `tokens/resolver.py`, ou `tokens/defaults/` — ils sont complets
- **NE PAS** modifier les renderers `pdf.py` ou `epub.py` — ils acceptent deja les tokens
- **NE PAS** creer un systeme de ClassConfig complexe — le champ `document_class` dans BookConfig suffit, la logique de chargement est dans `resolve_tokens(class_name=...)`
- **NE PAS** ajouter de nouvelles dependances pip
- **NE PAS** casser les tests existants (170 tests passent actuellement)
- **NE PAS** modifier `render_cover()` dans cette story — la couverture est traitee en Epic 5
- **NE PAS** utiliser `model_validator` pour la classe — un simple `Field(pattern=...)` suffit

### Backward compatibility — Critique

Le pipeline doit fonctionner **exactement comme avant** si `book.yaml` n'a pas de champ `class`. Cela signifie :
- `document_class` a un defaut `"business-manual"`
- Sans `tokens.yaml` auteur et sans `class`, le pipeline charge les defaults `business_manual.yaml` qui reproduisent les valeurs actuellement hardcodees dans `_BASE_TEMPLATE`
- Les tests existants (fixtures `minimal/`, `full/`, `broken/`) ne doivent pas casser

### Fixtures existantes a NE PAS modifier

```
tests/fixtures/books/minimal/book.yaml    — pas de champ class → defaut
tests/fixtures/books/full/book.yaml       — pas de champ class → defaut
tests/fixtures/books/broken/              — cas d'erreur existants
tests/fixtures/tokens/                    — fixtures tokens deja completes
```

### Intelligence Story 4.1 — Lecons apprises

1. **Securite :** Les tokens string doivent etre valides par regex avant interpolation Typst/CSS — deja fait dans 4.1, ne pas contourner
2. **Path traversal :** `resolve_tokens()` a deja une protection `is_relative_to()` — ne pas contourner
3. **YAML errors :** `resolve_tokens()` gere deja `yaml.YAMLError` et `OSError` — ne pas re-wrapper
4. **Backward compat :** Le parametre `tokens=None` des renderers declenche le fallback hardcode — tester que ce path fonctionne toujours
5. **Defaults dupliques :** Les defaults existent en 3 endroits (registry, ResolvedTokenSet, business_manual.yaml) — design decision MVP1, ne pas tenter de dedupliquer

### Git Intelligence

- Pattern de commit : `feat(bookforge): implement Story X.Y — <description>`
- Dernier commit : `fix(bookforge): address code review findings for Story 4.1` (9ee0212e)
- 170 tests passent, ruff clean, mypy clean
- Story 4.1 = 2 commits (impl + review fixes)

### Project Structure Notes

- Alignement avec la structure unifiee : tous les changements dans `src/bookforge/` et `tests/`
- Le fichier `templates/typst/business_manual.typ` est un stub (2 lignes) — ne pas le modifier dans cette story
- `docs/book.yaml.example` existe deja — ajouter le champ `class` avec commentaire

### References

- [Source: _bmad-output/planning-artifacts/architecture.md — Decision 5 "Design Token Format"]
- [Source: _bmad-output/planning-artifacts/architecture.md — "Triplet immuable (BookNode, ClassConfig, ResolvedTokenSet)"]
- [Source: _bmad-output/planning-artifacts/architecture.md — Project Structure "config/schema.py"]
- [Source: _bmad-output/planning-artifacts/epics.md — Epic 4, Story 4.2]
- [Source: _bmad-output/planning-artifacts/prd.md — FR26 "Classe de document pre-chargeant un jeu de tokens"]
- [Source: _bmad-output/implementation-artifacts/4-1-systeme-de-design-tokens-yaml-et-registre-d-assertions.md — Dev Notes, Review Findings]
- [Source: src/bookforge/config/schema.py — BookConfig actuel (pas de champ class)]
- [Source: src/bookforge/pipeline.py — run_pipeline() actuel (pas d'appel resolve_tokens)]
- [Source: src/bookforge/tokens/resolver.py — resolve_tokens(user_yaml, class_name)]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

### Completion Notes List

- Champ `document_class` ajoute a BookConfig avec alias YAML `class`, defaut `business-manual`, validation kebab-case via regex pattern
- Champ `tokens` optionnel ajoute a BookConfig pour chemin explicite vers un fichier tokens.yaml auteur
- `ConfigDict(populate_by_name=True)` configure pour supporter alias et nom Python
- Pipeline integre : `resolve_tokens()` appele apres `load_book_config()`, tokens passes a `render_pdf()` et `render_epub()`
- Auto-detection : si pas de `config.tokens`, le pipeline cherche automatiquement `book_root / "tokens.yaml"`
- Fichier tokens explicite introuvable leve `InputError` (pas de fallback silencieux)
- 8 tests unitaires BookConfig (alias, defaut, custom, validation pattern x3, tokens path, tokens default)
- 6 tests integration pipeline (class + tokens, surcharges, backward compat, unknown class warning, explicit tokens path, missing tokens error)
- 184/184 tests passent, zero regression, ruff clean, mypy clean

### Change Log

- 2026-04-07: Implementation Story 4.2 — classe de document et integration tokens pipeline

### File List

- src/bookforge/config/schema.py (modified — ajout document_class + tokens fields, ConfigDict)
- src/bookforge/pipeline.py (modified — import resolve_tokens, resolution tokens, passage aux renderers)
- tests/test_config.py (modified — 8 tests TestBookConfigDocumentClass)
- tests/test_pipeline.py (modified — 6 tests TestPipelineTokenIntegration)
- tests/fixtures/books/with_class/book.yaml (new — fixture avec class: business-manual)
- tests/fixtures/books/with_class/tokens.yaml (new — fixture surcharges auteur)
- tests/fixtures/books/with_class/chapitres/01-introduction.md (new — chapitre minimal)
- docs/book.yaml.example (new — exemple complet commente avec champs class et tokens)
