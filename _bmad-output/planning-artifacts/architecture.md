---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
lastStep: 8
status: 'complete'
completedAt: '2026-04-06'
inputDocuments:
  - '_bmad-output/planning-artifacts/prd.md'
  - '_bmad-output/planning-artifacts/prd-validation-report.md'
  - '_bmad-output/brainstorming/brainstorming-session-2026-04-05-1500.md'
workflowType: 'architecture'
project_name: 'BookForge'
user_name: 'JM'
date: '2026-04-06'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements (51 FRs) :**

| Catégorie | FRs | Implications architecturales |
|---|---|---|
| Configuration & entrée | FR1-5 | Module de parsing `book.yaml` + validation d'entrées, point d'entrée unique |
| Rendu intérieur | FR6-14 | Moteur de rendu PDF (Typst), AST intermédiaire, système de templates par type de page |
| Export multi-format | FR15-19 | Dual renderer (Typst + Pandoc), passes de transformation par format, post-processing unifié |
| Couverture & 4e | FR20-24 | Module couverture indépendant, calcul dimensionnel (dos), composition d'image |
| Design tokens | FR25-27 | Système de tokens YAML → templates, classes de document, escape hatch |
| LLM-judge | FR28-30 | Module LLM optionnel, capture screenshots, boucle feedback avec catalogue d'actions borné, mode offline |
| QA & validation | FR31-34 | Checks programmatiques indépendants, snapshot testing, polices embarquées |
| Preview & itération | FR35-38 | Sampling intelligent, progression observable par phase, sortie structurée |
| Logging | FR39-40 | Logging structuré transversal (timestamp, sévérité, composant, message) |
| Pages finales | FR41 | Templates optionnels intégrés au module structure |
| Multi-langue | FR43-47 | Module i18n (Vision), traduction LLM, adaptation typographique par locale |
| CLI | FR49-51 | Point d'entrée CLI, codes de sortie, output JSON |

**Non-Functional Requirements (15 NFRs) :**

| Catégorie | NFRs | Contrainte architecturale |
|---|---|---|
| Performance | NFR1-4 | Pipeline < 5 min/200p, EPUB < 2 min, preview < 10s — parallélisme intra-phase requis |
| Fiabilité | NFR5-7 | Déterminisme strict (version pinning obligatoire), zero crash silencieux, snapshot regression testing |
| Intégration | NFR8-10 | Offline-first, LLM optionnel, coût < 0.50$/livre, tolérance panne API |
| Maintenabilité | NFR11-13 | Modules indépendants testables, extensibilité renderer, < 5 deps runtime (budget en tension) |
| Portabilité | NFR14-15 | Windows/macOS/Linux (multiplicateur de complexité filesystem), installation ≤ 3 commandes |

**Scale & Complexity :**

- Domaine principal : CLI / compilateur de livres
- Niveau de complexité : Moyen-haut (rendu pro + boucle LLM sur chemin critique)
- Modèle architectural : Compilateur (front-end / IR / passes de transformation / back-ends multiples)
- Composants architecturaux estimés : 10-12 modules

### Modèle architectural — BookForge comme compilateur de livres

```
Front-end:
  Validator (book.yaml, Markdown, assets) → Parser → AST normalisé

Middle-end (résolution + passes):
  AST + ClassConfig + DesignTokens → Triplet immuable (contrat de rendu)
  Triplet → Passes de transformation spécifiques au format cible

Back-ends (parallélisables):
  AST transformé PDF → Renderer PDF (Typst)
  AST transformé EPUB → Renderer EPUB (Pandoc)
  Config couverture → Générateur couverture

QA (post-render):
  Phase 3: Checks programmatiques sur toutes les sorties
  Phase 4: LLM-judge optionnel (boucle sur PDF uniquement)
    PDF → Screenshots → LLM → Catalogue d'actions → Ajustements tokens → Re-render PDF

Phase 5: Export final
```

### Technical Constraints & Dependencies

- **Runtime :** Python >= 3.10, Typst (binaire standalone), Pandoc, Matplotlib — budget < 5 deps runtime
- **Budget dépendances en tension :** Python + Typst + Pandoc + Matplotlib = 4/5 slots. Packages Python supplémentaires probables (Pillow pour DPI, python-barcode pour ISBN). Clarifier si NFR13 compte les binaires externes seuls ou inclut les packages pip
- **Installation :** `pip install` + Typst + Pandoc. Pas de GTK/Pango/Cairo
- **Offline-first :** PDF + EPUB sans appel réseau obligatoire
- **Déterminisme :** Mêmes entrées → même sortie (hors LLM). Implique version pinning strict de toutes les dépendances (Typst, Pandoc, packages pip)
- **Portabilité :** Cross-platform Windows/macOS/Linux — zones à risque : chemins fichiers (séparateurs, longueur max), résolution polices système, encodage noms de fichiers, comportements OS-spécifiques de Typst/Pandoc

### Cross-Cutting Concerns

