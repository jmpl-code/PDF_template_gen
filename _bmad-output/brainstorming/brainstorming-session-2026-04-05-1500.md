---
stepsCompleted: [1, 2, 3, 4]
inputDocuments: []
session_topic: 'Pipeline automatisé Markdown -> ebook pro publiable Amazon KDP'
session_goals: 'Rendu visuel professionnel, automatisation maximale, compatibilité KDP'
selected_approach: 'ai-recommended'
techniques_used: ['morphological-analysis', 'cross-pollination', 'resource-constraints']
ideas_generated: 46
technique_execution_complete: true
session_active: false
workflow_completed: true
facilitation_notes: 'Utilisateur très technique (Python, Typst, Matplotlib), pipeline existant à améliorer. Ouvert aux approches radicales (LLM multimodal). Fort intérêt pour automatisation totale.'
---

# Brainstorming Session Results

**Facilitateur:** JM
**Date:** 2026-04-05

---

## Session Overview

**Sujet :** Pipeline automatisé Markdown -> ebook pro publiable Amazon KDP
**Objectifs :** Rendu visuel professionnel, automatisation maximale, compatibilité KDP (EPUB/PDF)

### Contexte du projet

- Pipeline existant : Markdown -> Typst (stabilisé) -> PDF
- Diagrammes : Matplotlib haute résolution 300 DPI avec charte graphique
- Export EPUB via Pandoc
- Métadonnées via plan.yaml
- Outils testés et écartés : WeasyPrint (dépendances lourdes), xhtml2pdf (qualité insuffisante)

### Problèmes identifiés

- Pas de couverture / 4e de couverture
- Texte mal aéré
- Typographie de mauvaise qualité
- Schémas et diagrammes coupés
- Titres trop collés au texte

### Piste existante

