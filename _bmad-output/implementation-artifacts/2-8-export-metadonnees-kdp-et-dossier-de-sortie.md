# Story 2.8: Export metadonnees KDP et dossier de sortie

Status: review

## Story

As a auteur,
I want que les metadonnees KDP soient exportees et la sortie organisee dans un dossier structure,
so that je peux copier-coller les metadonnees sur KDP et retrouver facilement mes fichiers.

## Acceptance Criteria

1. **Given** un `BookConfig` avec description, mots-cles, categories **When** le pipeline termine **Then** un fichier `metadata-kdp.json` est genere avec description, mots-cles et categories prets a copier-coller
2. **Given** le pipeline termine avec succes **When** le dossier de sortie est cree **Then** `output/` contient les fichiers nommes explicitement (`livre-interieur.pdf`, `couverture.pdf`, `metadata-kdp.json`)
3. **Given** les memes entrees **When** l'export est execute deux fois **Then** la structure est coherente a chaque execution (determinisme)
4. **Given** un `BookConfig` sans description ni mots-cles (champs optionnels) **When** l'export est execute **Then** `metadata-kdp.json` est genere avec les champs absents mis a `null` ou liste vide
5. **Given** un titre/auteur avec caracteres speciaux (accents, guillemets) **When** `metadata-kdp.json` est genere **Then** les caracteres sont correctement encodes en UTF-8
6. **Given** le dossier de sortie n'existe pas **When** l'export demarre **Then** le dossier est cree automatiquement (parents inclus)
7. **Given** un dossier de sortie existant avec des fichiers precedents **When** l'export est relance **Then** les fichiers sont ecrases proprement sans residus

## Tasks / Subtasks

