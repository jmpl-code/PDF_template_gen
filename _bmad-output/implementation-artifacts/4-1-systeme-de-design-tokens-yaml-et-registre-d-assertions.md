# Story 4.1 : Systeme de design tokens YAML et registre d'assertions

Status: review

## Story

As a auteur,
I want personnaliser le rendu via un fichier `tokens.yaml` simple (font_size, line_height, marges...),
So that j'adapte l'apparence sans toucher au code ni aux templates.

## Acceptance Criteria (BDD)

1. **Given** un fichier `tokens.yaml` avec des valeurs simples (ex: `font_size: 11`)
   **When** le systeme resout les tokens via le registre interne (`TokenSpec` avec min/max/source)
   **Then** un `ResolvedTokenSet` valide est produit

2. **Given** une valeur hors bornes (ex: `font_size: 3`)
   **When** le systeme resout les tokens
   **Then** un warning est emis avec la borne violee et la source de reference (ex: "font_size=3 hors bornes [9, 14] — source: Bringhurst")
   **And** la valeur par defaut est utilisee a la place

3. **Given** aucun fichier `tokens.yaml` fourni
   **When** le systeme resout les tokens
   **Then** les tokens par defaut de la classe `business-manual` sont charges depuis `defaults/business_manual.yaml`

4. **Given** un `ResolvedTokenSet` valide
   **When** les renderers PDF et EPUB consomment les tokens
   **Then** les valeurs sont appliquees au rendu (font_size, line_height, marges dans le `.typ` genere et le CSS EPUB)