- Approche HTML "façon slides imprimables" (résultats positifs d'un ami)
- Feedback Gemini Vision validant l'approche LLM-as-a-judge

---

## Technique Selection

**Approche :** Recommandation IA
**Techniques :** Analyse Morphologique -> Cross-Pollination -> Resource Constraints

---

## Technique Execution Results

### Analyse Morphologique

**Dimensions identifiées du pipeline :**

| # | Dimension | Options explorées |
|---|---|---|
| 1 | Format intermédiaire | HTML+CSS, LaTeX, EPUB natif, PDF direct, AST (Pandoc), DOCX, IDML, React/JSX |
| 2 | Moteur de rendu | Typst, WeasyPrint, Prince, Paged.js, Vivliostyle, xhtml2pdf |
| 3 | Typographie | Config manuelle, sélection IA par genre |
| 4 | Mise en page | Règles statiques, feedback loop LLM multimodal |
| 5 | Visuels | Matplotlib PNG, SVG, Typst canvas, génération IA |
| 6 | Structure livre | Templates manuels, génération auto |
| 7 | Templates/Thèmes | Template unique, bibliothèque par genre |
| 8 | Post-processing | Vérification manuelle, LLM vision critique |
| 9 | Boucle de feedback | Render -> Screenshot -> LLM -> Ajuste -> Re-render |

**Breakthrough :** L'idée d'un LLM multimodal comme "directeur artistique" dans la boucle, validée par un test Gemini réel.

### Cross-Pollination

**Domaines pillés :**

- **Édition print pro** -> Micro-templates par type de page, système BAT avec score qualité
- **Web design / Design Systems** -> Design tokens, composants sémantiques réutilisables
- **Outils de présentation** -> Mode "slide" pour pages à fort impact
- **LaTeX / académique** -> Classes de document, séparation contenu/présentation absolue
- **Jeu vidéo** -> Layer de "polish" auto (lettrines, filets, ornements)
- **DevOps / CI/CD** -> Pipeline avec quality gates, Book-as-Code

### Resource Constraints

**Contraintes testées :**

- "Une seule commande, zéro intervention" -> Presque toutes les idées survivent
- "Zéro dépendance lourde" -> Typst gagne (binaire unique)
- "LLM < 0.50$ par livre" -> Sampling intelligent de 5-10 pages représentatives
- "20 pages comme 300 pages" -> Design tokens et composants scalent naturellement

---

## Inventaire complet des idées (46)

### Theme 1 : Architecture "Book-as-Code"

| # | Idée | Description |
|---|---|---|
| 2 | Design tokens YAML | Fichier centralisé de tous les paramètres visuels, switchable par genre |
| 9 | Composants sémantiques Markdown | `:::framework`, `:::callout`, `:::chapter-summary` |
| 11 | Classes de document | `business-manual`, `fiction-novel`, `technical-guide` |
| 12 | Balises sémantiques custom | Le contenu est sémantique, le moteur décide du rendu par format |
| 8 | Design tokens par genre | Business = austère, fiction = élégant, switch en un mot |
| 15 | Book-as-Code YAML | Un seul fichier déclaratif pilote tout le pipeline |

### Theme 2 : LLM-as-a-Judge

| # | Idée | Description |
|---|---|---|
| 1 | Boucle feedback LLM multimodal | Render -> screenshot -> critique -> ajuste config -> re-render |
| 4 | Boucle rapide vs lente | Rapide = ajuste config (auto), lente = ajuste structure (semi-auto) |
| 5 | Checklist par catégorie | Typo (une fois), aération/visuels/structure (chaque build) |
| 7 | BAT avec score qualité | Épreuves numérotées, loop until score >= seuil |
| 16 | Sampling intelligent | 5-10 pages représentatives, ~0.10-0.30$ par livre |
| Couv #4 | LLM-judge couverture | Test miniature 150px + cohérence genre Amazon |
| Format #3 | LLM teste formats | Détecte les pages qui cassent en reflowable |

### Theme 3 : Couverture & 4e de couverture

| # | Idée | Description |
|---|---|---|
| Couv #1 | Template paramétrique | Piloté par classe + design tokens |
| Couv #2 | Illustration IA | Prompt généré depuis le contenu du livre |
| Couv #3 | Composition programmatique | Pillow/Cairo, pixel-perfect, versionnable |
| Couv #4 | LLM-judge couverture | Test miniature 150px |
| Couv #5 | Scraping références Amazon | Data-driven cover design |
| 4eCouv #1 | Contenu généré par LLM | Pitch, bullet points, bio auteur auto |
| 4eCouv #2 | Calcul auto du dos | Largeur = f(nombre pages, type papier) |
| 4eCouv #3 | ISBN/code-barres auto | python-barcode, placement automatique |

### Theme 4 : Structure du livre automatisée

| # | Idée | Description |
|---|---|---|
| TDM #1 | TDM auto depuis Markdown | Design piloté par la classe du document |
| TDM #2 | Multi-niveaux intelligente | Profondeur auto selon taille du livre |
| TDM #3 | Double TDM | Sommaire court au début + TDM détaillée à la fin |
| Garde #1 | Template par classe | Fond sombre + titre blanc pour business, minimaliste pour fiction |
| Garde #2 | Métadonnées de chapitre | Frontmatter par chapitre (quote, icon, mot-clé) |
| Garde #3 | Icônes/illustrations auto | Génération cohérente par chapitre via Matplotlib/IA |

### Theme 5 : Rendu & qualité visuelle

| # | Idée | Description |
|---|---|---|
| 3 | Bibliothèque design references | Pages "idéales" comme référence pour le LLM-judge |
| 6 | Micro-templates par type de page | Page titre, page dense, page figure, page framework |
| 10 | Mode slide pages impact | Approche "slides imprimables" pour pages de garde, résumés |
| 13 | Layer polish auto | Lettrines, filets décoratifs, ornements entre sections |
| 14 | Pipeline CI/CD quality gates | Checks programmatiques : DPI, marges, orphelines, taille fichier |

### Theme 6 : Multi-format & export

| # | Idée | Description |
|---|---|---|
| Format #1 | Double export | PDF fixed layout + EPUB reflowable auto |
| Format #2 | Reflowable enrichi | Fallback image auto pour éléments trop complexes |
| Preview #1 | Rendu partiel intelligent | 5 pages représentatives en 3 secondes |
| Preview #2 | Hot reload | Live preview à chaque sauvegarde |
| Preview #3 | Multi-format côte à côte | PDF + Kindle simulator + miniature Amazon |
| Preview #4 | Mode sans LLM | Checks programmatiques gratuits pour itérer |

### Theme 7 : Multi-langue

| # | Idée | Description |
|---|---|---|
| i18n #1 | Structure par langue | Dossier par langue, config/design partagés |
| i18n #2 | Traduction LLM au build | `--lang en` traduit et génère tout à la volée |
| i18n #3 | Adaptation typo par langue | Guillemets, espaces insécables, conventions auto |
| i18n #4 | Couverture multi-langue | LLM vérifie que le titre traduit tient dans l'espace |
| i18n #5 | Diagrammes localisés | Labels extraits, traduits, régénérés automatiquement |

### Theme 8 : Versioning & itération

| # | Idée | Description |
|---|---|---|
| Version #1 | Semver livre | "2e édition" auto sur couverture quand version majeure change |
| Version #2 | Changelog auto | Diff entre versions pour informer les lecteurs |
| Version #3 | Branches par édition | Reproductibilité totale, rebuild n'importe quelle édition |
| Version #4 | A/B testing couverture | 3 variantes générées, test taux de clic Amazon |

---

## Priorisation

### Quick Wins (Semaine 1)

| Priorité | Idée | Effort | Impact |
|---|---|---|---|
| QW1 | Design tokens YAML | ~1 jour | Fort — fondation de tout |
| QW2 | TDM auto depuis Markdown | ~1 jour | Moyen |
| QW3 | Pages de garde par classe | ~1 jour | Fort — visuel immédiat |
| QW4 | Balises sémantiques Markdown | ~2 jours | Fort |
| QW5 | Calcul auto du dos | ~0.5 jour | Moyen |
| QW6 | ISBN/code-barres auto | ~0.5 jour | Faible mais pro |
| QW7 | Preview partiel 5 pages | ~1 jour | Fort pour itération |

**Enchaînement :** QW1 → QW3 → QW4 → QW2 → QW7 → QW5+QW6

### Fort Impact (Semaines 2-3)

| Priorité | Idée | Effort | Dépendance |
|---|---|---|---|
| Impact #1 | Boucle LLM-judge + sampling | ~3-5 jours | QW1 (tokens) |
| Impact #2 | Couverture paramétrique + LLM-judge couv | ~3-4 jours | Parallélisable |
| Impact #3 | Classes de document + micro-templates | ~2-3 jours | QW1+QW3+QW4 |

### Expansion (Semaine 4+)

- 4eCouv contenu généré par LLM
- Double export PDF + EPUB
- Hot reload + preview multi-format
- Layer polish auto

### Breakthrough (Plus tard)

- Traduction LLM au build (i18n #2)
- Diagrammes localisés (i18n #5)
- A/B testing couvertures (Version #4)
- Scraping références Amazon (Couv #5)

---

## Architecture cible

```
book.yaml (config déclarative)
  ├── content: chapitres/*.md (avec balises sémantiques)
  ├── class: "business-manual"
  ├── design_tokens: "corporate-dark"
  ├── cover: { style: "dark-corporate", illustration: "ai" }
  ├── i18n: { source: "fr", targets: ["en", "es"] }
  └── quality: { min_score: 8, llm_judge: true }
          │
          ▼
    ┌─────────────┐
    │  PARSE       │  Markdown étendu -> AST avec composants sémantiques
    └──────┬──────┘
           ▼
    ┌─────────────┐
    │  STRUCTURE   │  Couverture + TDM + pages de garde + contenu + 4e de couv
    └──────┬──────┘
           ▼
    ┌─────────────┐
    │  RENDER      │  Typst / HTML selon la page, piloté par classe + tokens
    └──────┬──────┘
           ▼
    ┌─────────────┐
    │  POLISH      │  Lettrines, filets, ornements, ISBN auto
    └──────┬──────┘
           ▼
    ┌─────────────┐
    │  QA AUTO     │  Checks programmatiques (DPI, marges, orphelines, dos)
    └──────┬──────┘
           ▼
    ┌─────────────┐
    │  LLM JUDGE   │  Sampling 5-10 pages + couverture miniature 150px
    └──────┬──────┘  (loop jusqu'à score >= seuil)
           ▼
    ┌─────────────┐
    │  EXPORT      │  PDF KDP + EPUB Kindle + couverture print complète
    └─────────────┘
```

---

## Session Summary

**Achievements :**
- 46 idées générées à travers 3 techniques (Analyse Morphologique, Cross-Pollination, Resource Constraints)
- 8 thèmes identifiés couvrant l'intégralité du pipeline
- Architecture cible complète avec plan d'action séquencé
- Concept breakthrough validé : LLM multimodal comme directeur artistique en boucle de feedback

**Breakthrough moment :** L'idée du LLM-as-a-judge visuel, combinée avec le test Gemini réel de JM, a transformé la session d'un "comment améliorer le CSS" en un "comment construire un pipeline auto-correcteur intelligent".

**Prochaine étape recommandée :** Commencer par QW1 (design tokens YAML) — c'est la fondation sur laquelle tout le reste s'appuie.
