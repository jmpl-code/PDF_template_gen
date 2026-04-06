---
stepsCompleted: ['step-01-validate-prerequisites', 'step-02-design-epics', 'step-03-create-stories', 'step-04-final-validation']
inputDocuments:
  - '_bmad-output/planning-artifacts/prd.md'
  - '_bmad-output/planning-artifacts/architecture.md'
---

# BookForge - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for BookForge, decomposing the requirements from the PRD and Architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements

FR1: L'auteur peut definir un livre via `book.yaml` (titre, sous-titre, auteur, genre, chapitres, ISBN)
FR2: L'auteur peut fournir le contenu en fichiers Markdown standard
FR3: L'auteur peut utiliser des balises semantiques (`:::framework`, `:::callout`, `:::chapter-summary`) [MVP1]
FR4: L'auteur peut referencer des images et diagrammes depuis le Markdown
FR5: Le systeme peut valider les entrees (`book.yaml`, Markdown, assets) avec messages d'erreur explicites [MVP0]
FR6: Le systeme peut transformer du Markdown en PDF avec typographie conforme aux standards editoriaux (espaces insecables, ligatures, cesure automatique, interligne 120-140% du corps)
FR7: Le systeme peut generer une table des matieres depuis les headings Markdown
FR8: Le systeme peut generer des pages de garde de chapitre
FR9: Le systeme peut integrer images et diagrammes sans coupure de page, redimensionnes et centres automatiquement
FR10: Le systeme peut rendre encadres et frameworks visuellement distincts du texte [MVP1]
FR11: Le systeme peut appliquer une classe de document (`business-manual`) [MVP1]
FR12: Le systeme peut generer les pages liminaires (titre, copyright, dedicace optionnelle) [MVP0]
FR13: Le systeme peut generer des en-tetes/pieds de page configurables (titre livre, chapitre, numero) [MVP0]
FR14: Le systeme peut appliquer une numerotation differenciee (romaine liminaires, arabe corps) [MVP1]
FR15: Le systeme peut exporter en PDF valide conforme KDP print-on-demand
FR16: Le systeme peut exporter en EPUB conforme aux specifications EPUB 3.x, avec metadonnees completes, compatible Kindle [MVP0.5]
FR17: Le systeme peut rendre tous les elements lisibles dans l'EPUB [MVP0.5]
FR18: Le systeme peut produire PDF + EPUB en une seule commande [MVP0.5]
FR19: Le systeme peut exporter les metadonnees KDP (description, mots-cles, categories) pretes a copier-coller [MVP0]
FR20: Le systeme peut generer une couverture depuis un template parametrique
FR21: Le systeme peut generer une 4e de couverture (pitch, bio, code-barres ISBN) [MVP1]
FR22: Le systeme peut calculer la largeur du dos selon le nombre de pages [MVP1]
FR23: Le systeme peut assembler couverture + dos + 4e en image complete KDP [MVP1]
FR24: Le systeme peut generer une miniature couverture 150px pour verification [MVP1]
FR25: L'auteur peut personnaliser le rendu via design tokens YAML [MVP1]
FR26: L'auteur peut choisir une classe de document pre-chargeant un jeu de tokens [MVP1]
FR27: L'auteur peut surcharger ponctuellement le rendu via des instructions natives du moteur de rendu (escape hatch) [MVP1]
FR28: L'auteur peut soumettre des screenshots au LLM-judge et recevoir un feedback actionnable [MVP1]
FR29: Le systeme peut executer une boucle LLM-judge automatisee avec limite d'iterations [MVP2]
FR30: Le systeme peut fonctionner entierement sans LLM (mode offline) [MVP0]
FR31: Le systeme peut verifier que les images sont >= 300 DPI
FR32: Le systeme peut detecter les erreurs de mise en page (orphelines/veuves, images debordant des marges, tableaux tronques, titres isoles en bas de page) et emettre des warnings [MVP2]
FR33: Le systeme peut reproduire un rendu identique a partir des memes entrees [MVP0]
FR34: Le systeme peut embarquer les polices dans PDF et EPUB [MVP0]
FR35: L'auteur peut generer un preview rapide sur 5 pages representatives [MVP2]
FR36: L'auteur peut relancer le pipeline apres modification et voir le resultat mis a jour
FR37: Le systeme peut afficher la progression du pipeline (etape, pourcentage) [MVP0]
FR38: Le systeme peut organiser la sortie dans un dossier structure avec noms explicites [MVP0]
FR39: Le systeme peut logger warnings et erreurs dans un format structure (timestamp, severite warn/error, composant source, message descriptif)
FR40: Le systeme peut reporter le cout LLM par livre [MVP2]
FR41: Le systeme peut integrer des pages finales optionnelles (bibliographie, "du meme auteur", remerciements) [MVP1]
FR42: Le systeme peut appliquer des elements de polish (lettrines, filets, ornements) selon la classe [Growth]
FR43: L'auteur peut specifier langue source et cibles dans `book.yaml` [Vision]
FR44: Le systeme peut traduire le Markdown via LLM au build [Vision]
FR45: Le systeme peut adapter les conventions typographiques a la langue cible [Vision]
FR46: Le systeme peut generer couverture et 4e de couv dans la langue cible [Vision]
FR47: Le systeme peut regenerer les diagrammes avec labels traduits [Vision]
FR48: L'auteur peut definir une identite de collection reutilisable entre livres [Growth]
FR49: L'auteur peut lancer le pipeline via une commande unique acceptant le chemin vers `book.yaml` et des options (`--lang`, `--judge`, `--preview`) [MVP0]
FR50: Le systeme peut retourner des codes de sortie distincts (0 = succes, 1 = erreur d'entree, 2 = erreur de rendu, 3 = erreur LLM) [MVP0]
FR51: Le systeme peut produire un output machine-readable (JSON) avec le statut, les chemins de sortie et les warnings pour usage scripte [MVP1]

### NonFunctional Requirements

NFR1: Pipeline Markdown -> PDF en < 5 minutes pour 200 pages (hors LLM)
NFR2: Boucle LLM-judge en < 10 minutes total (max 3 iterations)
NFR3: Preview 5 pages en < 10 secondes
NFR4: Export EPUB en < 2 minutes pour 200 pages
NFR5: Resultat identique bit-for-bit pour memes entrees (hors LLM)
NFR6: Jamais de crash silencieux — erreur loggee, arret propre
NFR7: Tests regression visuels (snapshot diff) detectent toute modification
NFR8: Fonctionne entierement offline. LLM = couche optionnelle
NFR9: Cout LLM < 0.50$ par livre (sampling 5-10 pages)
NFR10: Tolere indisponibilite API LLM sans bloquer l'export
NFR11: Modules independants (parser, renderer PDF, renderer EPUB, cover, LLM-judge) testables isolement
NFR12: Ajout de renderer/format sans modifier le code existant
NFR13: Dependances externes < 5 runtime (hors dev/test) et versionnees
NFR14: Fonctionne sur Windows, macOS et Linux
NFR15: Installation en 3 commandes maximum

### Additional Requirements

- Starter template : Typer + uv + Hatchling + Ruff + pytest — initialisation via `uv init bookforge --lib`
- Structure projet complete avec 10+ modules organises en packages (config/, parser/, ast_nodes/, tokens/, passes/, renderers/, quality/, judge/)
- AST hybride : markdown-it-py (front-end) -> dataclasses custom frozen (IR)
- Interface Python -> Typst : generation fichiers .typ + subprocess `typst compile`
- Interface Python -> Pandoc : subprocess direct
- Validation config : Pydantic v2
- Format design tokens : YAML auteur simple + registre systeme avec assertions (min/max/source)
- Strategie d'erreurs : exceptions typees (BookForgeError, InputError, RenderError, LLMError) mappees aux codes de sortie
- Pattern LLM : interface Protocol Python + une implementation par provider
- Gestion assets : chemins relatifs au Markdown, resolus au parsing
- Pattern subprocess uniforme via `run_external()` (capture_output, text, check, jamais shell=True)
- Paths cross-platform : pathlib.Path partout, os.path interdit
- Logging : un logger par module (`bookforge.<module>`), messages utilisateur en francais via exceptions, logging interne en anglais
- Testing : golden files, fixtures dans tests/fixtures/, nommage `test_<quoi>_<condition>_<attendu>()`
- Sequence d'implementation : config -> parser -> renderer_pdf -> cli -> quality -> tokens -> epub -> judge
- Version pinning obligatoire pour determinisme (NFR5)
- CI : ruff + mypy + pytest via GitHub Actions

### UX Design Requirements

Pas de document UX Design. Les exigences UX sont couvertes par les FRs CLI (FR49-51) et les NFRs portabilite/installation (NFR14-15).

### FR Coverage Map

| FR | Epic | Description |
|---|---|---|
| FR1 | Epic 2 | Config book.yaml |
| FR2 | Epic 2 | Contenu Markdown |
| FR3 | Epic 4 | Balises semantiques |
| FR4 | Epic 2 | Images/diagrammes |
| FR5 | Epic 2 | Validation entrees |
| FR6 | Epic 2 | Typographie pro PDF |
| FR7 | Epic 2 | Table des matieres |
| FR8 | Epic 2 | Pages de garde chapitre |
| FR9 | Epic 2 | Integration images |
| FR10 | Epic 4 | Encadres/frameworks |
| FR11 | Epic 4 | Classe document |
| FR12 | Epic 2 | Pages liminaires |
| FR13 | Epic 2 | En-tetes/pieds de page |
| FR14 | Epic 4 | Numerotation romaine/arabe |
| FR15 | Epic 2 | Export PDF KDP |
| FR16 | Epic 3 | Export EPUB |
| FR17 | Epic 3 | Elements lisibles EPUB |
| FR18 | Epic 3 | PDF + EPUB une commande |
| FR19 | Epic 2 | Metadonnees KDP |
| FR20 | Epic 2 | Couverture template |
| FR21 | Epic 5 | 4e de couverture |
| FR22 | Epic 5 | Calcul largeur dos |
| FR23 | Epic 5 | Assemblage couv complete |
| FR24 | Epic 5 | Miniature 150px |
| FR25 | Epic 4 | Design tokens YAML |
| FR26 | Epic 4 | Classe + jeu de tokens |
| FR27 | Epic 4 | Escape hatch |
| FR28 | Epic 6 | LLM-judge manuel |
| FR29 | Epic 7 | Boucle LLM auto |
| FR30 | Epic 2 | Mode offline |
| FR31 | Epic 7 | Verification DPI |
| FR32 | Epic 7 | Detection erreurs layout |
| FR33 | Epic 2 | Reproductibilite |
| FR34 | Epic 2 | Polices embarquees |
| FR35 | Epic 7 | Preview 5 pages |
| FR36 | Epic 6 | Relance pipeline |
| FR37 | Epic 2 | Progression pipeline |
| FR38 | Epic 2 | Dossier sortie structure |
| FR39 | Epic 2 | Logging structure |
| FR40 | Epic 7 | Report cout LLM |
| FR41 | Epic 5 | Pages finales |
| FR42 | Epic 8 | Polish auto (Growth) |
| FR43 | Epic 9 | Langue source/cibles (Vision) |
| FR44 | Epic 9 | Traduction LLM (Vision) |
| FR45 | Epic 9 | Conventions typo langue (Vision) |
| FR46 | Epic 9 | Couv langue cible (Vision) |
| FR47 | Epic 9 | Diagrammes traduits (Vision) |
| FR48 | Epic 8 | Collection (Growth) |
| FR49 | Epic 2 | CLI commande unique |
| FR50 | Epic 2 | Codes de sortie |
| FR51 | Epic 6 | Output JSON |

## Epic List

### Epic 1 : Fondation du projet et pipeline minimal
L'auteur peut initialiser le projet BookForge et disposer de la structure de base prete au developpement.
**FRs couvertes :** Exigences additionnelles Architecture (starter template, structure projet, CI)

### Epic 2 : Du Markdown au PDF — Premier rendu
L'auteur peut transformer son manuscrit Markdown en un PDF avec une mise en page de base (TDM, pages liminaires, en-tetes/pieds de page, couverture statique).
**FRs couvertes :** FR1, FR2, FR4, FR5, FR6, FR7, FR8, FR9, FR12, FR13, FR15, FR19, FR20, FR30, FR33, FR34, FR37, FR38, FR39, FR49, FR50

### Epic 3 : Export EPUB Kindle
L'auteur peut generer un EPUB compatible Kindle en plus du PDF, les deux en une seule commande.
**FRs couvertes :** FR16, FR17, FR18

### Epic 4 : Design tokens et personnalisation avancee
L'auteur peut personnaliser le rendu via des tokens YAML, appliquer une classe de document, utiliser des balises semantiques et un escape hatch.
**FRs couvertes :** FR3, FR10, FR11, FR14, FR25, FR26, FR27

### Epic 5 : Couverture complete KDP
L'auteur peut generer une couverture complete (couv + dos calcule + 4e de couverture) et verifier la miniature 150px.
**FRs couvertes :** FR21, FR22, FR23, FR24, FR41

### Epic 6 : LLM-judge manuel et output structure
L'auteur peut soumettre des screenshots au LLM-judge pour un feedback actionnable et obtenir un rapport JSON machine-readable.
**FRs couvertes :** FR28, FR36, FR51

### Epic 7 : QA automatisee et pipeline intelligent
Le pipeline detecte automatiquement les erreurs de mise en page, execute la boucle LLM-judge automatisee, genere des previews rapides et reporte les couts.
**FRs couvertes :** FR29, FR31, FR32, FR35, FR40

### Epic 8 : Polish et identite de collection [Growth]
Le systeme applique des elements de polish (lettrines, filets) et permet de definir une identite de collection reutilisable.
**FRs couvertes :** FR42, FR48

### Epic 9 : Publication multilingue [Vision]
L'auteur peut traduire et publier son livre dans d'autres langues via LLM.
**FRs couvertes :** FR43, FR44, FR45, FR46, FR47

## Epic 1 : Fondation du projet et pipeline minimal

L'auteur dispose d'un projet BookForge initialise, structure et pret au developpement.

### Story 1.1 : Initialisation du projet avec le starter template

As a auteur-developpeur,
I want initialiser le projet BookForge avec la stack Typer + uv + Hatchling,
So that je dispose d'un squelette fonctionnel avec les dependances, le linting et les tests configures.

**Acceptance Criteria:**

**Given** un environnement avec Python >= 3.10, uv installe
**When** je lance `uv init bookforge --lib` et les commandes d'ajout de dependances
**Then** le projet contient `pyproject.toml` configure (Hatchling, Ruff, mypy, pytest), `uv.lock` genere, et la structure `src/bookforge/`
**And** `uv run pytest` passe sans erreur
**And** `uv run ruff check .` passe sans erreur

### Story 1.2 : Structure des modules et erreurs de base

As a auteur-developpeur,
I want disposer de la structure complete des packages et des classes d'erreurs,
So that les stories suivantes peuvent implementer chaque module dans son emplacement defini.

**Acceptance Criteria:**

**Given** le projet initialise (Story 1.1)
**When** je cree la structure des packages (`config/`, `parser/`, `ast_nodes/`, `tokens/`, `passes/`, `renderers/`, `quality/`, `judge/`) avec `__init__.py`
**Then** tous les packages sont importables (`from bookforge.config import ...`)
**And** `errors.py` definit `BookForgeError`, `InputError` (exit 1), `RenderError` (exit 2), `LLMError` (exit 3)
**And** `external.py` definit `run_external()` avec le pattern subprocess uniforme (capture_output, text, check, jamais shell=True)
**And** les tests verifient que chaque exception retourne le bon `exit_code`

### Story 1.3 : CI GitHub Actions

As a auteur-developpeur,
I want un pipeline CI qui execute ruff, mypy et pytest a chaque push,
So that la qualite du code est verifiee automatiquement.

**Acceptance Criteria:**

**Given** le projet avec sa structure (Story 1.2)
**When** un push est effectue sur le depot
**Then** GitHub Actions execute `ruff check`, `mypy`, et `pytest`
**And** le workflow fonctionne sur Python 3.10+ et les trois OS (Windows, macOS, Linux)
**And** le pipeline echoue si un check ne passe pas

## Epic 2 : Du Markdown au PDF — Premier rendu

L'auteur peut transformer son manuscrit Markdown en un PDF avec une mise en page de base (TDM, pages liminaires, en-tetes/pieds de page, couverture statique).

### Story 2.1 : Parsing et validation de book.yaml

As a auteur,
I want definir mon livre via `book.yaml` et recevoir des messages d'erreur clairs si la config est invalide,
So that je sais exactement quoi corriger avant de lancer le pipeline.

**Acceptance Criteria:**

**Given** un fichier `book.yaml` avec titre, sous-titre, auteur, genre, chapitres
**When** le systeme parse et valide la configuration via Pydantic v2
**Then** un objet `BookConfig` valide est retourne avec tous les champs types
**And** si un champ obligatoire manque, une `InputError` est levee avec un message en francais indiquant le champ manquant
**And** si un fichier chapitre reference n'existe pas, une `InputError` est levee avec le chemin du fichier

### Story 2.2 : Parser Markdown vers AST

As a auteur,
I want que mes fichiers Markdown soient parses en un AST structure,
So that le contenu est represente de maniere exploitable par les renderers.

**Acceptance Criteria:**

**Given** des fichiers Markdown references dans `book.yaml`
**When** le parser traite les fichiers via markdown-it-py
**Then** un `BookNode` (AST frozen) est produit avec `ChapterNode`, `HeadingNode`, `ParagraphNode`, `ImageNode`, `TableNode`
**And** chaque noeud porte `source_file` et `line_number` pour la tracabilite
**And** les chemins d'images sont resolus en absolu relatifs au fichier Markdown source
**And** si une image referencee n'existe pas, une `InputError` est levee
**And** les golden files de test verifient la stabilite de l'AST produit

### Story 2.3 : Renderer PDF — Template Typst de base

As a auteur,
I want que l'AST soit transforme en fichier Typst et compile en PDF,
So that j'obtiens un premier rendu PDF de mon manuscrit.

**Acceptance Criteria:**

**Given** un `BookNode` (AST) valide
**When** le renderer genere un fichier `.typ` et appelle `typst compile` via `run_external()`
**Then** un PDF valide est produit avec typographie conforme (interligne 120-140%, polices embarquees)
**And** le fichier `.typ` intermediaire est conserve pour debug
**And** les memes entrees produisent le meme PDF (determinisme NFR5)
**And** si Typst n'est pas installe, une `RenderError` claire est levee

### Story 2.4 : Table des matieres et pages liminaires

As a auteur,
I want que le PDF contienne une TDM cliquable et des pages liminaires (titre, copyright),
So that mon livre a une structure professionnelle.

**Acceptance Criteria:**

**Given** un AST avec plusieurs chapitres et headings
**When** le renderer produit le PDF
**Then** une table des matieres est generee automatiquement depuis les headings avec numeros de page
**And** les pages liminaires (page de titre, page de copyright) sont inserees avant le contenu
**And** une page de dedicace optionnelle est ajoutee si configuree dans `book.yaml`

### Story 2.5 : Pages de garde de chapitre et en-tetes/pieds de page

As a auteur,
I want que chaque chapitre commence par une page de garde et que le PDF ait des en-tetes/pieds de page,
So that la navigation dans le livre est fluide et professionnelle.

**Acceptance Criteria:**

**Given** un AST avec des chapitres
**When** le renderer produit le PDF
**Then** chaque chapitre commence sur une nouvelle page avec une page de garde (titre du chapitre)
**And** les en-tetes affichent le titre du livre et le chapitre courant
**And** les pieds de page affichent le numero de page
**And** les pages liminaires n'ont pas d'en-tetes/pieds de page

### Story 2.6 : Integration des images et diagrammes

As a auteur,
I want que les images et diagrammes soient integres sans coupure de page, redimensionnes et centres,
So that les visuels sont lisibles et bien positionnes.

**Acceptance Criteria:**

**Given** un AST contenant des `ImageNode` avec chemins resolus
**When** le renderer produit le PDF
**Then** les images sont centrees horizontalement
**And** les images trop larges sont redimensionnees pour tenir dans les marges
**And** aucune image n'est coupee par un saut de page (protection anti-coupure)
**And** les images conservent leur ratio d'aspect

### Story 2.7 : Couverture template statique

As a auteur,
I want qu'une couverture de base soit generee depuis le titre, sous-titre et auteur,
So that j'ai une couverture utilisable des MVP0.

**Acceptance Criteria:**

**Given** les informations de couverture dans `book.yaml` (titre, sous-titre, auteur)
**When** le pipeline genere la couverture
**Then** une image de couverture est produite via un template Typst statique
**And** le titre, sous-titre et nom d'auteur sont affiches lisiblement
**And** le fichier couverture est place dans le dossier de sortie

### Story 2.8 : Export metadonnees KDP et dossier de sortie

As a auteur,
I want que les metadonnees KDP soient exportees et la sortie organisee dans un dossier structure,
So that je peux copier-coller les metadonnees sur KDP et retrouver facilement mes fichiers.

**Acceptance Criteria:**

**Given** un `BookConfig` avec description, mots-cles, categories
**When** le pipeline termine
**Then** un fichier `metadata-kdp.json` est genere avec description, mots-cles et categories prets a copier-coller
**And** le dossier de sortie `output/` contient les fichiers nommes explicitement (`livre-interieur.pdf`, `couverture.pdf`, `metadata-kdp.json`)
**And** la structure est coherente a chaque execution

### Story 2.9 : CLI, logging et progression

As a auteur,
I want lancer le pipeline via une commande unique avec progression visible et logging structure,
So that je suis informe de l'avancement et des eventuels problemes.

**Acceptance Criteria:**

**Given** un `book.yaml` valide et les fichiers Markdown
**When** je lance `python -m bookforge book.yaml`
**Then** le pipeline s'execute bout-en-bout (parse -> render -> export) sans appel reseau (mode offline)
**And** la progression est affichee par phase (parsing, rendering, export)
**And** les warnings sont logges avec timestamp, severite, composant source et message descriptif
**And** le code de sortie est 0 en cas de succes, 1 pour erreur d'entree, 2 pour erreur de rendu
**And** le pipeline fonctionne sur Windows, macOS et Linux (pathlib partout)

## Epic 3 : Export EPUB Kindle

L'auteur peut generer un EPUB compatible Kindle en plus du PDF, les deux en une seule commande.

### Story 3.1 : Renderer EPUB via Pandoc

As a auteur,
I want que mon manuscrit soit exporte en EPUB conforme EPUB 3.x compatible Kindle,
So that je peux publier sur le Kindle Store.

**Acceptance Criteria:**

**Given** un `BookNode` (AST) valide et un `BookConfig`
**When** le renderer EPUB transforme l'AST et appelle `pandoc` via `run_external()`
**Then** un EPUB valide est produit avec metadonnees completes (titre, auteur, langue, description)
**And** tous les elements (texte, images, tableaux) sont lisibles dans l'EPUB
**And** les tableaux de plus de 4 colonnes sont convertis en image fallback
**And** les polices sont embarquees dans l'EPUB (FR34)
**And** si Pandoc n'est pas installe, une `RenderError` claire est levee

### Story 3.2 : Dual export PDF + EPUB en une commande

As a auteur,
I want produire PDF et EPUB en une seule execution du pipeline,
So that je gagne du temps et j'ai les deux formats prets simultanement.

**Acceptance Criteria:**

**Given** un `book.yaml` valide
**When** je lance `python -m bookforge book.yaml`
**Then** le dossier de sortie contient `livre-interieur.pdf` ET `livre.epub`
**And** les deux formats sont produits en une seule execution sans relance
**And** l'EPUB est genere en < 2 minutes pour 200 pages (NFR4)
**And** si le rendu EPUB echoue, le PDF est quand meme produit avec un warning

## Epic 4 : Design tokens et personnalisation avancee

L'auteur peut personnaliser le rendu via des tokens YAML, appliquer une classe de document, utiliser des balises semantiques et un escape hatch.

### Story 4.1 : Systeme de design tokens YAML et registre d'assertions

As a auteur,
I want personnaliser le rendu via un fichier `tokens.yaml` simple (font_size, line_height, marges...),
So that j'adapte l'apparence sans toucher au code ni aux templates.

**Acceptance Criteria:**

**Given** un fichier `tokens.yaml` avec des valeurs simples (ex: `font_size: 11`)
**When** le systeme resout les tokens via le registre interne (`TokenSpec` avec min/max/source)
**Then** un `ResolvedTokenSet` valide est produit
**And** si une valeur est hors bornes (ex: `font_size: 3`), un warning est emis avec la borne et la source de reference
**And** les tokens resolus sont consommes par les renderers PDF et EPUB
**And** les tokens par defaut de la classe `business-manual` sont fournis dans `defaults/business_manual.yaml`

### Story 4.2 : Classe de document et jeu de tokens predefini

As a auteur,
I want choisir une classe de document (`business-manual`) qui precharge un jeu de tokens coherent,
So that j'obtiens un rendu professionnel sans configuration manuelle.

**Acceptance Criteria:**

**Given** `book.yaml` avec `class: business-manual`
**When** le pipeline charge la configuration
**Then** les tokens par defaut de la classe sont charges
**And** les tokens auteur (si presents) surchargent les tokens de classe
**And** le rendu PDF et EPUB utilise les tokens resolus (classe + surcharges)

### Story 4.3 : Balises semantiques (frameworks, callouts, chapter-summary)

As a auteur,
I want utiliser des balises `:::framework`, `:::callout`, `:::chapter-summary` dans mon Markdown,
So that les encadres et frameworks sont visuellement distincts du texte.

**Acceptance Criteria:**

**Given** du Markdown contenant `:::framework`, `:::callout`, `:::chapter-summary`
**When** le parser traite le contenu via le plugin semantique markdown-it-py
**Then** des noeuds `FrameworkNode`, `CalloutNode`, `ChapterSummaryNode` sont crees dans l'AST
**And** le renderer PDF produit des encadres visuellement distincts (bordure, fond, espacement)
**And** le renderer EPUB produit un style CSS distinct pour chaque type de balise
**And** une balise non reconnue leve un warning (pas une erreur)

### Story 4.4 : Numerotation differenciee et escape hatch Typst

As a auteur,
I want une numerotation romaine pour les pages liminaires et arabe pour le corps, et pouvoir injecter du Typst natif si necessaire,
So that j'ai un controle fin sur des cas specifiques sans etre limite par les tokens.

**Acceptance Criteria:**

**Given** un livre avec pages liminaires et corps
**When** le renderer produit le PDF
**Then** les pages liminaires sont numerotees en chiffres romains (i, ii, iii...)
**And** le corps commence a la page 1 en chiffres arabes
**And** si `book.yaml` contient un champ `typst_raw`, le contenu est injecte tel quel dans le fichier `.typ`
**And** un escape hatch invalide produit une `RenderError` claire (pas un crash Typst obscur)

## Epic 5 : Couverture complete KDP

L'auteur peut generer une couverture complete (couv + dos calcule + 4e de couverture) et verifier la miniature 150px.

### Story 5.1 : 4e de couverture et calcul du dos

As a auteur,
I want generer une 4e de couverture avec pitch, bio et code-barres ISBN, et que le dos soit calcule automatiquement,
So that j'ai tous les elements requis pour l'impression KDP.

**Acceptance Criteria:**

**Given** un `book.yaml` avec pitch, bio auteur, ISBN et le PDF interieur genere
**When** le module couverture est execute
**Then** une 4e de couverture est produite avec le pitch, la bio et un code-barres ISBN
**And** la largeur du dos est calculee automatiquement : nombre de pages x 0.002252" (papier blanc KDP)
**And** si l'ISBN est absent, la 4e est generee sans code-barres avec un warning

### Story 5.2 : Assemblage couverture complete et miniature

As a auteur,
I want que couverture + dos + 4e soient assembles en une image complete KDP, et qu'une miniature 150px soit generee,
So that je peux uploader directement sur KDP et verifier le rendu Amazon.

**Acceptance Criteria:**

**Given** la couverture avant, le dos calcule et la 4e de couverture
**When** le module assemblage est execute
**Then** un fichier `couverture-complete.pdf` est produit avec couv + dos + 4e aux dimensions KDP (avec fond perdu 3.2mm)
**And** un fichier `couverture-kindle.jpg` est produit (couverture seule)
**And** un fichier `couverture-miniature-150px.jpg` est produit pour verification du rendu Amazon
**And** le titre est lisible sur la miniature 150px

### Story 5.3 : Pages finales optionnelles

As a auteur,
I want integrer des pages finales optionnelles (bibliographie, "du meme auteur", remerciements),
So that mon livre a une fin professionnelle et complete.

**Acceptance Criteria:**

**Given** un `book.yaml` avec des sections optionnelles (bibliography, also_by, acknowledgments)
**When** le renderer produit le PDF
**Then** les pages finales configurees sont ajoutees apres le dernier chapitre
**And** chaque page finale commence sur une nouvelle page avec un titre
**And** les pages finales non configurees ne sont pas incluses (pas de page vide)
**And** les pages finales sont incluses dans la table des matieres

## Epic 6 : LLM-judge manuel et output structure

L'auteur peut soumettre des screenshots au LLM-judge pour un feedback actionnable et obtenir un rapport JSON machine-readable.

### Story 6.1 : Interface LLM-judge et evaluation manuelle

As a auteur,
I want soumettre des screenshots de pages au LLM-judge et recevoir un feedback actionnable sur la mise en page,
So that je sais precisement quels tokens ajuster pour ameliorer le rendu.

**Acceptance Criteria:**

**Given** un PDF genere et l'option `--judge` activee
**When** le systeme capture des screenshots de pages representatives et les soumet au LLM (Gemini Vision)
**Then** un `JudgeVerdict` est retourne avec un score qualite et une liste d'actions du catalogue borne (ex: augmenter espacement, reduire image)
**And** les actions referencent des tokens specifiques avec les valeurs suggerees
**And** le verdict est affiche de maniere lisible a l'auteur
**And** si l'API LLM est indisponible, un warning est emis et le pipeline continue sans bloquer (NFR10)
**And** le protocole `LLMJudge` est implemente avec `GeminiJudge` comme premiere implementation

### Story 6.2 : Relance pipeline et output JSON machine-readable

As a auteur,
I want relancer le pipeline apres modification et obtenir un rapport JSON avec statut, chemins et warnings,
So that je peux iterer rapidement et integrer BookForge dans des scripts.

**Acceptance Criteria:**

**Given** un pipeline deja execute et des modifications apportees (tokens, contenu)
**When** je relance `python -m bookforge book.yaml`
**Then** le pipeline re-genere tous les livrables avec les modifications prises en compte
**And** avec l'option `--json`, un fichier `report.json` est produit contenant : statut (success/error), chemins des fichiers generes, liste des warnings, score LLM-judge (si active)
**And** le JSON est conforme a un schema stable pour usage scripte

## Epic 7 : QA automatisee et pipeline intelligent

Le pipeline detecte automatiquement les erreurs de mise en page, execute la boucle LLM-judge automatisee, genere des previews rapides et reporte les couts.

### Story 7.1 : Checks QA programmatiques

As a auteur,
I want que le pipeline verifie automatiquement la qualite du rendu (DPI images, erreurs de mise en page),
So that les problemes techniques sont detectes avant publication.

**Acceptance Criteria:**

**Given** un PDF et un EPUB generes
**When** les checks QA sont executes
**Then** les images < 300 DPI sont detectees et reportees avec le chemin et le DPI reel
**And** les orphelines/veuves sont detectees et reportees
**And** les images debordant des marges sont detectees
**And** les tableaux tronques sont detectes
**And** les titres isoles en bas de page sont detectes
**And** un rapport QA structure est produit avec severite (warning/error) par probleme

### Story 7.2 : Boucle LLM-judge automatisee

As a auteur,
I want que le LLM-judge itere automatiquement (capture -> critique -> ajuste tokens -> re-rend) avec une limite d'iterations,
So that le rendu s'ameliore automatiquement sans intervention manuelle.

**Acceptance Criteria:**

**Given** un PDF genere et l'option `--judge` avec mode automatique
**When** la boucle LLM-judge est declenchee
**Then** le systeme capture des screenshots, soumet au LLM, applique les actions du catalogue borne aux tokens, et re-rend le PDF
**And** la boucle s'arrete quand le score qualite atteint le seuil OU apres max 3 iterations
**And** le score qualite augmente (ou stagne) entre iterations — jamais de regression
**And** si la boucle ne converge pas apres 3 iterations, un fallback manuel est propose avec le dernier verdict
**And** la boucle complete s'execute en < 10 minutes (NFR2)

### Story 7.3 : Preview rapide et report cout LLM

As a auteur,
I want generer un preview rapide sur 5 pages representatives et connaitre le cout LLM par livre,
So that je peux iterer rapidement sans attendre le rendu complet et maitriser mon budget.

**Acceptance Criteria:**

**Given** un `book.yaml` valide
**When** je lance `python -m bookforge book.yaml --preview`
**Then** 5 pages representatives sont selectionnees (couverture, TDM, debut chapitre, page avec image, page avec tableau)
**And** seules ces pages sont rendues en PDF
**And** le preview est genere en < 10 secondes (NFR3)
**And** a la fin de chaque execution avec LLM, le cout estime est affiche (tokens consommes x prix)
**And** le cout cumule est inclus dans le `report.json`
**And** le cout par livre reste < 0.50$ via le sampling intelligent (NFR9)

## Epic 8 : Polish et identite de collection [Growth]

Le systeme applique des elements de polish (lettrines, filets) et permet de definir une identite de collection reutilisable.

### Story 8.1 : Polish automatique (lettrines, filets, ornements)

As a auteur,
I want que le systeme applique automatiquement des elements de polish selon la classe de document,
So that le rendu atteint un niveau de finition d'editeur professionnel.

**Acceptance Criteria:**

**Given** un livre avec une classe de document (`business-manual`)
**When** le renderer produit le PDF
**Then** des lettrines sont appliquees au debut de chaque chapitre selon la classe
**And** des filets decoratifs separent les sections selon la classe
**And** des ornements de fin de chapitre sont ajoutes selon la classe
**And** chaque element de polish est configurable via les design tokens (activable/desactivable)

### Story 8.2 : Identite de collection reutilisable

As a auteur,
I want definir une identite de collection (palette, polices, mise en page) reutilisable entre livres,
So that tous les livres d'une meme serie ont un rendu coherent.

**Acceptance Criteria:**

**Given** un fichier `collection.yaml` definissant une identite visuelle (polices, couleurs, style couverture)
**When** `book.yaml` reference cette collection
**Then** les tokens de la collection sont charges comme base (avant la classe, avant les surcharges auteur)
**And** la couverture utilise le gabarit de la collection
**And** deux livres utilisant la meme collection produisent un rendu visuellement coherent

## Epic 9 : Publication multilingue [Vision]

L'auteur peut traduire et publier son livre dans d'autres langues via LLM.

### Story 9.1 : Traduction LLM et adaptation typographique

As a auteur,
I want traduire mon manuscrit Markdown via LLM au build et que les conventions typographiques s'adaptent a la langue cible,
So that je peux publier une edition dans une autre langue sans traduction manuelle.

**Acceptance Criteria:**

**Given** un `book.yaml` avec `lang: fr` et `targets: ["en"]`
**When** je lance `python -m bookforge book.yaml --lang en`
**Then** le contenu Markdown est traduit via LLM dans la langue cible
**And** les conventions typographiques sont adaptees (guillemets droits en anglais, pas d'espace insecable avant ponctuation)
**And** le resultat traduit est rendu en PDF + EPUB avec les memes tokens
**And** si la traduction allonge un titre au-dela de la zone de couverture, un warning est emis

### Story 9.2 : Couverture et diagrammes localises

As a auteur,
I want que la couverture, la 4e de couverture et les diagrammes soient regeneres dans la langue cible,
So that l'edition traduite est complete et coherente.

**Acceptance Criteria:**

**Given** une traduction en cours vers une langue cible
**When** le pipeline genere les livrables traduits
**Then** le titre et sous-titre de couverture sont dans la langue cible
**And** la 4e de couverture (pitch, bio) est traduite
**And** les diagrammes Matplotlib sont regeneres avec les labels traduits
**And** si un diagramme ne peut pas etre regenere (image statique), un warning est emis et l'original est conserve
