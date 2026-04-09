# Story 5.1 : 4e de couverture et calcul du dos

Status: ready-for-dev

<!-- Note: Validation est optionnelle. Lancer validate-create-story pour un quality check avant dev-story. -->

## Story

As a auteur,
I want generer une 4e de couverture avec pitch, bio et code-barres ISBN, et que le dos soit calcule automatiquement,
So that j'ai tous les elements requis pour l'impression KDP.

## Acceptance Criteria (BDD)

1. **Given** un `book.yaml` enrichi avec `pitch_4e`, `bio_auteur` et `isbn`, et le PDF interieur `livre-interieur.pdf` deja genere
   **When** le module couverture est execute (`render_back_cover()` ou equivalent)
   **Then** un fichier `4e-de-couverture.pdf` est produit dans le dossier de sortie
   **And** le PDF contient le texte du `pitch_4e` et le texte du `bio_auteur`
   **And** un code-barres EAN-13 base sur l'ISBN est present sur la 4e de couverture

2. **Given** un `book.yaml` avec un ISBN valide et un nombre de pages connu de l'interieur
   **When** la fonction `compute_spine_width_inches(pages: int) -> float` est appelee
   **Then** elle retourne `pages * 0.002252` (formule KDP papier blanc)
   **And** le resultat est expose au pipeline pour usage par la Story 5.2 (assemblage couverture complete)
   **And** la valeur calculee est loggee en mode `INFO` (`Spine width: 0.135 in for 60 pages`)

3. **Given** un `book.yaml` SANS champ `isbn` (ou `isbn: null`)
   **When** `render_back_cover()` est appele
   **Then** la 4e de couverture est generee SANS code-barres (pas de bloc visuel reserve)
   **And** un warning est logge : `"ISBN absent : 4e de couverture generee sans code-barres EAN-13"`
   **And** aucune `RenderError` n'est levee (degradation gracieuse, conforme NFR6)

4. **Given** un `book.yaml` SANS `pitch_4e` ou SANS `bio_auteur`
   **When** `render_back_cover()` est appele
   **Then** les sections manquantes ne sont pas affichees (pas de placeholder vide)
   **And** un warning par champ manquant est logge en mode `WARNING`
   **And** la 4e de couverture est tout de meme produite (au minimum avec le titre repris en haut + une zone vide ou contracted)

5. **Given** un ISBN syntaxiquement invalide (ex: `"978-INVALID"`, longueur != 13 apres normalisation, ou somme de controle EAN-13 fausse)
   **When** `render_back_cover()` est appele
   **Then** une `InputError` est levee AVANT l'invocation de Typst, avec un message explicite : `"ISBN invalide : 'XXX' (attendu : EAN-13 a 13 chiffres avec checksum valide)"`
   **And** la couverture interieure (story 2.7) n'est pas re-generee (pas d'effet de bord)

6. **Given** un `book.yaml` avec `pitch_4e`, `bio_auteur` et `isbn` valides
   **When** le pipeline complet `run_pipeline()` s'execute
   **Then** le dossier de sortie contient (en plus des livrables existants) `4e-de-couverture.pdf`
   **And** le pipeline expose la valeur du `spine_width_inches` calculee dans son retour ou dans le logging structurels (preparation Story 5.2)
   **And** aucune regression sur les 223 tests existants

## Tasks / Subtasks