1. **Configuration centralisée** — `book.yaml` + design tokens irriguent parser, renderers, couverture, structure
2. **Contrat de rendu = triplet (AST, ClassConfig, DesignTokens)** — Les trois doivent être résolus et figés avant le fork vers les renderers. L'AST seul ne suffit pas comme contrat
3. **Passes de transformation par format** — Couche architecturale entre l'AST et les renderers. Lieu de la logique dual-format (fallback image, simplification tableaux, adaptation). Pas un concern "transversal" mais une couche à part entière
4. **Tokens (statiques) vs Règles de layout (dynamiques)** — Les design tokens YAML sont la configuration auteur. Les règles de layout sont les micro-décisions contextuelles du moteur de rendu (comportement en bord de page, etc.). Deux mécanismes, deux responsabilités
5. **Logging structuré** — Format uniforme (timestamp, sévérité, composant source) à travers tous les modules
6. **Gestion d'erreurs gracieuse** — Warnings explicites, jamais de crash silencieux, codes de sortie différenciés
7. **4 niveaux de fallback à architecturer** — Format (complexité → image), LLM (mode offline), Itération (max itérations → manuel), Rendu (gap : pas de stratégie si le moteur échoue sur un edge-case)
8. **Progression observable par phase** — Le pipeline reporte son avancement par phase (pas par étape linéaire) à travers tous les modules
9. **Structure naturelle en 5 phases** — Parse, Render parallèle, QA programmatique, LLM-judge optionnel, Export. Permet parallélisme intra-phase et progression reportable
10. **Asymétrie LLM-judge PDF/EPUB** — La boucle LLM ne concerne que le PDF (screenshots). Question ouverte : si le LLM ajuste les tokens, l'EPUB est-il re-rendu ?
11. **Catalogue d'actions LLM borné** — Le LLM-judge choisit dans un ensemble fini d'actions prédéfinies (augmenter espacement, réduire image, forcer saut de page...) garantissant la prévisibilité
12. **Validation ≠ Parsing** — Deux responsabilités distinctes. Le validateur est un gate d'entrée, le parser reçoit du contenu garanti valide
13. **Version pinning obligatoire** — Condition nécessaire au déterminisme NFR5. Lockfile de toutes les versions (Typst, Pandoc, packages pip)
14. **Portabilité comme multiplicateur de complexité** — Chaque module touchant au filesystem est un vecteur de bug cross-platform

### Observations Party Mode (Winston, Amelia, Mary, Dr. Quinn)

**Surconception identifiée pour MVP0 :**
- Le triplet AST+ClassConfig+DesignTokens → en MVP0, c'est `AST + config statique`
- 5 phases → Parse + Render + Export suffit en MVP0
- 4 niveaux de fallback → 2 suffisent (nominal + dégradé explicite)
- Logging structuré JSON → messages lisibles et barre de progression suffisent

**Manques identifiés :**
- **Modèle d'erreur utilisateur** — quand la compilation échoue, qu'est-ce que l'auteur voit et fait ? UX de CLI, pas du logging
- **Stratégie de cache** — recompiler tout ou invalider par chapitre modifié ? Impacte l'architecture plus que les 14 concerns
- **Schéma JSON/YAML pour `book.yaml`** — sans validation de schéma, le parsing est fragile
- **Contrat Python → Typst** — interface (subprocess ? API ?) non définie, c'est le cœur de MVP0
- **Stratégie de test** — golden files PDF, snapshots, fixtures. Non-négociable pour le déterminisme

**Garde-fou compilateur :** Le modèle compilateur s'applique à l'architecture interne, pas au contrat utilisateur. Ne pas dériver vers une complexité type `gcc` — la vision est "simple par défaut, puissant si nécessaire"

**Goulot d'étranglement épistémique (Dr. Quinn) :** Le vrai verrou n'est pas technique — c'est la définition formelle de "qualité professionnelle". Le LLM-judge ne peut pas évaluer ce qui n'est pas défini. Contradiction TRIZ : sortie déterministe vs jugement LLM non-déterministe. Solution : les tokens comme assertions vérifiables + catalogue d'actions borné = boucle convergente par construction

### Référentiels qualité et tokens — État de l'art

#### Seuils qualité automatisables (Book Quality Specification)

**Amazon KDP Print :**
- Résolution images : >= 300 DPI
- Fond perdu : 3.2 mm sur 3 bords extérieurs
- Marges intérieures : 9.6 mm (24-150p), 12.7 mm (151-300p), 15.9 mm (301-500p)
- Épaisseur tranche : nb pages × 0.002252" (papier blanc)
- Polices 100% embarquées, PDF < 650 Mo

