# Story 3.2 : Dual export PDF + EPUB en une commande

Status: review

## Story

As a auteur,
I want produire PDF et EPUB en une seule execution du pipeline,
So that je gagne du temps et j'ai les deux formats prets simultanement.

## Acceptance Criteria

1. **Given** un `book.yaml` valide **When** je lance `python -m bookforge book.yaml` **Then** le dossier de sortie contient `livre-interieur.pdf` ET `livre.epub`
2. **And** les deux formats sont produits en une seule execution sans relance
3. **And** l'EPUB est genere en < 2 minutes pour 200 pages (NFR4)
4. **And** si le rendu EPUB echoue, le PDF est quand meme produit avec un warning (pas d'echec pipeline)

## Tasks / Subtasks

- [x] Task 1 — Etendre `organize_output()` dans `src/bookforge/export.py` pour accepter l'EPUB (AC: #1)
  - [x] 1.1 Ajouter parametre `epub_path: Path | None = None` a `organize_output()`
  - [x] 1.2 Si `epub_path` est fourni et existe, le copier vers `output_dir / "livre.epub"`
  - [x] 1.3 Logger la copie (ou l'absence) de l'EPUB
- [x] Task 2 — Integrer `render_epub()` dans `src/bookforge/pipeline.py` (AC: #1, #2, #4)
  - [x] 2.1 Importer `render_epub` depuis `bookforge.renderers.epub`
  - [x] 2.2 En Phase 2 (Render), apres `render_pdf()` et `render_cover()`, appeler `render_epub(book, book_root, config=config)`
  - [x] 2.3 Encapsuler l'appel `render_epub()` dans un `try/except RenderError` : si echec, logger un `logger.warning(...)` et continuer avec `epub_path = None`
  - [x] 2.4 Passer `epub_path` a `organize_output()` en Phase 3
  - [x] 2.5 Mettre a jour les logs de phase : `"Phase 2/3: rendering PDF + EPUB"`
- [x] Task 3 — Exporter `render_epub` dans `src/bookforge/renderers/__init__.py` (AC: #2)
  - [x] 3.1 Ajouter `from bookforge.renderers.epub import render_epub` et l'inclure dans `__all__`
- [x] Task 4 — Tests (AC: #1-4)
  - [x] 4.1 `test_export.py` — `organize_output` avec `epub_path=None` → meme comportement qu'avant (retro-compatibilite)
  - [x] 4.2 `test_export.py` — `organize_output` avec `epub_path` fourni → `livre.epub` copie dans output
  - [x] 4.3 `test_pipeline.py` — pipeline complet → output contient `livre-interieur.pdf` ET `livre.epub`
  - [x] 4.4 `test_pipeline.py` — echec EPUB (mock `render_epub` leve `RenderError`) → PDF produit, pas d'exception pipeline
  - [x] 4.5 `test_pipeline.py` — callback progress toujours appele correctement (parsing, rendering, export)
  - [x] 4.6 Verifier zero regression — tous les tests existants passent (157 total, zero regression)

## Dev Notes

### Architecture et pattern a suivre

Cette story est une **integration pure** — aucun nouveau module, aucun nouvel algorithme. Il s'agit d'orchestrer `render_epub()` (deja complet depuis Story 3.1) dans le pipeline existant.

**Principe cle :** L'EPUB est un livrable **secondaire** par rapport au PDF. Son echec ne doit JAMAIS bloquer la production du PDF (AC #4). C'est la seule vraie complexite de cette story.

### Fichiers a modifier

| Fichier | Action | Complexite |
|---------|--------|------------|
| `src/bookforge/export.py` | Ajouter param `epub_path` a `organize_output()` | Faible |
| `src/bookforge/pipeline.py` | Appeler `render_epub()` + try/except + passer epub a `organize_output()` | Moyenne |
| `src/bookforge/renderers/__init__.py` | Ajouter export `render_epub` | Triviale |
| `tests/test_export.py` | 2 nouveaux tests | Faible |
| `tests/test_pipeline.py` | 3 nouveaux tests (dont mock EPUB failure) | Moyenne |

### Fichiers a NE PAS modifier

- `src/bookforge/renderers/epub.py` — deja complet (Story 3.1)
- `src/bookforge/renderers/pdf.py` — inchange
- `src/bookforge/renderers/cover.py` — inchange
- `src/bookforge/cli.py` — aucune option CLI a ajouter (dual export = comportement par defaut, FR18)
- `src/bookforge/config/schema.py` — pas de champ format a ajouter
- `src/bookforge/errors.py` — RenderError existe deja et suffit
- `src/bookforge/external.py` — inchange

### Code de reference : pipeline.py actuel (Phase 2)

```python
# Phase 2 — Render (ACTUEL)
_notify(progress_callback, "rendering", 0)
logger.info("Phase 2/3: rendering PDF")
interior_pdf = render_pdf(book, book_root, config=config)
cover_pdf = render_cover(config, book_root)
logger.info("Rendered interior and cover PDFs")
_notify(progress_callback, "rendering", 100)
```

**Cible apres modification :**

```python
# Phase 2 — Render (CIBLE)
_notify(progress_callback, "rendering", 0)
logger.info("Phase 2/3: rendering PDF + EPUB")
interior_pdf = render_pdf(book, book_root, config=config)
cover_pdf = render_cover(config, book_root)

epub_path: Path | None = None
try:
    epub_path = render_epub(book, book_root, config=config)
except RenderError as exc:
    logger.warning("EPUB rendering failed, continuing with PDF only: %s", exc)

logger.info("Rendered interior PDF, cover PDF%s", " and EPUB" if epub_path else "")
_notify(progress_callback, "rendering", 100)
```

### Code de reference : export.py — `organize_output()` modification

```python
# ACTUEL
def organize_output(
    config: BookConfig,
    interior_pdf: Path,
    cover_pdf: Path,
    output_dir: Path,
) -> Path:

# CIBLE — ajout param optionnel
def organize_output(
    config: BookConfig,
    interior_pdf: Path,
    cover_pdf: Path,
    output_dir: Path,
    epub_path: Path | None = None,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(interior_pdf, output_dir / "livre-interieur.pdf")
    shutil.copy2(cover_pdf, output_dir / "couverture.pdf")
    if epub_path is not None:
        shutil.copy2(epub_path, output_dir / "livre.epub")
        logger.debug("Copied EPUB to output: %s", output_dir / "livre.epub")
    export_metadata_kdp(config, output_dir)
    return output_dir
```

### Code de reference : renderers/__init__.py

```python
# CIBLE
from bookforge.renderers.cover import render_cover
from bookforge.renderers.epub import render_epub
from bookforge.renderers.pdf import render_pdf

__all__ = ["render_cover", "render_epub", "render_pdf"]
```

### Pattern de test pour mock EPUB failure

Les tests pipeline existants mockent `bookforge.renderers.pdf.run_external` et `bookforge.renderers.cover.run_external`. Pour la Story 3.2, il faut aussi mocker `bookforge.renderers.epub.run_external`.

```python
# Exemple pour test echec EPUB
with (
    patch("bookforge.renderers.pdf.run_external") as mock_pdf_ext,
    patch("bookforge.renderers.cover.run_external") as mock_cover_ext,
    patch("bookforge.renderers.epub.run_external") as mock_epub_ext,
):
    mock_pdf_ext.side_effect = fake_pdf_compile
    mock_cover_ext.side_effect = fake_cover_compile
    mock_epub_ext.side_effect = RenderError("Pandoc not found")

    result = run_pipeline(...)
    # Le pipeline ne doit PAS lever d'exception
    # livre-interieur.pdf et couverture.pdf doivent exister
    # livre.epub ne doit PAS exister
```

Pour le test succes, mocker `render_epub` pour creer un fichier EPUB factice :

```python
def fake_epub_pandoc(cmd: list[str], description: str):
    # Pandoc est appele avec -o comme dernier argument
    epub_path = Path(cmd[-1])
    epub_path.parent.mkdir(parents=True, exist_ok=True)
    epub_path.write_bytes(b"PK fake epub")  # EPUB = ZIP = commence par PK
    return MagicMock()
```

**Attention :** `render_epub()` ecrit des fichiers intermediaires (content.md, metadata.yaml, epub.css) dans `_epub_build/` avant d'appeler Pandoc. Le mock de `run_external` doit creer le fichier EPUB final car `render_epub()` retourne son chemin.

### Nommage du fichier EPUB dans le dossier de sortie

Le fichier EPUB final dans le dossier de sortie doit etre `livre.epub` (sans "interieur" — l'EPUB est un livrable unique, pas une separation interieur/couverture comme le PDF KDP).

### Anti-patterns a eviter

1. **NE PAS** ajouter de parallelisme (threading/asyncio) pour les renderers — hors scope, rendement minimal pour MVP0.5
2. **NE PAS** ajouter d'option CLI `--formats` — le dual export est le comportement par defaut (FR18)
3. **NE PAS** modifier `render_epub()` — il est complet depuis Story 3.1
4. **NE PAS** modifier `render_pdf()` — inchange
5. **NE PAS** creer de nouveau module — c'est une integration de modules existants
6. **NE PAS** faire echouer le pipeline si EPUB echoue — c'est l'AC #4 critique
7. **NE PAS** utiliser un `except Exception` generique pour l'echec EPUB — attraper uniquement `RenderError`
8. **NE PAS** utiliser `os.path` — `pathlib.Path` uniquement
9. **NE PAS** modifier les fixtures de test existantes
10. **NE PAS** changer la signature de `run_pipeline()` — elle est deja correcte

### Previous Story Intelligence (Story 3.1)

- **152 tests** passent — zero regression attendue
- Pattern `from __future__ import annotations` en premiere ligne de chaque module
- Logger par module : `logging.getLogger("bookforge.<module>")`
- Logging interne en **anglais** (debug/info/warning)
- `mkdir(parents=True, exist_ok=True)` pour creer les dossiers
- Commit pattern : `feat(bookforge): implement Story X.Y — description`
- ruff + mypy stricts — corriger avant commit
- Convention de test : `test_<quoi>_<condition>_<attendu>()`
- Mock pattern : mocker `run_external` dans les tests renderer, pas les vrais appels subprocess
- `render_epub()` retourne `Path` vers `output_dir / "livre.epub"` — utiliser ce chemin directement
- Le renderer EPUB ecrit ses artefacts intermediaires dans `output_dir / "_epub_build/"`
- `render_epub(book, output_dir, config=config)` — meme signature que `render_pdf()`

### Git Intelligence

Derniers commits pertinents :
- `271a6ae8` feat(bookforge): implement Story 3.1 — EPUB renderer via Pandoc
- `3ff7d190` refactor(bookforge): use parse_book from parser module and fix CLI test stderr
- `2d51d30b` feat(bookforge): implement Story 2.9 — CLI, logging and progress reporting

Fichiers modifies dans Story 3.1 :
- `src/bookforge/renderers/epub.py` (stub → renderer complet)
- `tests/test_renderer_epub.py` (cree, 15 tests)

### Project Structure Notes

- Integration pure : modification de 3 fichiers source + 2 fichiers de test
- Aucun nouveau fichier source, aucun nouveau module
- La structure de test suit le pattern existant (classes par fonctionnalite, `_copy_fixture_to`, mocks `run_external`)
- Les tests existants de `test_pipeline.py` et `test_export.py` ne doivent PAS etre modifies, seulement de nouveaux tests ajoutes

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 3.2] — User story et acceptance criteria
- [Source: _bmad-output/planning-artifacts/prd.md#FR18] — PDF + EPUB en une seule commande
- [Source: _bmad-output/planning-artifacts/prd.md#NFR4] — Export EPUB < 2 minutes pour 200 pages
- [Source: _bmad-output/planning-artifacts/architecture.md#Phase 2] — Render parallelisable, dual format split
- [Source: _bmad-output/implementation-artifacts/3-1-renderer-epub-via-pandoc.md] — Previous story patterns et intelligence

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

- ruff F401: removed unused `BookConfig` import in pipeline.py (pre-existing issue, not introduced by this story)

### Completion Notes List

- `organize_output()` etendu avec param optionnel `epub_path: Path | None = None` — copie `livre.epub` si fourni
- `pipeline.py` Phase 2 appelle `render_epub()` avec try/except `RenderError` — echec EPUB = warning, pipeline continue
- `renderers/__init__.py` exporte `render_epub`
- 5 nouveaux tests: 2 export (retro-compatibilite + copie EPUB) + 3 pipeline (dual export succes, echec EPUB gracieux, callbacks)
- 157/157 tests passent, ruff clean, mypy clean
- Aucun nouveau module, aucune nouvelle dependance

### Change Log

- 2026-04-07: Story 3.2 implemented — Dual export PDF + EPUB en une commande

### File List

- **src/bookforge/pipeline.py** — Modified (ajout render_epub + try/except RenderError, suppression import BookConfig inutilise)
- **src/bookforge/export.py** — Modified (param epub_path ajouté a organize_output)
- **src/bookforge/renderers/__init__.py** — Modified (export render_epub)
- **tests/test_pipeline.py** — Modified (3 tests ajoutes: TestDualExport)
- **tests/test_export.py** — Modified (2 tests ajoutes: epub retro-compatibilite + copie)