> ✅ **DECISIONS TECHNIQUES VERROUILLEES** (2026-04-10, JM) :
> - **Code-barres** : package Typst `@preview/tiaoma:0.3.0` — fetch online au premier run accepte
> - **Page count** : `typst query` avec label `<book-meta>` injecte dans `generate_typst()`
> - **Cache CI** : ajouter step de cache `~/.cache/typst/` (Linux) / `%LOCALAPPDATA%\typst\` (Windows) dans GitHub Actions pour eviter le re-fetch a chaque build

- [ ] Task 1 — Etendre `BookConfig` avec les champs 4e de couverture (AC: #1, #4)
  - [ ] 1.1 Ajouter `pitch_4e: str | None = None` dans `BookConfig` (`src/bookforge/config/schema.py`), apres `description`
  - [ ] 1.2 Ajouter `bio_auteur: str | None = None` dans `BookConfig`, apres `pitch_4e`
  - [ ] 1.3 Aucun validator custom (chaines libres, multi-lignes acceptees)
  - [ ] 1.4 Verifier que `isbn: str | None = None` existe deja (ligne 22) — ne pas dupliquer
  - [ ] 1.5 Ajouter une normalisation : helper `_normalize_isbn(raw: str) -> str` qui retire tirets/espaces et retourne 13 chiffres (utilise par Task 4)

- [ ] Task 2 — Helper `compute_spine_width_inches` (AC: #2)
  - [ ] 2.1 Creer `src/bookforge/renderers/spine.py` (nouveau fichier, module dedie)
  - [ ] 2.2 Definir `def compute_spine_width_inches(pages: int) -> float` qui retourne `pages * 0.002252`
  - [ ] 2.3 Lever `ValueError("pages doit etre > 0")` si `pages <= 0`
  - [ ] 2.4 Documenter la formule via docstring + reference architecture.md ligne 134 (`papier blanc KDP`)
  - [ ] 2.5 Pas de constante magique : exposer `KDP_WHITE_PAPER_INCHES_PER_PAGE = 0.002252` au niveau module

- [ ] Task 3 — Extraction du nombre de pages depuis le PDF interieur (AC: #2)
  - [ ] 3.1 Approche retenue : **Typst metadata query** (zero nouvelle dep Python, voir Dev Notes)
  - [ ] 3.2 Modifier `generate_typst()` (`src/bookforge/renderers/pdf.py`) : ajouter en fin de document Typst la ligne `[#metadata((page-count: counter(page).final().first())) <book-meta>]`
  - [ ] 3.3 Apres `compile_typst()`, invoquer `typst query <typ_path> "<book-meta>" --format json` via `run_external()` et parser le JSON pour extraire `page-count`
  - [ ] 3.4 Encapsuler ceci dans une fonction `query_page_count(typ_path: Path) -> int` dans `src/bookforge/renderers/spine.py`
  - [ ] 3.5 Si la query echoue (Typst absent, JSON malforme, label manquant) : lever `RenderError("Impossible d'extraire le nombre de pages : <details>")`
  - [ ] 3.6 Exporter `query_page_count`, `compute_spine_width_inches`, `KDP_WHITE_PAPER_INCHES_PER_PAGE` depuis `spine.py`

- [ ] Task 4 — Generateur de la 4e de couverture dans `cover.py` (AC: #1, #3, #4, #5)
  - [ ] 4.1 Dans `src/bookforge/renderers/cover.py`, ajouter la fonction `generate_back_cover_typst(config: BookConfig, output_path: Path) -> Path`
  - [ ] 4.2 Definir une constante `_BACK_COVER_TEMPLATE` (template inline, pattern identique a `_COVER_TEMPLATE`) avec les zones : titre repris en haut (16pt bold), pitch (11pt justified), bio auteur (10pt italic), zone code-barres en bas a droite
  - [ ] 4.3 Format page : 6×9 in (identique au livre interieur, identique a la couverture), marges `(x: 1.5cm, y: 2cm)`
  - [ ] 4.4 Pour le code-barres EAN-13 : utiliser le **package Typst `@preview/tiaoma:0.3.0`** (voir Dev Notes pour decision et alternatives) — appel `#tiaoma.ean13("9781234567897")`
  - [ ] 4.5 Si `config.isbn is None` : ne PAS importer `tiaoma`, ne PAS reserver de zone barcode, logger `warning("ISBN absent : 4e de couverture generee sans code-barres EAN-13")`
  - [ ] 4.6 Si `config.pitch_4e is None` : omettre la zone pitch + warning
  - [ ] 4.7 Si `config.bio_auteur is None` : omettre la zone bio + warning
  - [ ] 4.8 Echapper `pitch_4e` et `bio_auteur` via `escape_typst()` (deja importe depuis `pdf.py`)
  - [ ] 4.9 Validation ISBN AVANT generation : appeler `_normalize_isbn()` (Task 1.5) puis verifier longueur 13 et checksum EAN-13 (algorithme : somme ponderee 1/3 sur les 12 premiers digits, modulo 10)
  - [ ] 4.10 Si validation echoue → `raise InputError(f"ISBN invalide : '{config.isbn}' (attendu : EAN-13 a 13 chiffres avec checksum valide)")`
  - [ ] 4.11 Ajouter `compile_back_cover(typ_path, pdf_path) -> Path` (pattern identique a `compile_cover()`)
  - [ ] 4.12 Ajouter `render_back_cover(config: BookConfig, output_dir: Path) -> Path | None` qui retourne `None` si TOUS les champs (`pitch_4e`, `bio_auteur`, `isbn`) sont absents (rien a rendre)

- [ ] Task 5 — Integration dans le pipeline (AC: #6)
  - [ ] 5.1 Dans `src/bookforge/pipeline.py`, apres `interior_pdf = render_pdf(...)` et avant `render_cover(...)`, calculer `page_count = query_page_count(typ_path)` — necessite que `render_pdf` retourne le `.typ` ou conserve un chemin connu
  - [ ] 5.2 Adapter `render_pdf()` pour exposer le chemin du `.typ` genere (ajouter un retour secondaire ou un attribut accessible) — option recommandee : retourner un dataclass `PdfRenderResult(pdf_path: Path, typ_path: Path)` plutot que casser la signature actuelle qui retourne `Path`
  - [ ] 5.3 Calculer `spine_width = compute_spine_width_inches(page_count)` et logger `INFO`
  - [ ] 5.4 Apres `render_cover(...)`, invoquer `back_cover_pdf = render_back_cover(config, book_root)` (None si pas de contenu)
  - [ ] 5.5 Si `back_cover_pdf is not None` : passer ce chemin a `organize_output()` (etendre la signature avec `back_cover_path: Path | None = None`)
  - [ ] 5.6 Dans `organize_output()` (`src/bookforge/export.py`), copier `back_cover_pdf` vers `output_dir / "4e-de-couverture.pdf"` si fourni
  - [ ] 5.7 Stocker `spine_width_inches` dans le retour du pipeline pour usage Story 5.2 — option : retourner un dataclass `PipelineResult(output_dir: Path, spine_width_inches: float | None)` au lieu de `Path` seul. **Coordonner avec l'API publique : si breaking change, ajouter param de compat ou wrapper.**

- [ ] Task 6 — Fixture de test integration (AC: #1, #2, #6)
  - [ ] 6.1 Creer `tests/fixtures/books/with_back_cover/book.yaml` :
    ```yaml
    titre: "Mon Livre Avec 4e"
    sous_titre: "Un test integration"
    auteur: "JM"
    genre: "business"
    isbn: "9781234567897"   # ISBN EAN-13 valide (checksum correct)
    pitch_4e: |
      Ce livre vous explique tout ce que vous devez savoir sur le sujet.
      Lecture indispensable pour les entrepreneurs.
    bio_auteur: |
      JM est consultant en entreprise depuis 20 ans.
      Auteur de plusieurs ouvrages de reference.
    chapitres:
      - titre: "Introduction"
        fichier: "chapitres/01-introduction.md"
    ```
  - [ ] 6.2 Creer `tests/fixtures/books/with_back_cover/chapitres/01-introduction.md` minimal (memes contenu que `with_typst_raw`)
  - [ ] 6.3 Verifier que l'ISBN choisi (`9781234567897`) a un checksum EAN-13 valide (calcul manuel ou via test unitaire)

- [ ] Task 7 — Tests unitaires (AC: tous)
  - [ ] 7.1 `tests/test_spine.py` (NOUVEAU FICHIER) :
    - `test_compute_spine_width_60_pages` : `60 * 0.002252 == 0.13512`
    - `test_compute_spine_width_zero_pages_raises` : `pages=0` → `ValueError`
    - `test_compute_spine_width_negative_raises` : `pages=-5` → `ValueError`
    - `test_compute_spine_width_constant_exposed` : `KDP_WHITE_PAPER_INCHES_PER_PAGE == 0.002252`
    - `test_query_page_count_typst_missing_raises_render_error` : mock `run_external` pour simuler echec → `RenderError`
    - `test_query_page_count_returns_int` : mock `run_external` pour retourner JSON valide → int retourne
  - [ ] 7.2 Etendre `tests/test_cover.py` avec une nouvelle classe `TestBackCover` :
    - `test_back_cover_with_all_fields` : config complete → `.typ` contient pitch + bio + appel `tiaoma.ean13`
    - `test_back_cover_without_isbn_skips_barcode` : pas d'ISBN → `.typ` ne contient pas `tiaoma`, warning logge
    - `test_back_cover_without_pitch_omits_section` : pas de `pitch_4e` → `.typ` ne contient pas la zone pitch, warning logge
    - `test_back_cover_without_bio_omits_section` : pas de `bio_auteur` → `.typ` ne contient pas la zone bio, warning logge
    - `test_back_cover_invalid_isbn_raises_input_error` : ISBN `"978-INVALID"` → `InputError` avec mention de l'ISBN
    - `test_back_cover_isbn_checksum_invalid_raises` : ISBN `"9781234567890"` (checksum faux) → `InputError`
    - `test_back_cover_isbn_normalization` : ISBN `"978-1-2345-6789-7"` (avec tirets) → normalise et accepte
    - `test_back_cover_special_chars_escaped_in_pitch` : pitch contenant `#`, `$` → escape applique
    - `test_back_cover_returns_none_if_all_empty` : config sans pitch/bio/isbn → `render_back_cover` retourne `None`
  - [ ] 7.3 Tests integration `tests/test_pipeline.py` :
    - `test_pipeline_with_back_cover_produces_4e_pdf` : fixture `with_back_cover` → `output_dir / "4e-de-couverture.pdf"` existe (mock Typst si necessaire)
    - `test_pipeline_without_back_cover_skips_4e` : fixture `minimal` → pas de fichier `4e-de-couverture.pdf` cree
  - [ ] 7.4 Tests integration `tests/test_export.py` :
    - `test_organize_output_copies_back_cover_when_provided`
    - `test_organize_output_skips_back_cover_when_none`
  - [ ] 7.5 Tests `tests/test_renderer_pdf.py` :
    - `test_generate_typst_includes_book_meta_label` : verifie la presence de `<book-meta>` dans le `.typ` genere

- [ ] Task 8 — Cache CI des packages Typst (Decision 1)
  - [ ] 8.0.1 Dans `.github/workflows/ci.yml` (cf. Story 1.3), ajouter un step `actions/cache@v4` AVANT le step de tests/build :
    ```yaml
    - name: Cache Typst packages
      uses: actions/cache@v4
      with:
        path: |
          ~/.cache/typst
          ~/AppData/Local/typst
          ~/Library/Caches/typst
        key: typst-packages-v1
    ```
  - [ ] 8.0.2 Verifier que le step est place AVANT toute invocation de `typst compile` ou `typst query` dans le workflow
  - [ ] 8.0.3 Smoke test : pousser une branche et observer dans les logs CI le hit/miss de cache (premier run = miss + download, runs suivants = hit + 0 download)

- [ ] Task 9 — Validation finale et regression (AC: tous)
  - [ ] 9.1 `uv run pytest -q` : 100% pass (223 baseline + nouveaux ≈ 240+)
  - [ ] 9.2 `uv run ruff check .` : 0 erreur
  - [ ] 9.3 `uv run mypy src/bookforge` : 0 erreur (mypy strict)
  - [ ] 9.4 Smoke test manuel : compiler la fixture `with_back_cover` end-to-end et inspecter visuellement le `4e-de-couverture.pdf` (Typst doit fetch `tiaoma` une seule fois sur premier run, ensuite cache local)
  - [ ] 9.5 Inspecter le `.typ` genere de la 4e pour verifier l'import `tiaoma` et l'appel `ean13`

## Dev Notes

### Contexte : pourquoi cette story existe

Story 5.1 ouvre **Epic 5 (Couverture complete KDP)**. Elle couvre 3 FRs du PRD :
- **FR21** (MVP1) : 4e de couverture avec pitch, bio, code-barres ISBN
- **FR22** (MVP1) : calcul largeur du dos selon nombre de pages
- **FR24** (MVP1, partiel) : preparation pour la miniature (page count expose pour Story 5.2)

L'objectif final d'Epic 5 (Story 5.2) est d'**assembler** couverture-avant + dos calcule + 4e en une image complete KDP. Cette story 5.1 produit les **briques separees** : la 4e de couverture comme PDF independant + le `spine_width` comme valeur calculee dans le pipeline.

### Etat actuel du code (NE PAS reinventer)

| Fichier | Etat | Action Story 5.1 |
|---|---|---|
| `src/bookforge/renderers/cover.py` | Story 2.7 livree : `_COVER_TEMPLATE`, `generate_cover_typst()`, `compile_cover()`, `render_cover()` | **Etendre** : ajouter `_BACK_COVER_TEMPLATE`, `generate_back_cover_typst()`, `compile_back_cover()`, `render_back_cover()` |
| `src/bookforge/config/schema.py` | `BookConfig` Pydantic v2, `isbn: str \| None = None` deja present (ligne 22) | **Etendre** : ajouter `pitch_4e`, `bio_auteur` |
| `src/bookforge/pipeline.py` | Phase 2 appelle `render_pdf()` puis `render_cover()` puis `render_epub()` puis `organize_output()` | **Etendre** : extraire page count entre `render_pdf` et `render_cover`, appeler `render_back_cover` |
| `src/bookforge/export.py` | `organize_output(config, interior_pdf, cover_pdf, output_dir, epub_path=None)` | **Etendre** : ajouter `back_cover_path: Path \| None = None` |
| `src/bookforge/renderers/pdf.py` | `render_pdf()` retourne `Path` (interior PDF) | **Modifier** : retourner `PdfRenderResult(pdf_path, typ_path)` ou exposer le chemin `.typ` autrement |
| `src/bookforge/errors.py` | `InputError`, `RenderError` (exit codes 1, 2) | **Reutiliser** — ne pas creer de nouvelle classe |
| `src/bookforge/external.py` | `run_external(cmd, description)` leve `RenderError` avec stderr | **Reutiliser** pour `typst query` |

**Pattern existant a reproduire** (Story 2.7) : template inline en constante string + 3 fonctions (`generate_*_typst`, `compile_*`, `render_*`). Voir `cover.py` lignes 14-86 pour reference exacte.

### Decisions techniques verrouillees (2026-04-10, JM)

#### ✅ Decision 1 : Code-barres EAN-13 → package Typst `@preview/tiaoma:0.3.0`

**Choix retenu** : import Typst natif `#import "@preview/tiaoma:0.3.0": ean13` puis `#ean13("9781234567897")` dans le template de la 4e.

**Trade-off accepte** : la premiere compilation sur une machine vierge declenche un download HTTP unique (~quelques Ko) depuis `packages.typst.org` vers le cache local Typst. Compilations suivantes 100% offline. JM accepte explicitement ce besoin online.

**Cache CI** : ajouter dans `.github/workflows/ci.yml` un step `actions/cache@v4` sur les chemins :
- Linux : `~/.cache/typst/`
- Windows : `~/AppData/Local/typst/`
- macOS : `~/Library/Caches/typst/`

Cle de cache : `typst-packages-${{ hashFiles('**/*.typ') }}` ou plus simplement `typst-packages-v1` (le contenu change rarement).

**A FAIRE AVANT CODE** : verifier rapidement sur https://typst.app/universe/package/tiaoma que la version `0.3.0` existe et que la signature publique est bien `ean13(code: str)`. Si l'API a change (autre version, autre nom de fonction), adapter — mais ne pas changer d'approche.

#### ✅ Decision 2 : Page count → `typst query` avec label `<book-meta>`

**Choix retenu** : injecter en fin de `generate_typst()` (PAS dans `_BASE_TEMPLATE` qui est le header) la ligne :
```typst
#metadata((page-count: counter(page).final().first())) <book-meta>
```
Puis appeler `typst query <typ_path> "<book-meta>" --format json` via `run_external()`. Parse le JSON via `json.loads()` (stdlib) :
```json
[ { "value": { "page-count": 60 } } ]
```

**Pourquoi pas pypdf** : meme avec NFR13 non-bloquante, `typst query` est idiomatique cote Typst, deterministe, et evite un round-trip de parsing PDF binaire pour une info que Typst connait nativement. Pas de dep ajoutee = pas de friction inutile (sans pour autant en faire un dogme).

**Verifier** : que l'ajout du label invisible n'impacte aucun test existant qui assert sur des chaines specifiques du `.typ` genere (lecon Epic 4 retro #5 sur la fragilite des golden sous-strings).

### Schema Pydantic — Ajouts minimaux

Fichier `src/bookforge/config/schema.py` :

```python
class BookConfig(BaseModel):
    ...
    isbn: str | None = None
    dedicace: str | None = None
    description: str | None = None
    pitch_4e: str | None = None       # <-- NOUVEAU (Story 5.1, FR21)
    bio_auteur: str | None = None     # <-- NOUVEAU (Story 5.1, FR21)
    mots_cles: list[str] | None = None
    ...
```

Pas de validator custom : ce sont des chaines libres multi-lignes (comme `description`).

### Helper de normalisation et validation ISBN

```python
def _normalize_isbn(raw: str) -> str:
    """Retire tirets et espaces, retourne 13 chiffres."""
    cleaned = raw.replace("-", "").replace(" ", "")
    if not cleaned.isdigit() or len(cleaned) != 13:
        raise InputError(
            f"ISBN invalide : '{raw}' (attendu : EAN-13 a 13 chiffres)"
        )
    if not _validate_ean13_checksum(cleaned):
        raise InputError(
            f"ISBN invalide : '{raw}' (checksum EAN-13 incorrect)"
        )
    return cleaned


def _validate_ean13_checksum(digits: str) -> bool:
    """EAN-13 checksum: sum(d_i * (1 if i pair else 3)) % 10 == 0."""
    total = sum(int(d) * (3 if i % 2 else 1) for i, d in enumerate(digits))
    return total % 10 == 0
```

A placer dans `src/bookforge/renderers/cover.py` (helpers prives) ou dans un nouveau module `src/bookforge/isbn.py` si l'utilisateur prefere isoler. **Recommandation : helpers prives dans `cover.py`** (eviter de creer un module pour 20 lignes).

### Template Typst 4e de couverture (squelette)

```typst
// 4e de couverture — BookForge (Story 5.1)
// Format 6x9 pouces (KDP standard, identique a la couverture avant)

#import "@preview/tiaoma:0.3.0": ean13   // SEULEMENT si ISBN present

#set page(
  width: 6in,
  height: 9in,
  margin: (x: 1.5cm, y: 2cm),
  numbering: none,
)

#set text(font: "New Computer Modern", lang: "fr", region: "FR")

// Titre repris en haut
#align(center)[
  #text(size: 16pt, weight: "bold")[{titre}]
]
#v(1.5cm)

// Pitch (si present)
#text(size: 11pt)[
  #par(justify: true)[{pitch_4e}]
]
#v(1cm)

// Bio auteur (si present)
#text(size: 10pt, style: "italic")[
  #par(justify: true)[{bio_auteur}]
]

#v(1fr)

// Code-barres EAN-13 en bas a droite (si ISBN present)
#align(right + bottom)[
  #ean13("{isbn_normalized}")
]
```

L'import `tiaoma` doit etre conditionnel — utiliser un assemblage Python qui inclut/omet la ligne `#import` selon presence ISBN.

### Modifications a `_BASE_TEMPLATE` pour la query page count

Dans `src/bookforge/renderers/pdf.py`, ajouter en TOUTE FIN du fichier `.typ` genere par `generate_typst()` (apres tous les chapitres) :

```typst
#metadata((page-count: counter(page).final().first())) <book-meta>
```

Le label `<book-meta>` est invisible dans le rendu mais queryable via `typst query`. **Attention** : cette ligne doit etre injectee dans `generate_typst()`, PAS dans `_BASE_TEMPLATE` (qui est le header de page setup).

Verifier que l'ajout n'impacte aucun test golden / aucun test qui compte les pages.

### Pipeline modifie — flux

```
book.yaml → load_book_config() → BookConfig (avec pitch_4e, bio_auteur)
        → parse markdown → BookNode
        → resolve_tokens() → ResolvedTokenSet
        → render_pdf(book, output_dir, config, tokens) → PdfRenderResult(pdf_path, typ_path)
        → page_count = query_page_count(typ_path)              [NEW]
        → spine_width = compute_spine_width_inches(page_count) [NEW]
        → logger.info("Spine width: %s in for %d pages", ...)  [NEW]
        → render_cover(config, book_root)                       [existant]
        → back_cover = render_back_cover(config, book_root)    [NEW, peut etre None]
        → render_epub(...)                                      [existant]
        → organize_output(config, interior_pdf, cover_pdf, output_dir,
                          epub_path=epub_path,
                          back_cover_path=back_cover)           [signature etendue]
        → return PipelineResult(output_dir, spine_width_inches=spine_width)
```

**Breaking change a gerer** : `run_pipeline()` retourne actuellement `Path`. Le passer a `PipelineResult` impacte `cli.py` et les tests. Alternative non-breaking : retourner toujours `Path` et stocker le `spine_width` dans un fichier metadata du dossier output (ex: `spine-info.json`). **Choisir l'option non-breaking par defaut** sauf si l'utilisateur prefere le dataclass.

### Fichiers a modifier — recap

| Fichier | Type | Changement |
|---|---|---|
| `src/bookforge/config/schema.py` | modify | Ajout `pitch_4e`, `bio_auteur` |
| `src/bookforge/renderers/cover.py` | modify | Ajout `_BACK_COVER_TEMPLATE`, `generate_back_cover_typst`, `compile_back_cover`, `render_back_cover`, helpers ISBN |
| `src/bookforge/renderers/spine.py` | new | `compute_spine_width_inches`, `query_page_count`, `KDP_WHITE_PAPER_INCHES_PER_PAGE` |
| `src/bookforge/renderers/__init__.py` | modify | Exporter `render_back_cover`, `compute_spine_width_inches` |
| `src/bookforge/renderers/pdf.py` | modify | Injection `<book-meta>` label en fin de `generate_typst()` ; `render_pdf()` expose le `typ_path` |
| `src/bookforge/pipeline.py` | modify | Calcul page count + spine width + invocation `render_back_cover` |
| `src/bookforge/export.py` | modify | `organize_output` accepte `back_cover_path` |
| `tests/test_spine.py` | new | Tests unitaires spine + page count |
| `tests/test_cover.py` | modify | Classe `TestBackCover` (~10 tests) |
| `tests/test_renderer_pdf.py` | modify | Test injection `<book-meta>` |
| `tests/test_pipeline.py` | modify | Tests integration `with_back_cover` |
| `tests/test_export.py` | modify | Tests `organize_output` avec `back_cover_path` |
| `tests/fixtures/books/with_back_cover/book.yaml` | new | Fixture integration |
| `tests/fixtures/books/with_back_cover/chapitres/01-introduction.md` | new | Chapitre minimal |
| `pyproject.toml` | **PAS de modification** | Aucune nouvelle dep — verifier explicitement |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | modify | `5-1` : ready-for-dev → in-progress → review |

### Anti-patterns a eviter

- **NE PAS** reimplementer EAN-13 a la main — tiaoma est verrouille (Decision 1)
- **NE PAS** parser le PDF interieur avec `pypdf` ou regex — `typst query` est verrouille (Decision 2)
- (Note : ajouter une dep Python n'est PAS interdit en general sur ce projet — NFR13 n'est pas une contrainte forte. Si une story future en a besoin, c'est OK. Pour 5.1, les 2 decisions ci-dessus sont juste les meilleures techniquement, pas un evitement de dep.)
- **NE PAS** faire de calcul du spine cote Typst — le calcul est cote Python, Typst recoit le resultat (separation des responsabilites)
- **NE PAS** parser le PDF interieur en Python — utiliser `typst query` (Decision 2 Option A)
- **NE PAS** echouer silencieusement si l'ISBN est absent — c'est une degradation gracieuse explicite avec warning (NFR6)
- **NE PAS** echouer silencieusement si l'ISBN est invalide — c'est une erreur dure (`InputError`) car l'auteur a explicitement fourni une valeur incorrecte
- **NE PAS** modifier `templates/typst/cover.typ` (fichier historique non utilise — voir lecon Story 4.4)
- **NE PAS** dupliquer le code de `generate_cover_typst` pour la 4e — extraire les helpers communs si pertinent (mais ne pas sur-abstraire pour 2 fonctions)
- **NE PAS** appeler `render_back_cover` AVANT `render_pdf` — le page count depend de l'interieur compile
- **NE PAS** modifier `renderers/epub.py` — la 4e est specifique au pipeline PDF
- **NE PAS** ajouter `pitch_4e`/`bio_auteur` dans `metadata-kdp.json` (export.py) — ces champs sont specifiques au layout, pas aux metadonnees KDP machine-readable
- **NE PAS** utiliser `print()` — logger via `logging.getLogger("bookforge.renderers.cover")`
- **NE PAS** utiliser `os.path` — `pathlib.Path` partout
- **NE PAS** casser les 223 tests existants

### Conventions de nommage

| Element | Convention | Exemple |
|---|---|---|
| Champ Pydantic | `snake_case` | `pitch_4e`, `bio_auteur` |
| Fonction module | `snake_case` | `render_back_cover`, `compute_spine_width_inches` |
| Constante module | `UPPER_SNAKE_CASE` | `KDP_WHITE_PAPER_INCHES_PER_PAGE` |
| Test | `test_<what>_<condition>_<expected>` | `test_back_cover_without_isbn_skips_barcode` |
| Logger | `bookforge.renderers.cover`, `bookforge.renderers.spine` | — |
| Fichier sortie | `4e-de-couverture.pdf` (kebab-case avec chiffre) | identique au pattern `livre-interieur.pdf`, `couverture.pdf` |

### Learnings de stories precedentes (a appliquer)

- **Story 2.7** : pattern `generate_*_typst` + `compile_*` + `render_*` → reproduire pour la 4e
- **Story 2.8** : `organize_output()` deja extensible via params nommes → ajouter `back_cover_path` proprement
- **Story 4.1** : `tokens` est `| None` partout → meme pattern pour `pitch_4e`/`bio_auteur`
- **Story 4.4** : escape hatch injecte VERBATIM → mais ici `pitch_4e`/`bio_auteur` ne sont PAS un escape hatch, donc DOIVENT etre echappes via `escape_typst()`
- **Epic 4 retro #2** : eviter toute nouvelle dep meme officielle → respecter strict 5/5 (decisions techniques 1+2)
- **Epic 4 retro #5** : assertions sur sous-strings de templates sont fragiles → utiliser `in` matching avec marqueurs uniques (`tiaoma.ean13`, `<book-meta>`) plutot que des chaines completes

### Commits attendus

Pattern Epic 4 : `feat(bookforge): implement Story 5.1 — 4e de couverture et calcul du dos`
Si fixes post-review : commit separe `fix(bookforge): address Story 5.1 review findings`

### Project Structure Notes

- Nouveau module `src/bookforge/renderers/spine.py` justifie : isole la logique de calcul + page count, testable independamment, reutilise par Story 5.2
- Pas de modification a `parser/`, `ast_nodes/`, `tokens/`, `passes/`, `quality/`, `judge/`
- Pas de modification a `templates/typst/*.typ` (templates inline dans les fichiers Python)
- Nouvelle fixture `with_back_cover/` suit le pattern existant (`minimal/`, `with_typst_raw/`)

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 5.1](../planning-artifacts/epics.md) — AC BDD initial (lignes 492-504)
- [Source: _bmad-output/planning-artifacts/prd.md#FR21](../planning-artifacts/prd.md) — 4e de couverture [MVP1]
- [Source: _bmad-output/planning-artifacts/prd.md#FR22](../planning-artifacts/prd.md) — Calcul largeur dos [MVP1]
- [Source: _bmad-output/planning-artifacts/architecture.md#KDP-specs](../planning-artifacts/architecture.md) — Specs KDP, formule spine 0.002252 (ligne 134)
- [Source: _bmad-output/planning-artifacts/architecture.md#NFR13](../planning-artifacts/architecture.md) — Budget deps clarification (ligne 768)
- [Source: src/bookforge/renderers/cover.py:14-86](../../src/bookforge/renderers/cover.py) — Pattern existant `generate_cover_typst`/`compile_cover`/`render_cover` a reproduire
- [Source: src/bookforge/config/schema.py:13-41](../../src/bookforge/config/schema.py) — `BookConfig` actuel
- [Source: src/bookforge/pipeline.py:78-93](../../src/bookforge/pipeline.py) — Phase 2 du pipeline a etendre
- [Source: src/bookforge/export.py:37-55](../../src/bookforge/export.py) — `organize_output` a etendre
- [Source: src/bookforge/renderers/pdf.py](../../src/bookforge/renderers/pdf.py) — `generate_typst` ou injecter `<book-meta>`
- [Source: src/bookforge/external.py:8](../../src/bookforge/external.py) — `run_external` pour invoquer `typst query`
- [Source: src/bookforge/errors.py](../../src/bookforge/errors.py) — `InputError` (exit 1), `RenderError` (exit 2)
- [Source: tests/test_cover.py](../../tests/test_cover.py) — Pattern de test existant pour la couverture avant
- [Source: _bmad-output/implementation-artifacts/2-7-couverture-template-statique.md](./2-7-couverture-template-statique.md) — Story originale du module cover
- [Source: _bmad-output/implementation-artifacts/4-4-numerotation-differenciee-et-escape-hatch-typst.md](./4-4-numerotation-differenciee-et-escape-hatch-typst.md) — Pattern d'extension du schema + tests
- [Source: _bmad-output/implementation-artifacts/epic-4-retro-2026-04-09.md](./epic-4-retro-2026-04-09.md) — Lecons retenues (deps, golden files)
- Externe : https://typst.app/universe (verifier package `tiaoma` et signature `ean13`)
- Externe : https://kdp.amazon.com/en_US/help/topic/G201953020 (specs KDP cover, formule spine)

## Dev Agent Record

### Agent Model Used

(a remplir par dev agent)

### Debug Log References

### Completion Notes List

### File List

### Change Log