**Typographie professionnelle (Bringhurst) :**
- Police corps : 10-12 pt (standard 6×9" : 11 pt)
- Interlignage : 120-145% du corps
- Longueur de ligne : 45-75 caractères (optimum 66)
- Alinéa : 1 em
- Césure : max 3 lignes consécutives avec trait d'union
- Justification : serif = justifié, sans-serif = fer à gauche

**EPUB 3.3 :**
- EPUBCheck 5.x : 0 erreur fatale
- Accessibilité WCAG 2.1 AA (obligatoire UE depuis juin 2025)
- Métadonnées accessibilité requises : `accessModeSufficient`, `accessMode`, `accessibilityFeature`

**ISO PDF/X-4 :** Profil ICC embarqué, polices 100%, transparences natives

**IBPA :** Tolérance 1 erreur mineure / 25 000 mots

#### Distinction : règles mécaniques vs sémantiques vs subjectives

| Type | Vérificateur | Exemples | Phase pipeline |
|---|---|---|---|
| Mécanique | Code (Typst, epubcheck, PIL) | DPI, marges, polices, orphelines, longueur de ligne | QA programmatique (Phase 3) |
| Sémantique | LLM-judge | Cohérence intro/chapitre, qualité aération visuelle, lisibilité couverture 150px | LLM-judge (Phase 4) |
| Subjective | Humain (hors v1) | "Test de l'étagère Eyrolles", impact émotionnel couverture | Manuel |

#### Modèle de tokens — 8 catégories (état de l'art industrie)

| Catégorie | Tokens | Source de référence |
|---|---|---|
| Géométrie page | format papier, marges (spine/edge/top/bottom), zone de rogne, bleed | KDP specs, Typst page setup |
| Typographie corps | font-family, font-size, line-height, letter-spacing | Bringhurst, W3C Design Tokens 2025.10 |
| Hiérarchie titres | taille/poids/espacement par niveau (h1-h4) | KOMA-Script, kaobook |
| Espacement | parindent, parskip, before/after headings | LaTeX memoir, Electric Book |
| Couleurs | texte, liens, filets, fonds encadrés | W3C Design Tokens |
| En-têtes/pieds | contenu running headers, style, numérotation | Typst bookly, memoir |
| Éléments spéciaux | style encadrés, callouts, frameworks, lettrines | Electric Book (~100 variables) |
| Couverture | titre, sous-titre, auteur, fond, spine width, 4e de couv | KDP cover specs |

#### Tokens comme assertions vérifiables

Les tokens ne sont pas de simples variables de style — ils portent un **contrat vérifiable** :

```yaml
# Exemple : token avec assertion
line_height:
  value: 1.35        # ratio interlignage/corps
  min: 1.20
  max: 1.45
  source: "Bringhurst §2.1"
  verifiable: true    # mesurable dans le PDF généré
```

Cette distinction permet de séparer le catalogue d'actions du LLM-judge (ne modifie que les tokens dont l'assertion est violée) du rendu déterministe (les assertions sont les critères d'arrêt de la boucle).

#### Projets de référence

- **Electric Book** (electricbookworks) — ~100 variables Sass, référence open-source book production config-driven
- **Typst bookly** — template paramétrique livres avec thèmes
- **LaTeX kaobook** — fusion KOMA-Script + tufte, état de l'art paramétrage LaTeX
- **Quarto + Typst** — `_quarto.yml` centralisant la config

## Starter Template Evaluation

### Primary Technology Domain

CLI Python / content production pipeline — basé sur l'analyse de contexte projet.

### Starter Options Considered

| Option | Pour | Contre |
|---|---|---|
| **Typer + uv + Hatchling** | Écosystème large, type hints, lockfile cross-platform, flexible | Typer API pré-`Annotated` |
| Cyclopts + uv | API plus moderne, meilleur support Union/Literal | Communauté plus petite, moins de tutoriels |
| Click + Poetry | Très mature, beaucoup de documentation | Verbose, Poetry lent, pas de type hints natifs |
| argparse + pip | Zéro dépendance CLI | Ergonomie développeur médiocre, pas de lockfile |

### Selected Starter: Typer + uv + Hatchling + Ruff + pytest

**Rationale :**
- Typer : sweet spot entre ergonomie (type hints) et maturité (écosystème FastAPI). CLI simple de BookForge ne nécessite pas les features avancées de Cyclopts
- uv : standard de facto 2025, lockfile cross-platform natif (NFR14), 10-100x plus rapide que pip
- Hatchling : pyproject.toml natif, support versioning Git (hatch-vcs)
- Ruff : remplace Black+Flake8+isort en un outil, standard Astral
- pytest : standard incontesté pour les tests Python

**Initialization Command:**

```bash
uv init bookforge --lib
cd bookforge
uv add typer matplotlib pyyaml
uv add --dev pytest ruff mypy
```

### Architectural Decisions Provided by Starter

**Language & Runtime:**
Python 3.10+, type hints systématiques, `pyproject.toml` comme fichier de configuration unique du projet

**Build System:**
Hatchling via `pyproject.toml`, versioning Git via hatch-vcs

**Dependency Management:**
uv avec `uv.lock` cross-platform — garantit le déterminisme (NFR5) et la portabilité (NFR14)

**Testing Framework:**
pytest avec fixtures de golden files pour snapshot testing (NFR7)

**Linting/Formatting:**
Ruff (lint + format) + mypy (type checking en CI) + Pyright (IDE)

**Project Structure:**

```
bookforge/
├── pyproject.toml
├── uv.lock
├── src/
│   └── bookforge/
│       ├── __init__.py
│       ├── cli.py              # Point d'entrée Typer (FR49-51)
│       ├── config.py           # Parsing + validation book.yaml (FR1, FR5)
│       ├── parser.py           # Markdown → AST (front-end)
│       ├── renderer_pdf.py     # AST → Typst → PDF (back-end)
│       ├── renderer_epub.py    # AST → Pandoc → EPUB (MVP0.5)
│       ├── cover.py            # Générateur couverture (MVP1)
│       ├── quality.py          # Checks programmatiques (Phase 3)
│       ├── judge.py            # LLM-judge optionnel (Phase 4, MVP2)
│       └── tokens.py           # Design tokens + assertions (MVP1)
├── tests/
│   ├── fixtures/
│   ├── test_config.py
│   ├── test_parser.py
│   └── test_renderer_pdf.py
└── templates/
    └── business-manual.typ
```

**Note:** L'initialisation du projet avec cette structure sera la première story d'implémentation.

## Core Architectural Decisions

### Decision Priority Analysis

**Décisions critiques (bloquent l'implémentation) :**
1. Représentation AST — Hybride markdown-it-py → dataclasses custom
2. Interface Python → Typst — Génération `.typ` + subprocess
3. Validation config — Pydantic v2
4. Stratégie d'erreurs — Exceptions typées + codes de sortie

**Décisions importantes (façonnent l'architecture) :**
5. Interface Python → Pandoc — Subprocess direct
6. Format design tokens — YAML auteur simple + registre système avec assertions
7. Pattern LLM — Interface Protocol + implémentation par provider
8. Gestion assets — Chemins relatifs au Markdown, résolus au parsing

**Décisions différées (post-MVP) :**
- Stratégie de cache / invalidation par chapitre (Growth)
- Hot reload / watch mode (Growth)
- Format de sortie web app (Vision)

### Décision 1 : Représentation AST

- **Choix :** Hybride — markdown-it-py (front-end parsing) → dataclasses custom typées (IR)
- **Rationale :** Séparation propre front-end/IR. Parser Markdown robuste (CommonMark, extensible par plugins pour `:::framework`), AST interne maîtrisé et typé pour les passes de transformation et les renderers
- **Affecte :** Parser, tous les renderers, passes de transformation, QA

### Décision 2 : Interface Python → Typst

- **Choix :** Génération de fichiers `.typ` + appel `typst compile` en subprocess
- **Rationale :** Contrôle total du template, fichier `.typ` intermédiaire debuggable, subprocess fiable cross-platform, zéro dépendance supplémentaire
- **Affecte :** renderer_pdf.py, templates/

### Décision 3 : Interface Python → Pandoc

- **Choix :** Subprocess direct (`pandoc` CLI)
- **Rationale :** Même pattern que Typst (cohérence), zéro dépendance Python supplémentaire, budget NFR13 préservé
- **Affecte :** renderer_epub.py

### Décision 4 : Validation config (book.yaml)

- **Choix :** Pydantic v2
- **Version :** Pydantic 2.x (vérifier version courante à l'implémentation)
- **Rationale :** Validation puissante, messages d'erreur utilisateur clairs out-of-the-box (répond au manque "modèle d'erreur utilisateur"), type hints natifs, sérialisation YAML → modèle directe
- **Budget deps :** Python + Typst(bin) + Pandoc(bin) + Matplotlib + Pydantic = 5/5 slots. Plafond NFR13 atteint
- **Affecte :** config.py (FR1, FR5), tokens.py

### Décision 5 : Format des design tokens

- **Choix :** YAML à deux niveaux — fichier auteur simple + registre système avec assertions
- **Rationale :** L'auteur écrit `font_size: 11`, le système résout vers un token avec contraintes (min/max/source). Le registre sert aussi de catalogue d'actions borné pour le LLM-judge
- **Affecte :** tokens.py, judge.py, renderer_pdf.py, renderer_epub.py

```yaml
# tokens.yaml (auteur — simple)
font_size: 11
line_height: 1.35
margin_inner: 15mm
```

```python
# registre interne (code — assertions)
TOKEN_REGISTRY = {
    "font_size": TokenSpec(min=9, max=14, unit="pt", source="Bringhurst"),
    "line_height": TokenSpec(min=1.20, max=1.45, source="Bringhurst §2.1"),
}
```

### Décision 6 : Stratégie d'erreurs

- **Choix :** Exceptions typées mappées aux codes de sortie FR50
- **Rationale :** Idiomatique Python, testable, messages lisibles (pas de stack trace pour l'auteur)

```python
class BookForgeError(Exception):
    exit_code: int

class InputError(BookForgeError):     # exit 1
class RenderError(BookForgeError):    # exit 2
class LLMError(BookForgeError):       # exit 3
```

- **Warnings :** Logging standard sans interruption du pipeline
- **Affecte :** Tous les modules, cli.py (catch top-level)

### Décision 7 : Pattern LLM

- **Choix :** Interface Protocol Python + une implémentation par provider
- **Rationale :** PRD prévoit Gemini → Claude/GPT-4o/local. Protocol = contrat de type sans dépendance, changement de provider = nouvelle classe

```python
class LLMJudge(Protocol):
    def evaluate(self, screenshots: list[Path], tokens: TokenSet) -> JudgeVerdict: ...
```

- **JudgeVerdict :** Score + liste d'actions du catalogue borné
- **Affecte :** judge.py, tokens.py (catalogue d'actions)

### Décision 8 : Gestion des assets

- **Choix :** Chemins relatifs au fichier Markdown source, résolus au parsing
- **Rationale :** Standard Markdown naturel, résolution unique au parsing, validation DPI centralisée post-résolution
- **Pipeline :** Parser résout → Validator vérifie (existence + DPI) → Renderer consomme chemins absolus
- **Affecte :** parser.py, quality.py (FR31)

### Decision Impact Analysis

**Séquence d'implémentation :**
1. config.py (Pydantic) — fondation, tout le pipeline en dépend
2. parser.py (markdown-it-py → AST custom) — front-end du compilateur
3. renderer_pdf.py (AST → .typ → subprocess typst) — premier livrable visible
4. cli.py (Typer + exceptions typées) — interface utilisateur
5. quality.py (validation assets, checks programmatiques) — QA
6. tokens.py (registre + YAML auteur) — MVP1
7. renderer_epub.py (subprocess pandoc) — MVP0.5
8. judge.py (Protocol + GeminiJudge) — MVP2

**Dépendances croisées :**
- Le registre de tokens (décision 5) est consommé par les renderers (2, 3), le judge (7), et la QA (8)
- La stratégie d'erreurs (6) traverse tous les modules — à implémenter dans les classes de base dès le départ
- L'AST custom (1) est le contrat central — sa structure doit être stabilisée avant les renderers

## Implementation Patterns & Consistency Rules

### Pattern Categories Defined

**8 zones de conflit potentielles identifiées** où des agents AI pourraient coder différemment sans guidelines.

### Naming Patterns

**Python :**

| Zone | Convention | Exemple |
|---|---|---|
| Modules | `snake_case.py` | `renderer_pdf.py` |
| Classes | `PascalCase` | `BookConfig`, `ChapterNode` |
| Fonctions/méthodes | `snake_case` | `parse_markdown()`, `render_pdf()` |
| Constantes | `UPPER_SNAKE` | `TOKEN_REGISTRY`, `MAX_LLM_ITERATIONS` |
| Noeuds AST | `PascalCase` + suffixe `Node` | `ChapterNode`, `CalloutNode`, `ImageNode` |
| Exceptions | `PascalCase` + suffixe `Error` | `InputError`, `RenderError` |

**YAML/Config :**

| Zone | Convention | Exemple |
|---|---|---|
| Clés book.yaml | `snake_case` | `font_size`, `margin_inner` |
| Noms de classes doc | `kebab-case` | `business-manual`, `fiction-novel` |
| Noms de tokens | `snake_case` | `line_height`, `heading_1_size` |

### Structure Patterns

**AST — Noeuds immuables :**

```python
@dataclass(frozen=True)
class ChapterNode:
    title: str
    children: tuple[ASTNode, ...]  # tuple, pas list (immuabilité)
    source_file: Path              # Traçabilité vers le .md source
    line_number: int               # Pour les messages d'erreur
```

Règles :
- Tous les noeuds `frozen=True` (immuabilité du triplet architectural)
- Enfants en `tuple`, jamais `list`
- Chaque noeud porte `source_file` + `line_number` (traçabilité erreurs)

**Subprocess — Pattern uniforme Typst/Pandoc :**

```python
def run_external(cmd: list[str], description: str) -> subprocess.CompletedProcess:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result
    except FileNotFoundError:
        raise RenderError(f"{description}: commande '{cmd[0]}' introuvable")
    except subprocess.CalledProcessError as e:
        raise RenderError(f"{description}: {e.stderr.strip()}")
```

Règles :
- Toujours `capture_output=True, text=True, check=True`
- Toujours wrapper en `RenderError` avec le stderr
- Jamais `shell=True` (sécurité + portabilité)

**Paths — Cross-platform :**

```python
from pathlib import Path
assets_dir = book_root / "images"                    # ✅
assets_dir = os.path.join(book_root, "images")       # ❌
assets_dir = f"{book_root}/images"                    # ❌
```

Règles :
- `pathlib.Path` partout, `os.path` interdit
- Jamais de concaténation de strings pour les chemins
- Chemins résolus en absolu au plus tôt (parser), relatifs jamais passés entre modules

### Communication Patterns

**Logging & Messages utilisateur :**

```python
import logging
logger = logging.getLogger("bookforge.renderer_pdf")

# Logging interne (développeur) — en anglais
logger.debug("Generating .typ file for chapter %s", chapter.title)
logger.warning("Image %s is %d DPI (< 300)", img.path, img.dpi)

# Message utilisateur (via exception) — en français, actionnable
raise InputError("L'image 'figures/fig1.png' est en 150 DPI (minimum 300)")
```

Règles :
- Un logger par module : `logging.getLogger("bookforge.<module>")`
- Logging = interne, technique, en anglais
- Messages utilisateur = via exceptions, en français, actionnable
- Warnings = `logger.warning()`, ne bloquent pas le pipeline
- Jamais de `print()` — tout passe par logging ou exceptions

### Process Patterns

**Testing :**

```
tests/
├── fixtures/
│   ├── books/
│   │   ├── minimal/          # book.yaml + 1 chapitre
│   │   ├── full/             # book.yaml + 12 chapitres + images
│   │   └── broken/           # Cas d'erreur intentionnels
│   └── golden/
│       ├── minimal.pdf       # Référence snapshot
│       └── minimal.typ       # Référence .typ intermédiaire
├── test_config.py
├── test_parser.py
└── test_renderer_pdf.py
```

Règles :
- Fixtures dans `tests/fixtures/`, jamais inline
- Golden files pour les snapshots (NFR5/NFR7)
- Nommage test : `test_<quoi>_<condition>_<attendu>()`
- Exemple : `test_parser_missing_image_raises_input_error()`

**Imports :**

```python
# Ordre : stdlib → third-party → bookforge (ruff enforce automatiquement)
import logging
from pathlib import Path

import yaml
from pydantic import BaseModel

from bookforge.config import BookConfig
from bookforge.ast_nodes import ChapterNode
```

### Enforcement Guidelines

**Tous les agents AI DOIVENT :**
- Utiliser `pathlib.Path` pour tout chemin (jamais `os.path`, jamais string concat)
- Wrapper tout subprocess via `run_external()` (jamais d'appel direct)
- Nommer les noeuds AST avec suffixe `Node`, les exceptions avec suffixe `Error`
- Logger via `logging.getLogger("bookforge.<module>")`, jamais `print()`
- Écrire les messages utilisateur en français via exceptions, le logging interne en anglais
- Utiliser `@dataclass(frozen=True)` pour tous les noeuds AST
- Placer les fixtures de test dans `tests/fixtures/`

**Pattern Enforcement :**
- Ruff enforce automatiquement : naming, imports, formatting
- mypy enforce les types en CI
- Code review pour : patterns subprocess, paths, logging, AST immuabilité
- Golden files = source de vérité pour le déterminisme (NFR5/NFR7)

## Project Structure & Boundaries

### Complete Project Directory Structure

```
bookforge/
├── pyproject.toml                  # Config centralisée (build, deps, ruff, mypy, pytest)
├── uv.lock                        # Lockfile cross-platform (déterminisme NFR5)
├── README.md
├── .gitignore
├── .github/
│   └── workflows/
│       └── ci.yml                  # ruff + mypy + pytest
│
├── src/
│   └── bookforge/
│       ├── __init__.py             # Version (__version__)
│       ├── cli.py                  # Typer entry point (FR49-51)
│       ├── errors.py               # BookForgeError, InputError, RenderError, LLMError
│       ├── external.py             # run_external() — pattern subprocess uniforme
│       │
│       ├── config/
│       │   ├── __init__.py
│       │   ├── schema.py           # Pydantic models BookConfig, ChapterConfig (FR1)
│       │   └── validator.py        # Validation book.yaml + assets (FR5)
│       │
│       ├── parser/
│       │   ├── __init__.py
│       │   ├── markdown.py         # markdown-it-py → tokens bruts
│       │   ├── semantic.py         # Plugin :::framework, :::callout (FR3, MVP1)
│       │   └── transform.py        # Tokens markdown-it → AST custom (dataclasses)
│       │
│       ├── ast_nodes/
│       │   ├── __init__.py         # Export tous les noeuds
│       │   ├── base.py             # ASTNode base, BookNode racine
│       │   ├── content.py          # ParagraphNode, HeadingNode, ImageNode, TableNode
│       │   ├── semantic.py         # CalloutNode, FrameworkNode, ChapterSummaryNode
│       │   └── structure.py        # ChapterNode, FrontMatterNode, BackMatterNode
│       │
│       ├── tokens/
│       │   ├── __init__.py
│       │   ├── registry.py         # TOKEN_REGISTRY, TokenSpec (min/max/source)
│       │   ├── resolver.py         # YAML auteur → tokens résolus + validés
│       │   └── defaults/
│       │       └── business_manual.yaml  # Tokens par défaut classe business-manual
│       │
│       ├── passes/
│       │   ├── __init__.py
│       │   ├── pdf_transform.py    # Passes AST spécifiques PDF (Typst)
│       │   └── epub_transform.py   # Passes AST spécifiques EPUB (fallback image, simplification)
│       │
│       ├── renderers/
│       │   ├── __init__.py
│       │   ├── pdf.py              # AST → .typ → subprocess typst compile (FR6-14)
│       │   ├── epub.py             # AST → HTML/Markdown → subprocess pandoc (FR15-18, MVP0.5)
│       │   └── cover.py            # Couverture + 4e + dos (FR20-24, MVP1)
│       │
│       ├── quality/
│       │   ├── __init__.py
│       │   ├── checks.py           # DPI, polices, marges, orphelines (FR31-34)
│       │   └── reporter.py         # Rapport QA structuré (FR39)
│       │
│       ├── judge/
│       │   ├── __init__.py
│       │   ├── protocol.py         # LLMJudge Protocol, JudgeVerdict, ActionCatalog
│       │   ├── gemini.py           # GeminiJudge (MVP2)
│       │   ├── mock.py             # MockJudge (tests)
│       │   └── loop.py             # Boucle feedback: screenshot → judge → tokens → re-render
│       │
│       └── pipeline.py             # Orchestrateur 5 phases (Phase 1-5)
│
├── templates/
│   └── typst/
│       ├── base.typ                # Template Typst de base
│       ├── business_manual.typ     # Classe business-manual
│       ├── chapter_page.typ        # Page de garde chapitre
│       └── cover.typ               # Template couverture
│
├── tests/
│   ├── conftest.py                 # Fixtures pytest partagées
│   ├── fixtures/
│   │   ├── books/
│   │   │   ├── minimal/            # book.yaml + 1 chapitre .md
│   │   │   ├── full/               # book.yaml + 12 chapitres + images
│   │   │   └── broken/             # Cas d'erreur (YAML invalide, image manquante, etc.)
│   │   ├── golden/
│   │   │   ├── minimal.typ         # Référence .typ intermédiaire
│   │   │   └── minimal_ast.json    # Référence AST sérialisé
│   │   └── tokens/
│   │       ├── valid.yaml          # Tokens valides
│   │       └── out_of_bounds.yaml  # Tokens hors bornes assertions
│   ├── test_config.py
│   ├── test_parser.py
│   ├── test_ast_nodes.py
│   ├── test_tokens.py
│   ├── test_passes.py
│   ├── test_renderer_pdf.py
│   ├── test_renderer_epub.py
│   ├── test_quality.py
│   ├── test_judge.py
│   └── test_pipeline.py           # Tests d'intégration pipeline complet
│
└── docs/
    └── book.yaml.example           # Exemple complet commenté
```

### Architectural Boundaries

**Module Boundaries — Qui appelle qui :**

```
cli.py → pipeline.py → config/ → parser/ → passes/ → renderers/ → quality/ → judge/
                                                                         ↑
                                                                    tokens/ (partagé)
```

| Module | Dépend de | Ne doit PAS dépendre de |
|---|---|---|
| `cli.py` | `pipeline`, `errors` | Aucun module interne directement |
| `pipeline.py` | Tous les modules | — |
| `config/` | `errors`, `pydantic` | Aucun autre module bookforge |
| `parser/` | `ast_nodes`, `errors`, `markdown-it-py` | `renderers`, `tokens`, `quality` |
| `ast_nodes/` | `pathlib` (stdlib) | Aucune dépendance bookforge |
| `tokens/` | `config`, `errors`, `pydantic` | `renderers`, `parser` |
| `passes/` | `ast_nodes`, `tokens` | `renderers` |
| `renderers/` | `ast_nodes`, `tokens`, `external`, `errors` | `parser`, `quality`, `judge` |
| `quality/` | `ast_nodes`, `errors` | `renderers`, `parser` |
| `judge/` | `tokens`, `errors` | `renderers`, `parser` |

**Règle clé :** Les dépendances vont de gauche à droite dans le pipeline. Jamais de dépendance circulaire. `ast_nodes/` et `errors.py` sont les seuls modules sans dépendance bookforge.

### Requirements to Structure Mapping

| Catégorie FR | Modules | Fichiers principaux |
|---|---|---|
| Configuration (FR1-5) | `config/` | `schema.py`, `validator.py` |
| Rendu intérieur (FR6-14) | `parser/`, `renderers/pdf.py`, `templates/` | `markdown.py`, `transform.py`, `pdf.py` |
| Export multi-format (FR15-19) | `renderers/`, `pipeline.py` | `pdf.py`, `epub.py`, `pipeline.py` |
| Couverture (FR20-24) | `renderers/cover.py`, `templates/cover.typ` | `cover.py` |
| Design tokens (FR25-27) | `tokens/` | `registry.py`, `resolver.py` |
| LLM-judge (FR28-30) | `judge/` | `protocol.py`, `loop.py`, `gemini.py` |
| QA (FR31-34) | `quality/` | `checks.py` |
| Preview & itération (FR35-38) | `pipeline.py`, `cli.py` | `pipeline.py` |
| Logging (FR39-40) | `quality/reporter.py` | `reporter.py` |
| CLI (FR49-51) | `cli.py`, `errors.py` | `cli.py` |

### Data Flow

```
book.yaml + *.md + images/
        │
        ▼
  ┌─ config/schema.py ──── BookConfig (Pydantic)
  │
  ▼
  ┌─ parser/markdown.py ── markdown-it tokens
  │    ▼
  ├─ parser/transform.py ─ BookNode (AST custom, frozen)
  │
  ▼
  ┌─ tokens/resolver.py ── ResolvedTokenSet (validé vs assertions)
  │
  ▼  Triplet immuable: (BookNode, ClassConfig, ResolvedTokenSet)
  │
  ├─ passes/pdf_transform.py ── AST transformé PDF
  │    ▼
  │  renderers/pdf.py ── .typ file → subprocess typst → output/livre.pdf
  │
  ├─ passes/epub_transform.py ── AST transformé EPUB
  │    ▼
  │  renderers/epub.py ── subprocess pandoc → output/livre.epub
  │
  ├─ renderers/cover.py ── output/couverture.pdf + couverture-kindle.jpg
  │
  ▼
  quality/checks.py ── QA report (DPI, marges, orphelines)
  │
  ▼ (optionnel, MVP2)
  judge/loop.py ── screenshot → LLM → actions → ajuste tokens → re-render
  │
  ▼
  output/
  ├── livre-interieur.pdf
  ├── couverture-complete.pdf
  ├── couverture-kindle.jpg
  ├── livre.epub
  ├── metadata-kdp.json
  └── qa-report.json
```

## Architecture Validation Results

### Coherence Validation ✅

- Toutes les décisions technologiques sont compatibles
- Les patterns sont cohérents avec le stack choisi
- La structure reflète fidèlement le modèle compilateur 5 phases
- Aucune contradiction entre décisions

### Requirements Coverage ✅

- **48/51 FRs** couvertes architecturalement (3 différées : FR42 Growth, FR43-47 Vision, FR48 Growth)
- **14/15 NFRs** couvertes (NFR13 clarifiée : interprétation = binaires externes uniquement)

### Implementation Readiness ✅

- 8 décisions critiques documentées avec rationale
- Patterns d'implémentation complets avec exemples de code
- Structure projet complète avec matrice de dépendances
- Mapping FR → modules explicite

### Issues résolues

1. **NFR13** → Interprétation : < 5 binaires externes (Typst + Pandoc = 2). Packages pip gérés par `uv.lock`
2. **FR35 (Preview)** → Ajouter `select_representative_pages()` dans `quality/` pour MVP2
3. **FR37 (Progression)** → Callback `progress_callback(phase, percent)` passé au pipeline, implémenté dans le CLI

### Architecture Completeness Checklist

**✅ Requirements Analysis**
- [x] Contexte projet analysé en profondeur (+ 4 sessions elicitation + party mode + recherche web)
- [x] Échelle et complexité évaluées (moyen-haut)
- [x] Contraintes techniques identifiées (budget deps, déterminisme, portabilité)
- [x] 14 cross-cutting concerns mappés
- [x] Référentiels qualité et tokens documentés (état de l'art)

**✅ Architectural Decisions**
- [x] 8 décisions critiques documentées avec versions et rationale
- [x] Stack technologique spécifié (Python/Typer/uv/Pydantic/markdown-it-py)
- [x] Patterns d'intégration définis (subprocess, Protocol)
- [x] Performance adressée (pipeline parallélisable)

**✅ Implementation Patterns**
- [x] Conventions naming (Python + YAML)
- [x] Patterns structure (AST frozen, subprocess uniforme, pathlib)
- [x] Patterns communication (logging/exceptions bilingue)
- [x] Patterns process (testing, imports)

**✅ Project Structure**
- [x] Arborescence complète définie
- [x] Boundaries modules avec matrice de dépendances
- [x] Points d'intégration mappés
- [x] Mapping FR → structure complet

### Architecture Readiness Assessment

**Overall Status :** READY FOR IMPLEMENTATION

**Confidence Level :** Haut

**Forces clés :**
- Modèle compilateur clair et éprouvé
- Séparation nette des responsabilités (matrice de dépendances)
- Tokens comme assertions vérifiables (résout le goulot épistémique)
- Enrichi par elicitation adversariale + systémique + recherche web

**Améliorations futures :**
- Stratégie de cache (Growth)
- Hot reload (Growth)
- Module i18n (Vision)
- Mécanisme de progression concret (à détailler en story)

### Implementation Handoff

**Tous les agents AI doivent :**
- Suivre les décisions architecturales exactement comme documentées
- Utiliser les patterns d'implémentation de façon cohérente
- Respecter la structure projet et les boundaries de modules
- Consulter ce document pour toute question architecturale

**Première priorité d'implémentation :**

```bash
uv init bookforge --lib
cd bookforge
uv add typer matplotlib pyyaml pydantic markdown-it-py
uv add --dev pytest ruff mypy
```

Puis : `config/schema.py` (Pydantic) → `parser/` → `renderers/pdf.py` → `cli.py`