- [x] Task 1: Ajouter les champs KDP au BookConfig (AC: #1, #4)
  - [x] 1.1 Ajouter `description: str | None = None` a BookConfig
  - [x] 1.2 Ajouter `mots_cles: list[str] | None = None` a BookConfig
  - [x] 1.3 Ajouter `categories: list[str] | None = None` a BookConfig
  - [x] 1.4 Mettre a jour les tests de config existants si necessaire
- [x] Task 2: Creer le module d'export metadonnees (AC: #1, #4, #5)
  - [x] 2.1 Creer `src/bookforge/export.py` avec fonction `export_metadata_kdp(config: BookConfig, output_dir: Path) -> Path`
  - [x] 2.2 Generer le JSON avec structure: `{"titre", "auteur", "sous_titre", "description", "mots_cles", "categories", "isbn", "genre"}`
  - [x] 2.3 Ecriture UTF-8 avec `json.dump(..., ensure_ascii=False, indent=2)`
  - [x] 2.4 Fichier nomme `metadata-kdp.json`
- [x] Task 3: Creer la fonction d'organisation du dossier de sortie (AC: #2, #3, #6, #7)
  - [x] 3.1 Creer `organize_output(config: BookConfig, build_dir: Path, output_dir: Path) -> Path` dans `export.py`
  - [x] 3.2 Creer `output_dir` si inexistant (`mkdir(parents=True, exist_ok=True)`)
  - [x] 3.3 Copier/renommer `livre-interieur.pdf` depuis le build dir
  - [x] 3.4 Copier/renommer `couverture.pdf` depuis le build dir
  - [x] 3.5 Generer `metadata-kdp.json` via `export_metadata_kdp()`
- [x] Task 4: Ajouter les tests (AC: #1-#7)
  - [x] 4.1 Creer `tests/test_export.py`
  - [x] 4.2 test_metadata_kdp_contains_all_fields — verifie tous les champs JSON
  - [x] 4.3 test_metadata_kdp_optional_fields_null — champs absents = null/[]
  - [x] 4.4 test_metadata_kdp_utf8_encoding — caracteres speciaux preserves
  - [x] 4.5 test_metadata_kdp_deterministic — memes entrees = meme sortie
  - [x] 4.6 test_organize_output_creates_directory — dossier cree si inexistant
  - [x] 4.7 test_organize_output_contains_expected_files — verifie les 3 fichiers
  - [x] 4.8 test_organize_output_overwrites_existing — ecrasement propre
  - [x] 4.9 test_metadata_kdp_json_valid — JSON parsable et bien forme
- [x] Task 5: Mettre a jour le fixture minimal book.yaml (AC: #1)
  - [x] 5.1 Ajouter des champs optionnels (description, mots_cles, categories) dans `tests/fixtures/books/full/book.yaml` si existant, sinon dans un nouveau fixture
- [x] Task 6: Passer linting et type-checking (tous AC)
  - [x] 6.1 `ruff check src/ tests/` et `ruff format --check src/ tests/`
  - [x] 6.2 `mypy src/`
  - [x] 6.3 `pytest` — tous les tests passent (112 existants + 11 nouveaux = 123)

## Dev Notes

### Architecture du module export

Creer un nouveau module `src/bookforge/export.py` — il n'existe pas encore. Ce module est **independant** des renderers. Il ne fait que lire le `BookConfig` et produire des fichiers de sortie.

**Justification du nouveau module** : L'export n'est ni un renderer (pas de Typst/Pandoc) ni de la qualite. C'est une phase distincte du pipeline (Phase 5 dans l'architecture). Creer `export.py` au meme niveau que `pipeline.py` est coherent avec l'architecture prevue.

### Signatures de fonctions

```python
# src/bookforge/export.py

def export_metadata_kdp(config: BookConfig, output_dir: Path) -> Path:
    """Exporte les metadonnees KDP en JSON pret a copier-coller."""

def organize_output(
    config: BookConfig,
    interior_pdf: Path,
    cover_pdf: Path,
    output_dir: Path,
) -> Path:
    """Organise le dossier de sortie final avec tous les livrables."""
```

### Structure du JSON metadata-kdp.json

```json
{
  "titre": "Mon Livre Business",
  "auteur": "JM",
  "sous_titre": "Un guide pratique",
  "description": "Description du livre pour la page KDP",
  "mots_cles": ["business", "guide", "productivite"],
  "categories": ["Business & Economie", "Management"],
  "isbn": null,
  "genre": "business"
}
```

- Utiliser `json.dump()` avec `ensure_ascii=False` pour preserver accents et caracteres speciaux
- `indent=2` pour lisibilite humaine (copier-coller facile)
- Les champs `None` deviennent `null` en JSON (comportement par defaut de json.dump)
- Les listes vides `[]` restent des listes vides

### Structure du dossier de sortie attendue

```
output/
├── livre-interieur.pdf    # Copie depuis build dir
├── couverture.pdf         # Copie depuis build dir
└── metadata-kdp.json      # Genere par export_metadata_kdp()
```

### Modification de BookConfig (schema.py)

`BookConfig` dans `src/bookforge/config/schema.py` (ligne 13) doit recevoir 3 nouveaux champs optionnels :

```python
class BookConfig(BaseModel):
    titre: str
    sous_titre: str | None = None
    auteur: str
    genre: str
    isbn: str | None = None
    dedicace: str | None = None
    description: str | None = None          # NEW — Description KDP
    mots_cles: list[str] | None = None      # NEW — Mots-cles KDP
    categories: list[str] | None = None     # NEW — Categories KDP
    chapitres: list[ChapterConfig]
```

**IMPORTANT** : Ces champs sont tous optionnels (`None` par defaut). Les 112 tests existants ne seront **pas casses** car ils ne fournissent pas ces champs. Pydantic v2 les met a `None` automatiquement.

### Pattern de copie de fichiers

Utiliser `shutil.copy2()` pour copier les PDF en preservant les metadonnees filesystem. Ne PAS utiliser `shutil.move()` — les fichiers source doivent rester dans le build dir pour le debug.

```python
import shutil
shutil.copy2(interior_pdf, output_dir / "livre-interieur.pdf")
shutil.copy2(cover_pdf, output_dir / "couverture.pdf")
```

### Imports necessaires (stdlib uniquement)

```python
import json
import logging
import shutil
from pathlib import Path
```

**ZERO nouvelle dependance externe** — tout est dans la stdlib Python. Pas besoin de toucher `pyproject.toml`.

### Integration pipeline (HORS SCOPE)

La Story 2.9 (CLI, logging et progression) integrera l'export dans le pipeline CLI. Pour cette story, les fonctions `export_metadata_kdp()` et `organize_output()` sont des fonctions independantes testables unitairement.

**NE PAS** modifier `pipeline.py` dans cette story — il est actuellement un placeholder.

### Project Structure Notes

- `export.py` au meme niveau que `pipeline.py` dans `src/bookforge/` — conforme a l'architecture
- Module dependencies: `export.py` depend de `config/schema.py` uniquement — respect du flux de dependances
- Pas de dependance vers `renderers/`, `parser/`, `quality/`, `judge/`

### Patterns etablis (Stories 2.3-2.7 — Respecter)

| Aspect | Pattern etabli | Appliquer dans export.py |
|--------|----------------|--------------------------|
| Logging | `logger = logging.getLogger("bookforge.<module>")` | `logger = logging.getLogger("bookforge.export")` |
| Paths | `pathlib.Path` partout, jamais `os.path` | Identique |
| Erreurs | Messages dev en anglais (logger), utilisateur en francais (exceptions) | Identique |
| Tests | `test_<quoi>_<condition>_<attendu>()` | Identique |
| Typing | `from __future__ import annotations` en premiere ligne | Identique |

### Anti-patterns a eviter

1. **NE PAS** integrer dans `pipeline.py` ou `cli.py` — Story 2.9
2. **NE PAS** generer de thumbnail JPEG — Story 5.2
3. **NE PAS** generer la couverture complete (dos + 4e) — Stories 5.1-5.2
4. **NE PAS** ajouter de QA report JSON — Story ulterieure (qa-report.json)
5. **NE PAS** ajouter d'EPUB dans le dossier de sortie — Story 3.1
6. **NE PAS** utiliser `os.path` — `pathlib.Path` uniquement
7. **NE PAS** modifier le fixture `tests/fixtures/books/minimal/book.yaml` — Les tests existants l'utilisent. Creer un nouveau fixture si besoin.
8. **NE PAS** valider le contenu des champs description/mots_cles/categories au-dela de Pydantic — Pas de validation metier pour MVP0
9. **NE PAS** ajouter de dependance externe — Tout est stdlib

### Previous Story Intelligence (Story 2.7)

- **112 tests** existants, tous passent — ne pas les casser
- Pattern inline template Typst avec `escape_typst()` — pas applicable ici (pas de Typst)
- `render_cover()` cree le dossier avec `mkdir(parents=True, exist_ok=True)` — reutiliser ce pattern
- Fichier de sortie couverture: `couverture.pdf` dans `output_dir` — coherent avec l'AC #2
- `run_external()` pour subprocess — pas necessaire ici (pas de commande externe)

### Git Intelligence (Commits recents)

- Commits suivent le pattern: `feat(bookforge): implement Story X.Y — description`
- Production code: ~876 lignes, tests: ~1660 lignes
- Convention francaise pour les noms de variables et fichiers YAML
- `from __future__ import annotations` en tete de chaque module

### Scope MVP0 vs MVP1+

| Aspect | MVP0 (cette story) | MVP1+ (hors scope) |
|--------|---------------------|---------------------|
| Metadonnees | titre, auteur, description, mots-cles, categories | + prix, date publication, editeur |
| Format metadata | JSON simple | + XML ONIX |
| Fichiers output | PDF interieur + couverture + JSON | + EPUB + thumbnail + QA report |
| Integration | Fonctions standalone | Integre dans CLI pipeline |
| Validation | Pydantic basique | Validation metier KDP (longueur description, nb mots-cles) |

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-2.8] — AC Given/When/Then
- [Source: _bmad-output/planning-artifacts/architecture.md#output-folder] — Structure output/ attendue
- [Source: _bmad-output/planning-artifacts/prd.md#FR19] — Export metadonnees KDP (description, mots-cles, categories)
- [Source: _bmad-output/planning-artifacts/architecture.md#Phase-5] — Phase Export final du pipeline
- [Source: _bmad-output/planning-artifacts/architecture.md#module-dependencies] — export depend uniquement de config/
- [Source: src/bookforge/config/schema.py] — BookConfig actuel (sans champs KDP)
- [Source: src/bookforge/renderers/cover.py] — Pattern mkdir + fichier de sortie
- [Source: _bmad-output/implementation-artifacts/2-7-couverture-template-statique.md] — Patterns etablis

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

- ruff E501 fixed in test_export.py (line too long on expected_keys set)
- 3 pre-existing files flagged by ruff format (validator.py, transform.py, test_errors.py) — not touched, out of scope

### Completion Notes List

- 3 champs optionnels ajoutes a BookConfig (description, mots_cles, categories) — zero regression sur 112 tests existants
- Module export.py cree avec export_metadata_kdp() et organize_output() — stdlib uniquement (json, shutil, pathlib)
- metadata-kdp.json genere en UTF-8 avec ensure_ascii=False et indent=2
- organize_output() copie PDFs via shutil.copy2() et genere metadata dans un seul appel
- 11 nouveaux tests dans test_export.py (7 metadata + 4 organize_output)
- Fixture full/book.yaml cree avec tous les champs KDP
- 123/123 tests passent, ruff clean, mypy clean

### File List

- src/bookforge/config/schema.py — Modified (3 nouveaux champs optionnels)
- src/bookforge/export.py — Created (module export metadonnees + organisation sortie)
- tests/test_export.py — Created (11 tests)
- tests/fixtures/books/full/book.yaml — Created (fixture complet avec champs KDP)
- tests/fixtures/books/full/chapitres/01-introduction.md — Created (chapitre pour fixture)