5. **Given** un `tokens.yaml` avec une cle inconnue (non presente dans le registre)
   **When** le systeme resout les tokens
   **Then** un warning est emis et la cle est ignoree (pas d'erreur)

## Tasks / Subtasks

- [x] Task 1 — Modele `TokenSpec` et registre (AC: #1, #2, #5)
  - [x] 1.1 Creer `TokenSpec` dataclass dans `src/bookforge/tokens/registry.py` : champs `default`, `min`, `max`, `unit`, `source`
  - [x] 1.2 Definir `TOKEN_REGISTRY: dict[str, TokenSpec]` avec les 8 categories de tokens (geometrie page, typographie corps, hierarchie titres, espacement, couleurs, en-tetes/pieds, elements speciaux, couverture)
  - [x] 1.3 Commencer avec les tokens critiques MVP1 : `font_size`, `line_height`, `margin_inner`, `margin_outer`, `margin_top`, `margin_bottom`, `page_width`, `page_height`, `heading_1_size`, `heading_2_size`, `heading_3_size`, `heading_4_size`, `par_indent`, `par_skip`

- [x] Task 2 — Modele `ResolvedTokenSet` et resolver (AC: #1, #2, #3, #5)
  - [x] 2.1 Creer `ResolvedTokenSet` (Pydantic BaseModel) dans `src/bookforge/tokens/resolver.py` avec un champ par token
  - [x] 2.2 Implementer `resolve_tokens(user_yaml: Path | None) -> ResolvedTokenSet` :
    - Charger `defaults/business_manual.yaml` comme base
    - Si `user_yaml` fourni, surcharger avec les valeurs utilisateur
    - Pour chaque token : valider vs `TokenSpec` (min/max), emettre warning si hors bornes, utiliser defaut
    - Ignorer les cles inconnues avec warning
  - [x] 2.3 Creer `src/bookforge/tokens/defaults/business_manual.yaml` avec les valeurs par defaut professionnelles

- [x] Task 3 — Consommation par le renderer PDF (AC: #4)
  - [x] 3.1 Modifier `generate_typst()` dans `src/bookforge/renderers/pdf.py` pour accepter un parametre optionnel `tokens: ResolvedTokenSet | None`
  - [x] 3.2 Si `tokens` fourni, generer `_BASE_TEMPLATE` dynamiquement au lieu du template hardcode (remplacer les valeurs 11pt, 1.3em, 2cm, etc. par les tokens resolus)
  - [x] 3.3 Si `tokens` est `None`, conserver le comportement actuel (backward compatibility)

- [x] Task 4 — Consommation par le renderer EPUB (AC: #4)
  - [x] 4.1 Modifier `render_epub()` dans `src/bookforge/renderers/epub.py` pour accepter un parametre optionnel `tokens: ResolvedTokenSet | None`
  - [x] 4.2 Si `tokens` fourni, generer `_KINDLE_CSS` dynamiquement avec les valeurs des tokens
  - [x] 4.3 Si `tokens` est `None`, conserver le CSS statique actuel (backward compatibility)

- [x] Task 5 — Export du module tokens (AC: #1)
  - [x] 5.1 Exporter `TokenSpec`, `TOKEN_REGISTRY`, `ResolvedTokenSet`, `resolve_tokens` depuis `src/bookforge/tokens/__init__.py`

- [x] Task 6 — Tests (tous les AC)
  - [x] 6.1 Creer `tests/fixtures/tokens/valid.yaml` (tokens dans les bornes)
  - [x] 6.2 Creer `tests/fixtures/tokens/out_of_bounds.yaml` (tokens hors bornes)
  - [x] 6.3 Creer `tests/fixtures/tokens/unknown_keys.yaml` (cles inconnues)
  - [x] 6.4 Tests unitaires `tests/test_tokens.py` :
    - `test_resolve_tokens_defaults_only` — sans YAML, charge business_manual defaults
    - `test_resolve_tokens_valid_override` — surcharge avec valeurs valides
    - `test_resolve_tokens_out_of_bounds_warns` — hors bornes declenche warning + utilise defaut
    - `test_resolve_tokens_unknown_key_warns` — cle inconnue declenche warning + ignoree
    - `test_token_spec_registry_completeness` — chaque token du registre a min, max, source
    - `test_resolved_token_set_all_fields` — ResolvedTokenSet a une valeur pour chaque token du registre
  - [x] 6.5 Tests integration renderers :
    - `test_render_pdf_with_tokens` — verifier que le `.typ` contient les valeurs des tokens
    - `test_render_pdf_without_tokens_backward_compat` — sans tokens = template hardcode
    - `test_render_epub_with_tokens` — verifier que le CSS contient les valeurs des tokens
    - `test_render_epub_without_tokens_backward_compat` — sans tokens = CSS statique

## Dev Notes

### Patterns de code etablis (a respecter)

- **Subprocess pattern :** `run_external()` dans `src/bookforge/external.py` — toujours `capture_output=True, text=True, check=True`, wrapper en `RenderError`
- **Erreurs :** Hierarchie dans `src/bookforge/errors.py` — `InputError` (exit 1), `RenderError` (exit 2), `LLMError` (exit 3). Pour les tokens hors bornes, utiliser `logging.warning()` et **non** une exception
- **Logging :** Un logger par module via `logging.getLogger("bookforge.<module>")`. Pattern deja en place dans tous les renderers
- **Imports :** `from __future__ import annotations` en premiere ligne de chaque module
- **Pydantic v2 :** Utilise dans `config/schema.py` pour `BookConfig` — reutiliser pour `ResolvedTokenSet`
- **YAML :** `import yaml` deja utilise dans `renderers/epub.py` — PyYAML est deja une dependance

### Architecture — Le Triplet immuable

L'architecture definit un **Triplet immuable** `(BookNode, ClassConfig, ResolvedTokenSet)` comme contrat de rendu. Story 4.1 cree la partie `ResolvedTokenSet` de ce triplet. Story 4.2 ajoutera `ClassConfig`.

Pour cette story, le pipeline ne passe pas encore les tokens aux renderers (cela sera integre en 4.2 quand `ClassConfig` existe). **Cependant**, les renderers doivent **accepter** le parametre `tokens` optionnel et l'utiliser s'il est fourni — pour permettre les tests et preparer l'integration.

### Structure de fichiers cible

```
src/bookforge/tokens/
  __init__.py          # Exports: TokenSpec, TOKEN_REGISTRY, ResolvedTokenSet, resolve_tokens
  registry.py          # TokenSpec dataclass + TOKEN_REGISTRY dict
  resolver.py          # resolve_tokens() + ResolvedTokenSet Pydantic model
  defaults/
    business_manual.yaml  # Valeurs par defaut pour la classe business-manual
```

### Tokens MVP1 — 8 categories (architecture Decision 5)

| Categorie | Tokens a implementer | Source reference |
|---|---|---|
| Geometrie page | `page_width`, `page_height`, `margin_inner`, `margin_outer`, `margin_top`, `margin_bottom` | KDP specs (6x9in, marges min) |
| Typographie corps | `font_family`, `font_size`, `line_height` | Bringhurst (9-14pt, 1.20-1.45) |
| Hierarchie titres | `heading_1_size`, `heading_2_size`, `heading_3_size`, `heading_4_size` | KOMA-Script |
| Espacement | `par_indent`, `par_skip` | LaTeX memoir |

Les categories couleurs, en-tetes/pieds, elements speciaux, couverture seront ajoutees dans les stories suivantes (4.2+).

### Format du fichier `tokens.yaml` auteur

```yaml
# tokens.yaml (auteur — simple, flat, snake_case)
font_size: 11
line_height: 1.35
margin_inner: 20mm
page_width: 6in
page_height: 9in
```

### Format du registre interne (code)

```python
@dataclass(frozen=True)
class TokenSpec:
    default: int | float | str
    min: int | float | None = None
    max: int | float | None = None
    unit: str = ""
    source: str = ""

TOKEN_REGISTRY: dict[str, TokenSpec] = {
    "font_size": TokenSpec(default=11, min=9, max=14, unit="pt", source="Bringhurst"),
    "line_height": TokenSpec(default=1.35, min=1.20, max=1.45, source="Bringhurst §2.1"),
    # ...
}
```

### Anti-patterns a eviter

- **NE PAS** creer un systeme de tokens generique/extensible — YAGNI. Le registre est un `dict[str, TokenSpec]` statique defini en code
- **NE PAS** modifier `pipeline.py` dans cette story — l'integration pipeline sera faite en 4.2
- **NE PAS** utiliser `InputError` pour les tokens hors bornes — c'est un warning, pas une erreur. Le pipeline continue avec la valeur par defaut
- **NE PAS** ajouter de nouvelles dependances pip — PyYAML et Pydantic sont deja disponibles
- **NE PAS** casser la backward compatibility des renderers — le parametre `tokens` doit etre optionnel (`None` par defaut)
- **NE PAS** supprimer les constantes `_BASE_TEMPLATE` et `_KINDLE_CSS` — elles restent comme fallback quand `tokens` est `None`

### Mapping tokens vers Typst (renderer PDF)

| Token | Template Typst actuel (hardcode) | Cible dynamique |
|---|---|---|
| `page_width` | `width: 6in` | `width: {page_width}` |
| `page_height` | `height: 9in` | `height: {page_height}` |
| `margin_inner` | `inside: 2cm` | `inside: {margin_inner}` |
| `margin_outer` | `outside: 1.5cm` | `outside: {margin_outer}` |
| `margin_top` | `top: 2.5cm` | `top: {margin_top}` |
| `margin_bottom` | `bottom: 2cm` | `bottom: {margin_bottom}` |
| `font_size` | `size: 11pt` | `size: {font_size}pt` |
| `line_height` | `leading: 1.3em` | `leading: {line_height}em` |
| `par_indent` | `first-line-indent: 1em` | `first-line-indent: {par_indent}` |
| `heading_1_size` | `size: 24pt` | `size: {heading_1_size}pt` |
| `heading_2_size` | `size: 18pt` | `size: {heading_2_size}pt` |
| `heading_3_size` | `size: 14pt` | `size: {heading_3_size}pt` |
| `heading_4_size` | `size: 12pt` | `size: {heading_4_size}pt` |

### Mapping tokens vers CSS (renderer EPUB)

| Token | CSS Kindle actuel (hardcode) | Cible dynamique |
|---|---|---|
| `font_size` | implicite (defaut navigateur) | `body { font-size: {font_size}pt; }` |
| `line_height` | `line-height: 1.4` | `line-height: {line_height}` |
| `heading_1_size` | `font-size: 1.8em` | `font-size: {heading_1_size / font_size}em` (ratio relatif) |
| `heading_2_size` | `font-size: 1.4em` | `font-size: {heading_2_size / font_size}em` |
| `heading_3_size` | `font-size: 1.2em` | `font-size: {heading_3_size / font_size}em` |
| `heading_4_size` | `font-size: 1.1em` | `font-size: {heading_4_size / font_size}em` |
| `par_indent` | `text-indent: 1em` | `text-indent: {par_indent}` |

**Note EPUB :** Les tokens de geometrie page (marges, dimensions) ne s'appliquent pas a l'EPUB (format reflowable). Seuls les tokens typographiques sont pertinents.

### Project Structure Notes

- Le module `src/bookforge/tokens/` existe deja avec des fichiers squelettes (docstrings uniquement)
- Le dossier `tests/fixtures/tokens/` existe deja avec un `.gitkeep`
- Le dossier `src/bookforge/tokens/defaults/` doit etre cree
- Conventions de nommage YAML/config : `snake_case` pour les cles (cf. architecture)
- Conventions de nommage classes doc : `kebab-case` (ex: `business-manual`)

### Dependencies dans le module tokens/

```
tokens/registry.py   → aucune dependance bookforge (dataclass stdlib)
tokens/resolver.py   → tokens/registry.py, pydantic, yaml, logging
tokens/__init__.py    → tokens/registry.py, tokens/resolver.py
```

### Intelligence des commits recents

Les 10 derniers commits suivent le pattern `feat(bookforge): implement Story X.Y — <description>`. Conventions :
- Un commit par story
- Message en anglais
- Tests inclus dans le meme commit
- ruff + mypy clean avant commit
- 157 tests passent actuellement (zero regression)

### References

- [Source: _bmad-output/planning-artifacts/architecture.md — Decision 5 "Design Token Format"]
- [Source: _bmad-output/planning-artifacts/architecture.md — "Token Categories (8-Category Model)"]
- [Source: _bmad-output/planning-artifacts/architecture.md — "Tokens as Verifiable Assertions"]
- [Source: _bmad-output/planning-artifacts/epics.md — Epic 4, Story 4.1]
- [Source: _bmad-output/planning-artifacts/prd.md — FR25-27 "Design tokens & personnalisation"]
- [Source: src/bookforge/renderers/pdf.py — _BASE_TEMPLATE hardcode]
- [Source: src/bookforge/renderers/epub.py — _KINDLE_CSS hardcode]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

### Completion Notes List

- TokenSpec frozen dataclass avec 15 tokens MVP1 couvrant 4 categories (geometrie, typographie, titres, espacement)
- TOKEN_REGISTRY statique avec assertions min/max/source pour chaque token numerique
- ResolvedTokenSet Pydantic BaseModel avec resolve_tokens() : charge defaults classe → surcharge utilisateur → validation bornes
- Renderers PDF et EPUB acceptent un parametre `tokens` optionnel (backward compatible)
- Template Typst dynamique genere a partir des tokens resolus (remplace le hardcode)
- CSS EPUB dynamique avec ratios heading/font_size calcules
- 13 tests couvrant tous les AC : unitaires (registre, resolver, bornes, cles inconnues) + integration (PDF .typ, EPUB CSS, backward compat)
- 170/170 tests passent, zero regression, ruff clean, mypy clean

### Change Log

- 2026-04-07: Implementation Story 4.1 — systeme de design tokens YAML complet

### File List

- src/bookforge/tokens/__init__.py (modified — exports TokenSpec, TOKEN_REGISTRY, ResolvedTokenSet, resolve_tokens)
- src/bookforge/tokens/registry.py (modified — TokenSpec dataclass + TOKEN_REGISTRY)
- src/bookforge/tokens/resolver.py (modified — ResolvedTokenSet + resolve_tokens)
- src/bookforge/tokens/defaults/business_manual.yaml (modified — valeurs par defaut classe business-manual)
- src/bookforge/renderers/pdf.py (modified — _build_template_from_tokens + parametre tokens optionnel)
- src/bookforge/renderers/epub.py (modified — _build_css_from_tokens + parametre tokens optionnel)
- tests/test_tokens.py (new — 13 tests unitaires et integration)
- tests/fixtures/tokens/valid.yaml (new — fixture tokens valides)
- tests/fixtures/tokens/out_of_bounds.yaml (new — fixture tokens hors bornes)
- tests/fixtures/tokens/unknown_keys.yaml (new — fixture cles inconnues)
