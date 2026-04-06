# Story 2.4 : Table des matieres et pages liminaires

Status: done

## Story

As a auteur,
I want que le PDF contienne une TDM cliquable et des pages liminaires (titre, copyright),
So that mon livre a une structure professionnelle.

## Criteres d'acceptation

1. **Given** un AST avec plusieurs chapitres et headings, **When** le renderer produit le PDF, **Then** une table des matieres est generee automatiquement depuis les headings avec numeros de page
2. **And** les pages liminaires (page de titre, page de copyright) sont inserees avant le contenu
3. **And** une page de dedicace optionnelle est ajoutee si configuree dans `book.yaml` (champ `dedicace`)
4. **And** les pages liminaires apparaissent dans l'ordre : page de titre, page de copyright, dedicace (si presente), TDM
5. **And** la TDM est cliquable (liens hypertexte vers les headings) avec numeros de page
6. **And** le contenu des chapitres commence apres la TDM

## Taches / Sous-taches

- [x] Tache 1 : Modifier la signature de `render_pdf()` et `generate_typst()` pour accepter `BookConfig` (AC: #1, #2, #3)
  - [x] 1.1 Ajouter le parametre `config: BookConfig | None = None` a `generate_typst()` et `render_pdf()`
  - [x] 1.2 Mettre a jour `renderers/__init__.py` pour exporter la nouvelle signature (inchange, re-export transparent)
  - [x] 1.3 Les 24 tests existants passent sans modification (parametre optionnel)

- [x] Tache 2 : Generer la page de titre en Typst (AC: #2)
  - [x] 2.1 Fonction `_render_title_page(config: BookConfig) -> str` dans `pdf.py`
  - [x] 2.2 Contenu : titre centre 28pt bold, sous-titre 18pt (si present), auteur 16pt en bas
  - [x] 2.3 Page dediee sans numero de page (`#set page(numbering: none)`)

- [x] Tache 3 : Generer la page de copyright en Typst (AC: #2)
  - [x] 3.1 Fonction `_render_copyright_page(config: BookConfig) -> str` dans `pdf.py`
  - [x] 3.2 Contenu : "(c) [annee] [auteur]. Tous droits reserves.", ISBN si present
  - [x] 3.3 Texte aligne en bas de page, taille 9pt

- [x] Tache 4 : Generer la page de dedicace optionnelle (AC: #3)
  - [x] 4.1 Fonction `_render_dedication_page(dedicace: str) -> str` dans `pdf.py`
  - [x] 4.2 Texte en italique (#emph), centre verticalement et horizontalement (#align(center + horizon))
  - [x] 4.3 Conditionnel dans `_render_front_matter()` : genere seulement si `config.dedicace` est non-None

- [x] Tache 5 : Generer la TDM cliquable (AC: #1, #5)
  - [x] 5.1 Utilise `#outline(indent: auto)` de Typst pour la TDM automatique (liens cliquables natifs)
  - [x] 5.2 Titre "Table des matieres" via `#heading(outlined: false, level: 1)` (non inclus dans sa propre TDM)
  - [x] 5.3 Pagebreak apres la TDM pour separer du contenu

- [x] Tache 6 : Assembler les pages liminaires dans `generate_typst()` (AC: #4, #6)
  - [x] 6.1 Ordre : preamble -> `#set page(numbering: none)` -> titre -> copyright -> dedicace -> TDM -> `#set page(numbering: "1")` + reset -> contenu
  - [x] 6.2 Numerotation desactivee pour les liminaires
  - [x] 6.3 Numerotation arabe reactivee + `#counter(page).update(1)` avant le contenu

- [x] Tache 7 : Ecrire les tests (AC: #1-#6)
  - [x] 7.1 `test_generate_typst_includes_title_page()` — titre et auteur presents dans le .typ
  - [x] 7.2 `test_generate_typst_includes_copyright_page()` — mention copyright presente
  - [x] 7.3 `test_generate_typst_includes_dedication_when_configured()` — dedicace presente si configuree
  - [x] 7.4 `test_generate_typst_no_dedication_when_not_configured()` — pas de dedicace si non configuree
  - [x] 7.5 `test_generate_typst_includes_outline()` — `#outline` present dans le .typ
  - [x] 7.6 `test_generate_typst_front_matter_order()` — titre avant copyright avant TDM avant contenu
  - [x] 7.7 `test_generate_typst_page_numbering_reset()` — `counter(page).update(1)` present avant contenu
  - [x] 7.8 Golden file `minimal.typ` inchange (tests sans config ne generent pas de front matter)
  - [x] 7.9 `test_render_pdf_with_config_produces_pdf()` — integration avec BookConfig
  - [x] 7.10 Tests supplementaires : sous-titre absent, ISBN absent, echappement du contenu config, retro-compatibilite sans config

## Dev Notes

### Contexte technique

**Typst `#outline()`** : genere automatiquement une TDM depuis tous les headings du document. Les liens sont cliquables nativement. Options :
- `indent: auto` — indentation automatique selon le niveau de heading
- `depth: 2` — limiter aux niveaux 1 et 2 (optionnel)
- Les entrees sont des blocs avec fill dots et numeros de page

**Numerotation de page Typst** :
```typst
// Pas de numero sur les liminaires
#set page(numbering: none)

// ... pages liminaires ...

// Numerotation arabe pour le corps
#set page(numbering: "1")
#counter(page).update(1)
```

**Signature actuelle** : `render_pdf(book: BookNode, output_dir: Path) -> Path`
**Nouvelle signature** : `render_pdf(book: BookNode, config: BookConfig, output_dir: Path) -> Path`

Le `BookConfig` (Pydantic model) contient deja tous les champs necessaires :
- `titre: str` — pour la page de titre
- `sous_titre: str | None` — sous-titre optionnel
- `auteur: str` — pour la page de titre et copyright
- `isbn: str | None` — pour la page de copyright
- `dedicace: str | None` — texte de dedicace optionnel

**Modules existants a utiliser** :
- `BookConfig` : `from bookforge.config.schema import BookConfig`
- `BookNode` : `from bookforge.ast_nodes import BookNode`
- `escape_typst()` : deja dans `pdf.py` — echapper le contenu texte utilisateur

### Architecture et contraintes

- `renderers/` depend de : `ast_nodes`, `config`, `external`, `errors` — ajouter `config` est architecturalement valide
- `renderers/` NE DOIT PAS dependre de : `parser`, `quality`, `judge`
- Pattern de generation Typst : string building sequentiel (meme approche que Story 2.3)
- Le template inline `_BASE_TEMPLATE` reste inchange — les pages liminaires sont inserees APRES
- `escape_typst()` DOIT etre utilise pour tout texte utilisateur (titre, auteur, dedicace, etc.)

### Strategie d'implementation

L'approche est purement dans le renderer Typst — pas de modification de l'AST. Les pages liminaires sont generees a partir des metadonnees `BookConfig`, pas du contenu Markdown. C'est conforme a l'architecture : le renderer combine AST (contenu) + config (metadonnees) pour produire le .typ final.

**Structure du fichier .typ genere** :
```
1. _BASE_TEMPLATE (page setup, typography)
2. #set page(numbering: none)     ← pas de numeros sur liminaires
3. Page de titre (titre, sous-titre, auteur)
4. #pagebreak()
5. Page de copyright
6. #pagebreak()
7. Page de dedicace (si configuree)
8. #pagebreak()
9. TDM (#outline)
10. #pagebreak()
11. #set page(numbering: "1")     ← numerotation arabe
12. #counter(page).update(1)       ← reset a page 1
13. Chapitres (contenu existant)
```

### Syntaxe Typst pour les pages liminaires

**Page de titre** :
```typst
#align(center + horizon)[
  #text(size: 28pt, weight: "bold")[Titre du Livre]
  #v(1em)
  #text(size: 18pt)[Sous-titre]
  #v(4em)
  #text(size: 16pt)[Nom de l'Auteur]
]
```

**Page de copyright** :
```typst
#align(bottom)[
  #set text(size: 9pt)
  \u{00A9} 2026 Nom de l'Auteur. Tous droits reserves.
  #linebreak()
  ISBN : 978-X-XXXX-XXXX-X
]
```

**Page de dedicace** :
```typst
#align(center + horizon)[
  #emph[Texte de dedicace]
]
```

**TDM** :
```typst
#heading(outlined: false, level: 1)[Table des matieres]
#outline(indent: auto)
```

### Notes de structure du projet

- Fichier `src/bookforge/renderers/pdf.py` : MODIFIER — ajouter les fonctions de pages liminaires et modifier `generate_typst()`
- Fichier `src/bookforge/renderers/__init__.py` : VERIFIER — la signature exportee doit rester coherente
- Fichier `tests/test_renderer_pdf.py` : MODIFIER — ajouter les nouveaux tests, mettre a jour les fixtures
- Fichier `tests/fixtures/golden/minimal.typ` : MODIFIER — mettre a jour pour inclure les pages liminaires
- Aucun nouveau fichier a creer (tout dans pdf.py)

### Anti-patterns a eviter

- **NE PAS** modifier l'AST (`BookNode`, `ChapterNode`, etc.) — les pages liminaires viennent de `BookConfig`
- **NE PAS** implementer la numerotation romaine pour les liminaires — c'est Story/Epic 4 (FR14)
- **NE PAS** implementer les en-tetes/pieds de page — c'est Story 2.5
- **NE PAS** implementer les pages de garde de chapitre — c'est Story 2.5
- **NE PAS** utiliser `os.path` — `pathlib.Path` uniquement
- **NE PAS** utiliser `print()` — `logging.getLogger("bookforge.renderers.pdf")`
- **NE PAS** oublier `escape_typst()` sur le contenu utilisateur (titre, auteur, dedicace)
- **NE PAS** casser les 72 tests existants — la nouvelle signature doit etre retro-compatible ou tous les tests mis a jour

### Intelligence de la Story 2.3 (precedente)

**Apprentissages cles** :
- Le template inline `_BASE_TEMPLATE` est prefere a un fichier externe (evite les problemes de resolution de chemin pip)
- Le premier chapitre N'A PAS de `#pagebreak()` — les suivants oui. Avec les liminaires, le premier chapitre viendra APRES la TDM qui a deja un pagebreak
- `_render_chapter(chapter, is_first, typ_dir)` : le parametre `is_first` controlait le pagebreak. Avec les liminaires, tous les chapitres auront un pagebreak (car la TDM precede)
- Les chemins d'images sont relatifs au `.typ` — pas d'impact sur cette story
- `str.maketrans` fonctionne avec des chaines multi-caracteres pour les remplacements
- Code review Gemini a trouve 6 problemes dans la story precedente — etre rigoureux

**Fichiers crees/modifies par Story 2.3** :
- `src/bookforge/renderers/pdf.py` (186 lignes actuelles)
- `src/bookforge/renderers/__init__.py`
- `tests/test_renderer_pdf.py` (492 lignes, 24 tests)
- `tests/fixtures/golden/minimal.typ`

**Etat du code** : 72 tests, ruff clean, mypy 0 erreurs

### Git Intelligence

- Dernier commit : `94b48aff fix(bookforge): address code review — add source_file/line_number to BookNode`
- Story 2.3 est en statut `review` — le code du renderer PDF est fonctionnel
- Pattern de commit : `feat(bookforge): implement Story X.Y — description`

### Dependances de cette story

- **Prerequis** : Story 2.3 (renderer PDF + template Typst) — DONE (review)
- **Bloque** : Story 2.5 (pages de garde chapitre + en-tetes/pieds de page)

### References

- [Source: _bmad-output/planning-artifacts/epics.md — Epic 2, Story 2.4]
- [Source: _bmad-output/planning-artifacts/architecture.md — Decision 2: Python -> Typst Interface]
- [Source: _bmad-output/planning-artifacts/architecture.md — Module Dependencies renderers/ -> ast_nodes, tokens, external, errors]
- [Source: _bmad-output/planning-artifacts/architecture.md — Project Structure templates/typst/]
- [Source: _bmad-output/planning-artifacts/prd.md — FR7 (TDM), FR12 (pages liminaires), FR14 (numerotation)]
- [Source: _bmad-output/implementation-artifacts/2-3-renderer-pdf-template-typst-de-base.md — Completion Notes, File List]
- [Source: Typst docs — outline(), counter(page), page numbering]
- [Source: src/bookforge/config/schema.py — BookConfig model avec dedicace, isbn, sous_titre]
- [Source: src/bookforge/renderers/pdf.py — generate_typst(), _BASE_TEMPLATE, escape_typst()]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

- Le parametre `config` est optionnel (`BookConfig | None = None`) pour la retro-compatibilite — les 24 tests existants passent sans modification
- `_render_front_matter()` orchestre l'assemblage de toutes les pages liminaires en une seule chaine Typst
- `escape_typst()` applique sur tout contenu utilisateur (titre, auteur, sous-titre, ISBN, dedicace)
- Golden file `minimal.typ` inchange car les tests de Story 2.3 n'utilisent pas `config` — la retro-compatibilite est assuree
- L'annee du copyright est dynamique via `datetime.date.today().year`

### Completion Notes List

- `_render_title_page(config)` : titre 28pt bold centre, sous-titre 18pt conditionnel, auteur 16pt, alignement `center + horizon`
- `_render_copyright_page(config)` : copyright (c) annee auteur, ISBN conditionnel, texte 9pt aligne en bas
- `_render_dedication_page(dedicace)` : texte en `#emph[]`, centre `center + horizon`
- `_render_toc()` : `#heading(outlined: false)` + `#outline(indent: auto)` — TDM cliquable native Typst
- `_render_front_matter(config)` : assemblage complet — `numbering: none` -> titre -> copyright -> dedicace -> TDM -> `numbering: "1"` + reset counter
- `generate_typst(book, output_path, config=None)` : insere front matter si config fourni
- `render_pdf(book, output_dir, config=None)` : passe config a generate_typst
- 13 nouveaux tests dans `TestFrontMatter` (page titre, sous-titre, copyright, ISBN, dedicace, TDM, ordre, numerotation, retro-compatibilite, echappement, integration)
- 85 tests totaux (72 existants + 13 nouveaux), ruff clean, mypy 0 erreurs

### Change Log

- 2026-04-06 : Implementation Story 2.4 — TDM et pages liminaires (6 fonctions, 13 tests)

### File List

- `src/bookforge/renderers/pdf.py` (modifie — ajout front matter + TDM)
- `tests/test_renderer_pdf.py` (modifie — 13 tests ajoutes dans TestFrontMatter)
