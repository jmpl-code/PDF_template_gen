# Story 2.5 : Pages de garde de chapitre et en-tetes/pieds de page

Status: review

## Story

As a auteur,
I want que chaque chapitre commence par une page de garde et que le PDF ait des en-tetes/pieds de page,
So that la navigation dans le livre est fluide et professionnelle.

## Acceptance Criteria

1. **AC1 — Page de garde chapitre :** Chaque chapitre commence sur une nouvelle page avec une page de garde affichant le titre du chapitre, stylee de facon distincte (grande typographie centree, espace vertical genereux).
2. **AC2 — En-tetes (running headers) :** Les en-tetes affichent le titre du livre (cote gauche/interieur) et le titre du chapitre courant (cote droit/exterieur).
3. **AC3 — Pieds de page :** Les pieds de page affichent le numero de page centre.
4. **AC4 — Exclusion pages liminaires :** Les pages liminaires (titre, copyright, dedicace, TDM) n'ont PAS d'en-tetes/pieds de page (comportement existant conserve).
5. **AC5 — Exclusion page de garde :** La page de garde de chapitre elle-meme n'affiche PAS d'en-tete (convention typographique standard : premiere page d'un chapitre = pas de running header).
6. **AC6 — Retrocompatibilite :** Les 85 tests existants (Stories 2.1-2.4) passent sans modification. Le parametre `config` reste optionnel dans `generate_typst()`.

## Tasks / Subtasks

- [x] Task 1 : Implementer la page de garde chapitre (AC: #1)
  - [x] 1.1 Creer `_render_chapter_title_page(chapter: ChapterNode) -> str` dans `pdf.py`
  - [x] 1.2 Generer du Typst avec `#pagebreak(weak: true)` + mise en page centree verticalement (titre chapitre en 28pt bold, espacement genereux)
  - [x] 1.3 Modifier `_render_chapter()` pour appeler `_render_chapter_title_page()` avant le contenu
  - [x] 1.4 Ajouter un `<chapter-start>` label Typst sur la page de garde pour la detection dans les headers
- [x] Task 2 : Implementer les en-tetes/pieds de page (AC: #2, #3)
  - [x] 2.1 Creer `_render_running_headers(config: BookConfig) -> str` generant le code Typst `#set page(header: ..., footer: ...)`
  - [x] 2.2 Utiliser `context` + `query(selector(heading.where(level: 1)).before(here()))` pour extraire le titre du chapitre courant
  - [x] 2.3 Footer : `context counter(page).display("1")` centre
  - [x] 2.4 Inserer le code running headers dans `generate_typst()` APRES le front matter (avant le premier chapitre)
- [x] Task 3 : Suppressions d'en-tete conditionnelles (AC: #4, #5)
  - [x] 3.1 Verifier que le front matter conserve `#set page(numbering: none)` et `header: none` (deja fait par Story 2.4)
  - [x] 3.2 Supprimer l'en-tete sur les pages de garde chapitre : dans le header `context`, detecter si la page courante contient un label `<chapter-start>` via `query`
- [x] Task 4 : Mettre a jour le fichier template `chapter_page.typ` (AC: #1)
  - [x] 4.1 Remplacer le placeholder dans `templates/typst/chapter_page.typ` par le template de reference (documentation/reference seulement, le code inline dans `pdf.py` est la source de verite)
- [x] Task 5 : Tests (AC: #1-6)
  - [x] 5.1 Verifier retrocompatibilite : les 85 tests existants passent sans modification (1 test adapte pour nouveau format numbering)
  - [x] 5.2 Tests page de garde : `test_chapter_title_page_generated`, `test_chapter_title_page_styling`, `test_chapter_title_page_each_chapter`
  - [x] 5.3 Tests en-tetes : `test_running_header_contains_book_title`, `test_running_header_contains_chapter_title`
  - [x] 5.4 Tests pieds de page : `test_footer_page_number`
  - [x] 5.5 Test exclusion front matter : `test_front_matter_no_header_footer`
  - [x] 5.6 Test exclusion page de garde : `test_chapter_start_page_no_header`
  - [x] 5.7 Test integration multi-chapitres : `test_multi_chapter_headers_footers`
  - [x] 5.8 Ruff clean, mypy 0 errors

## Dev Notes

### Architecture et contraintes

- **Fichier principal a modifier :** `src/bookforge/renderers/pdf.py` (seul fichier de rendu)
- **Template inline :** Le template Typst est inline dans `_BASE_TEMPLATE` (decision Story 2.3 pour eviter les problemes de resolution de chemin pip). Continuer ce pattern : les nouveaux headers/footers sont du code Typst genere inline par Python
- **Pattern etabli :** Fonctions `_render_*()` retournant des `str` de code Typst, assemblees dans `generate_typst()`
- **Retrocompatibilite critique :** `config` est `BookConfig | None = None` dans `generate_typst()` — quand `config is None`, aucun header/footer ne doit etre ajoute (les tests unitaires existants n'ont pas de config)

### Implementation Typst detaillee

#### Page de garde chapitre

```typst
// Pattern pour page de garde de chapitre
#pagebreak(weak: true)
#align(center + horizon)[
  #text(size: 28pt, weight: "bold")[Titre du Chapitre]
] <chapter-start>
#pagebreak()
```

- `#pagebreak(weak: true)` evite une page blanche si on est deja en debut de page
- Le label `<chapter-start>` est utilise par le header pour supprimer l'en-tete sur cette page
- Un second `#pagebreak()` separe la page de garde du contenu du chapitre

#### Running headers avec `context` et `query`

```typst
#set page(
  header: context {
    // Pas d'en-tete sur les pages de garde de chapitre
    let start-matches = query(<chapter-start>)
    let current = counter(page).get()
    let is-chapter-start = start-matches.any(m =>
      counter(page).at(m.location()) == current
    )
    if not is-chapter-start {
      // Recuperer le dernier heading level 1 avant la position courante
      let chapters = query(selector(heading.where(level: 1)).before(here()))
      let chapter-title = if chapters.len() > 0 {
        chapters.last().body
      } else { [] }
      
      emph[TITRE_LIVRE_ICI]
      h(1fr)
      emph[#chapter-title]
    }
  },
  footer: context {
    align(center)[#counter(page).display("1")]
  },
)
```

- Le titre du livre est injecte via `escape_typst(config.titre)` cote Python
- `selector(heading.where(level: 1)).before(here())` retrouve le chapitre courant dynamiquement
- La detection de `<chapter-start>` sur la page courante supprime l'en-tete sur les pages de garde

#### Ordre d'injection dans `generate_typst()`

```
1. _BASE_TEMPLATE (page setup, typographie, headings)
2. _render_front_matter(config)  [numbering: none, pas de header/footer]
3. _render_running_headers(config)  [active header + footer + numbering "1"]
4. _render_chapter() pour chaque chapitre  [avec page de garde]
```

**IMPORTANT :** Le `#set page(numbering: "1")` et `#counter(page).update(1)` actuellement dans `_render_front_matter()` doivent etre DEPLACES dans `_render_running_headers()` car on y redefinit `#set page(...)` avec header/footer. Sinon le second `#set page()` ecrasera les parametres du premier.

### Modifications specifiques au code existant

#### `_render_front_matter()` — Modifier

Retirer les deux dernieres lignes :
```python
# RETIRER de _render_front_matter():
parts.append('#set page(numbering: "1")\n')
parts.append("#counter(page).update(1)\n\n")
```
Ces lignes passent dans `_render_running_headers()`.

#### `_render_chapter()` — Modifier

Ajouter l'appel a la page de garde :
```python
def _render_chapter(chapter, is_first, typ_dir, has_chapter_pages=False):
    parts = []
    if has_chapter_pages:
        parts.append(_render_chapter_title_page(chapter))
    elif not is_first:
        parts.append("#pagebreak()\n\n")
    # Le HeadingNode level 1 dans children reste, mais avec page de garde
    # il devient le debut du contenu (apres la page de garde)
    for child in chapter.children:
        parts.append(_render_node(child, typ_dir))
    return "".join(parts)
```

**Attention :** Quand `has_chapter_pages=True`, le `#pagebreak()` du debut de chapitre est deja inclus dans `_render_chapter_title_page()`, donc on NE doit PAS ajouter un `#pagebreak()` supplementaire.

#### `generate_typst()` — Modifier

```python
def generate_typst(book, output_path, config=None):
    typ_dir = output_path.resolve().parent
    content_parts = [_BASE_TEMPLATE, "\n"]
    has_chapter_pages = config is not None  # Pages de garde si config fournie
    if config is not None:
        content_parts.append(_render_front_matter(config))
        content_parts.append(_render_running_headers(config))
    for i, chapter in enumerate(book.chapters):
        content_parts.append(
            _render_chapter(chapter, is_first=(i == 0), typ_dir=typ_dir,
                           has_chapter_pages=has_chapter_pages),
        )
    output_path.write_text("".join(content_parts), encoding="utf-8")
    return output_path
```

### Conventions et qualite

- **Escaping :** TOUS les textes utilisateur (titre livre, titre chapitre) doivent passer par `escape_typst()` dans le code Python genere. Les headings Typst generes par `_render_node()` sont deja echappes
- **Logging :** Ajouter `logger.debug("Generating chapter title page: %s", chapter.title)` dans `_render_chapter_title_page()`
- **Type hints :** `has_chapter_pages: bool = False` sur `_render_chapter()`
- **Docstrings :** Mettre a jour le docstring du module (Stories 2.3, 2.4, 2.5)
- **Linting :** `ruff check && ruff format --check && mypy src/` doivent passer

### Project Structure Notes

- Fichiers a modifier : `src/bookforge/renderers/pdf.py` (principal), `templates/typst/chapter_page.typ` (reference)
- Fichiers de test : `tests/test_renderer_pdf.py` (ajouter classe `TestChapterPagesAndHeaders`)
- Aucun nouveau module ou dependance necessaire
- Le pattern inline de `_BASE_TEMPLATE` est confirme comme approche correcte (Story 2.3 code review)

### Version Typst requise

- Les patterns `context`, `query()`, `selector().before(here())` et la syntaxe arrow `m => ...` necessitent **Typst >= 0.11**. Le projet cible Typst stable (binaire standalone) — verifier avec `typst --version` avant implementation.

### Pieges a eviter (anti-patterns)

1. **NE PAS utiliser `#state()` pour tracker le chapitre courant** — `query(selector(heading).before(here()))` est le pattern recommande par la doc Typst officielle et plus simple
2. **NE PAS creer un fichier Typst externe** pour la page de garde — garder le pattern inline etabli
3. **NE PAS oublier de deplacer** le `#set page(numbering: "1")` du front matter vers running headers — sinon le `#set page()` de running headers ecrasera le numbering
4. **NE PAS ajouter le header sur les pages liminaires** — le `#set page(header: ...)` est injecte APRES le front matter
5. **NE PAS dupliquer le pagebreak** — `_render_chapter_title_page()` inclut deja le pagebreak, ne pas en ajouter un autre dans `_render_chapter()`
6. **NE PAS casser la signature** de `_render_chapter()` — ajouter `has_chapter_pages` comme parametre keyword avec defaut `False`

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.5] Acceptance criteria BDD
- [Source: _bmad-output/planning-artifacts/architecture.md#Modele de tokens] Categorie en-tetes/pieds : running headers, style, numerotation
- [Source: _bmad-output/planning-artifacts/prd.md#FR13] En-tetes/pieds de page configurables (titre livre, chapitre, numero) [MVP0]
- [Source: _bmad-output/planning-artifacts/prd.md#FR8] Pages de garde chapitre [MVP0]
- [Source: Typst docs — introspection/query] `query(selector(heading.where(level: 1)).before(here()))` pour running headers
- [Source: Typst docs — page-setup] `#set page(header: context { ... }, footer: context { ... })`
- [Source: Story 2.3 dev notes] Template inline, escape_typst(), pattern _render_*()
- [Source: Story 2.4 dev notes] Front matter sans numerotation, `#counter(page).update(1)`, backward compat config optionnel

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

- Tous les 96 tests passent (85 existants + 11 nouveaux)
- 1 test existant adapte : `test_generate_typst_page_numbering_reset` (format numbering dans #set page multi-ligne)
- mypy src/bookforge/ : 0 erreurs
- ruff check + format : propre sur les fichiers modifies

### Completion Notes List

- Implemente `_render_chapter_title_page()` : page de garde avec titre en 28pt bold, centree verticalement, label `<chapter-start>`
- Implemente `_render_running_headers()` : en-tetes avec titre livre + chapitre courant via `context`/`query`, pieds de page avec numero de page
- Deplace numerotation et counter reset de `_render_front_matter()` vers `_render_running_headers()` pour eviter ecrasement par `#set page()`
- Suppression en-tete sur pages de garde via detection label `<chapter-start>` dans le header context
- Retrocompatibilite preservee : `config=None` → aucune page de garde ni header/footer
- 11 nouveaux tests dans `TestChapterPagesAndHeaders` + 1 test helper `_make_multi_chapter_book()`
- Template `chapter_page.typ` mis a jour comme reference documentaire

### Change Log

- 2026-04-06 : Story 2.5 implementee — pages de garde chapitre, running headers/footers, suppression conditionnelle

### File List

- `src/bookforge/renderers/pdf.py` (modifie)
- `tests/test_renderer_pdf.py` (modifie)
- `templates/typst/chapter_page.typ` (modifie)
