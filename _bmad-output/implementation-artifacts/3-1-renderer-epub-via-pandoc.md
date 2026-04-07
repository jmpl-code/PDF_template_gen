# Story 3.1 : Renderer EPUB via Pandoc

Status: review

## Story

As a auteur,
I want que mon manuscrit soit exporté en EPUB conforme EPUB 3.x compatible Kindle,
So that je peux publier sur le Kindle Store.

## Acceptance Criteria

1. **Given** un `BookNode` (AST) valide et un `BookConfig` **When** le renderer EPUB transforme l'AST et appelle `pandoc` via `run_external()` **Then** un fichier EPUB valide est produit
2. **And** les métadonnées complètes sont présentes dans l'EPUB (titre, auteur, langue `fr`, description, mots-clés)
3. **And** tous les éléments (texte, headings, images, tableaux) sont lisibles dans l'EPUB
4. **And** les tableaux de plus de 4 colonnes sont convertis en image fallback (via Matplotlib, déjà en dépendance)
5. **And** les polices sont embarquées dans l'EPUB (FR34) — ou à minima, un CSS Kindle basique est appliqué
6. **And** si Pandoc n'est pas installé, une `RenderError` claire est levée (via `run_external()`)

## Tasks / Subtasks

- [x] Task 1 — Implémenter `render_epub()` dans `src/bookforge/renderers/epub.py` (AC: #1, #2, #3, #6)
  - [x] 1.1 Créer `render_epub(book: BookNode, output_dir: Path, config: BookConfig | None = None) -> Path` — signature miroir de `render_pdf()`
  - [x] 1.2 Convertir l'AST BookNode en Markdown intermédiaire (headings, paragraphes, images, tableaux) — le Markdown est le format d'entrée natif de Pandoc
  - [x] 1.3 Générer un fichier de métadonnées YAML Pandoc (`metadata.yaml`) avec titre, auteur, lang, description, droits (copyright)
  - [x] 1.4 Appeler `run_external(["pandoc", input_md, "--metadata-file", metadata_yaml, "-o", output_epub, "--epub-chapter-level=1", ...])` pour produire l'EPUB
  - [x] 1.5 Retourner le chemin du fichier EPUB produit
- [x] Task 2 — Gérer le fallback image pour tableaux larges (AC: #4)
  - [x] 2.1 Lors de la conversion AST → Markdown, détecter les `TableNode` avec `len(headers) > 4`
  - [x] 2.2 Pour ces tableaux, générer une image PNG via Matplotlib (`table()`) à 300 DPI
  - [x] 2.3 Insérer une référence image Markdown à la place du tableau dans le fichier intermédiaire
  - [x] 2.4 Pour les tableaux ≤ 4 colonnes, générer du Markdown standard (pipe table)
- [x] Task 3 — CSS Kindle basique (AC: #5)
  - [x] 3.1 Créer un fichier CSS inline ou embarqué passé à Pandoc via `--css=epub.css`
  - [x] 3.2 Le CSS doit inclure : font-family (serif), line-height, margin des paragraphes, taille des headings
  - [x] 3.3 Pas d'embarquement de polices en MVP0.5 — le CSS Kindle standard suffit (les liseuses utilisent leurs propres polices)
- [x] Task 4 — Tests (AC: #1-6)
  - [x] 4.1 `test_renderer_epub.py` — test unitaire : AST minimal → Markdown intermédiaire correct
  - [x] 4.2 `test_renderer_epub.py` — test unitaire : métadonnées YAML générées correctement depuis BookConfig
  - [x] 4.3 `test_renderer_epub.py` — test unitaire : tableau > 4 colonnes → image fallback (mock Matplotlib)
  - [x] 4.4 `test_renderer_epub.py` — test unitaire : tableau ≤ 4 colonnes → Markdown pipe table
  - [x] 4.5 `test_renderer_epub.py` — test intégration : `render_epub()` appelle `run_external()` avec les bons arguments (mock `run_external`)
  - [x] 4.6 `test_renderer_epub.py` — test erreur : Pandoc introuvable → `RenderError`
  - [x] 4.7 Vérifier zéro régression — 152/152 tests passent (137 existants + 15 nouveaux)

## Dev Notes

### Architecture et pattern à suivre

Le renderer EPUB suit **exactement le même pattern** que le renderer PDF (`src/bookforge/renderers/pdf.py`) :
1. **Conversion AST → format intermédiaire** : BookNode → fichier Markdown (au lieu de .typ pour le PDF)
2. **Appel externe** : `pandoc` via `run_external()` (au lieu de `typst compile`)
3. **Retour du chemin** : Path vers le fichier .epub produit

Décision d'architecture n°3 : "Interface Python → Pandoc = Subprocess direct (`pandoc` CLI), même pattern que Typst."

### Fichiers existants à connaître

| Fichier | État actuel | Action story 3.1 |
|---------|-------------|-------------------|
| `src/bookforge/renderers/epub.py` | Stub (1 ligne docstring) | **Implémenter** — renderer complet |
| `src/bookforge/passes/epub_transform.py` | Stub (1 ligne docstring) | **NE PAS utiliser pour MVP0.5** — la transformation peut vivre dans epub.py directement. La passe séparée sera utile quand les design tokens interviendront (Epic 4) |
| `src/bookforge/external.py` | Complet (`run_external()`) | **Appeler** — ne pas modifier |
| `src/bookforge/renderers/pdf.py` | Complet | **Pattern de référence** — copier la structure |
| `src/bookforge/ast_nodes/` | Complet (BookNode, ChapterNode, HeadingNode, ParagraphNode, ImageNode, TableNode) | **Lire** — connaître les types AST |
| `src/bookforge/config/schema.py` | Complet (BookConfig Pydantic v2) | **Lire** — champs métadonnées (titre, auteur, description, mots_cles, isbn) |
| `src/bookforge/errors.py` | Complet (RenderError avec exit_code=2) | **Utiliser** — lever RenderError si erreur |
| `src/bookforge/pipeline.py` | Complet (3 phases) | **NE PAS modifier** — l'intégration pipeline est Story 3.2 |
| `src/bookforge/export.py` | Complet (organize_output) | **NE PAS modifier** — l'intégration export est Story 3.2 |

### Conversion AST → Markdown pour Pandoc

Le BookNode a cette structure :
```
BookNode(title, chapters: tuple[ChapterNode, ...])
  ChapterNode(title, children: tuple[ASTNode, ...])
    HeadingNode(level, text)
    ParagraphNode(text)
    ImageNode(src: Path, alt: str)  # src = chemin absolu résolu
    TableNode(headers: tuple[str, ...], rows: tuple[tuple[str, ...], ...])
```

La conversion vers Markdown :
- `ChapterNode` → `# {title}\n\n` (heading niveau 1)
- `HeadingNode` → `{"#" * level} {text}\n\n`
- `ParagraphNode` → `{text}\n\n`
- `ImageNode` → `![{alt}]({src})\n\n` (chemin absolu, Pandoc le résoudra)
- `TableNode` (≤ 4 cols) → pipe table Markdown standard
- `TableNode` (> 4 cols) → image PNG générée via Matplotlib, puis `![Table]({image_path})\n\n`

### Appel Pandoc — commande cible

```bash
pandoc input.md \
  --metadata-file=metadata.yaml \
  --css=epub.css \
  -o livre.epub \
  --epub-chapter-level=1 \
  --toc \
  --toc-depth=2
```

Le fichier `metadata.yaml` pour Pandoc :
```yaml
title: "Titre du livre"
author: "Nom Auteur"
lang: fr
description: "Description du livre"
rights: "© 2026 Nom Auteur"
```

### Fallback image pour tableaux larges

Utiliser `matplotlib.pyplot.table()` pour générer un PNG du tableau :
```python
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
ax.axis("off")
table = ax.table(
    cellText=rows,
    colLabels=headers,
    cellLoc="center",
    loc="center",
)
table.auto_set_font_size(True)
fig.savefig(output_path, dpi=300, bbox_inches="tight", pad_inches=0.1)
plt.close(fig)
```

Matplotlib est déjà une dépendance du projet (`matplotlib>=3.10.8` dans pyproject.toml). Ne pas ajouter de dépendance supplémentaire.

### CSS Kindle basique

```css
/* epub.css — style Kindle basique */
body {
  font-family: serif;
  line-height: 1.4;
}
h1 { font-size: 1.8em; margin-top: 2em; margin-bottom: 0.8em; }
h2 { font-size: 1.4em; margin-top: 1.5em; margin-bottom: 0.6em; }
h3 { font-size: 1.2em; margin-top: 1.2em; margin-bottom: 0.5em; }
p { text-indent: 1em; margin: 0.2em 0; }
img { max-width: 100%; height: auto; }
table { border-collapse: collapse; width: 100%; }
td, th { border: 1px solid #ccc; padding: 0.3em 0.5em; }
```

Le CSS est écrit en fichier temporaire à côté du Markdown intermédiaire, passé à Pandoc via `--css`.

### Gestion des fichiers temporaires

Écrire les fichiers intermédiaires dans `output_dir` (même approche que `render_pdf()` qui écrit le .typ dans `book_root`) :
- `output_dir / "_epub_build" / "content.md"` — Markdown intermédiaire
- `output_dir / "_epub_build" / "metadata.yaml"` — métadonnées Pandoc
- `output_dir / "_epub_build" / "epub.css"` — CSS Kindle
- `output_dir / "_epub_build" / "table_*.png"` — images fallback tableaux
- `output_dir / "livre.epub"` — fichier EPUB final

Le sous-dossier `_epub_build/` isole les artéfacts intermédiaires.

### Anti-patterns à éviter

1. **NE PAS** utiliser `pypandoc` ou tout wrapper Python — subprocess direct via `run_external()` (décision architecture n°3)
2. **NE PAS** modifier `pipeline.py` ni `export.py` — l'intégration pipeline est Story 3.2
3. **NE PAS** modifier `external.py` — il est déjà complet
4. **NE PAS** créer de classe EpubRenderer — une simple fonction `render_epub()` suffit (cohérence avec `render_pdf()`)
5. **NE PAS** embarquer de polices .ttf/.otf dans l'EPUB en MVP0.5 — le CSS Kindle standard suffit
6. **NE PAS** implémenter de passe de transformation dans `passes/epub_transform.py` — garder la logique dans epub.py pour MVP0.5, la passe sera utile quand les design tokens interviendront
7. **NE PAS** utiliser `os.path` — `pathlib.Path` uniquement
8. **NE PAS** ajouter de dépendances — Pandoc est un binaire externe, Matplotlib est déjà en dépendance
9. **NE PAS** appeler `epubcheck` dans cette story — la validation EPUB est hors scope MVP0.5 (prévue Epic 7)
10. **NE PAS** modifier les fixtures de test existantes

### Standards EPUB à respecter (de l'architecture)

- EPUB 3.3 ciblé (Pandoc produit du EPUB 3 par défaut)
- Métadonnées accessibilité souhaitables mais non bloquantes pour MVP0.5
- Les images doivent être référencées correctement (chemins absolus OK — Pandoc les copie dans l'EPUB)

### Previous Story Intelligence (Story 2.9)

- **136 tests** passent — zéro régression attendue
- Pattern `from __future__ import annotations` en première ligne de chaque module
- Logger par module : `logging.getLogger("bookforge.renderers.epub")`
- Logging interne en **anglais** (debug/info/warning)
- `mkdir(parents=True, exist_ok=True)` pour créer les dossiers
- Commit pattern : `feat(bookforge): implement Story X.Y — description`
- ruff + mypy stricts — corriger avant commit
- Convention de test : `test_<quoi>_<condition>_<attendu>()`
- Mock pattern : mocker `run_external` dans les tests renderer, pas les vrais appels subprocess

### Project Structure Notes

- `epub.py` existe déjà comme stub dans `src/bookforge/renderers/` — le remplir
- `test_renderer_epub.py` à créer dans `tests/` (miroir de `test_renderer_pdf.py`)
- Pas de nouveau module, pas de nouvelle dépendance, pas de modification de module existant
- Le seul fichier modifié est `src/bookforge/renderers/epub.py`
- Le seul fichier créé est `tests/test_renderer_epub.py`

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 3.1] — User story et acceptance criteria
- [Source: _bmad-output/planning-artifacts/architecture.md#Décision 3] — Interface Python → Pandoc = subprocess direct
- [Source: _bmad-output/planning-artifacts/architecture.md#EPUB 3.3] — Standards EPUB, accessibilité
- [Source: _bmad-output/planning-artifacts/architecture.md#Cross-Cutting Concerns §3] — Passes de transformation par format
- [Source: _bmad-output/planning-artifacts/prd.md#FR16] — EPUB conforme EPUB 3.x, métadonnées complètes, compatible Kindle
- [Source: _bmad-output/planning-artifacts/prd.md#FR17] — Tous les éléments lisibles dans l'EPUB
- [Source: _bmad-output/planning-artifacts/prd.md#FR34] — Polices embarquées
- [Source: _bmad-output/planning-artifacts/prd.md#NFR4] — Export EPUB < 2 minutes pour 200 pages
- [Source: _bmad-output/implementation-artifacts/2-9-cli-logging-et-progression.md] — Previous story patterns et intelligence

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

- ruff F401 fixed in epub.py (unused ChapterNode import)
- ruff F401 fixed in test_renderer_epub.py (unused _KINDLE_CSS import)
- ruff E501 fixed in test_renderer_epub.py (line too long for mock assertion)
- Test fix: run_external description passed as keyword arg, not positional

### Completion Notes List

- `render_epub()` implémenté avec même pattern que `render_pdf()`: AST → Markdown intermédiaire → subprocess Pandoc → EPUB
- Conversion AST → Markdown: ChapterNode → `#`, HeadingNode → `##`+, ParagraphNode → texte, ImageNode → `![alt](src)`, TableNode → pipe table ou image fallback
- Fallback image pour tableaux > 4 colonnes via Matplotlib `table()` à 300 DPI
- Métadonnées Pandoc YAML: titre, auteur, lang=fr, rights (copyright), description, mots-clés, ISBN
- CSS Kindle basique: serif, line-height 1.4, headings h1-h4, img max-width 100%, table styling
- Artéfacts intermédiaires isolés dans `_epub_build/` (content.md, metadata.yaml, epub.css, table_*.png)
- Appel Pandoc: `pandoc content.md --metadata-file --css --epub-chapter-level=1 --toc --toc-depth=2 -o livre.epub`
- 15 nouveaux tests, 152/152 total passent, zéro régression
- ruff clean, mypy clean

### Change Log

- 2026-04-07: Story 3.1 implemented — EPUB renderer via Pandoc

### File List

- **src/bookforge/renderers/epub.py** — Modified (stub → renderer complet)
- **tests/test_renderer_epub.py** — Created (15 tests: 3 AST→MD, 3 metadata, 1 wide table, 2 small table, 5 integration, 1 error)
