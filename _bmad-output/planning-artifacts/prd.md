---
stepsCompleted: ['step-01-init', 'step-02-discovery', 'step-02b-vision', 'step-02c-executive-summary', 'step-03-success', 'step-04-journeys', 'step-05-domain-skipped', 'step-06-innovation', 'step-07-project-type', 'step-08-scoping', 'step-09-functional', 'step-10-nonfunctional', 'step-11-polish', 'step-12-complete']
inputDocuments: ['_bmad-output/brainstorming/brainstorming-session-2026-04-05-1500.md']
workflowType: 'prd'
documentCounts:
  briefs: 0
  research: 0
  brainstorming: 1
  projectDocs: 0
classification:
  projectType: content_production_pipeline
  scope: automated_book_production
  domain: digital_publishing_kdp
  complexity: high
  projectContext: greenfield
  constraints:
    - YAGNI strict — pas d'abstraction tant qu'un seul utilisateur
    - QA deux couches — checks objectifs (programmatiques) + critique subjective (LLM-judge)
    - Apprentissages des prototypes intégrés comme contraintes de design (Typst, Matplotlib 300 DPI, plan.yaml)
lastEdited: '2026-04-06'
editHistory:
  - date: '2026-04-06'
    changes: 'Validation + Edit: mesurabilite FR6/FR32/FR39, leakage FR6/FR16/FR27, NFR13 precision, Parcours 5 multilingue, Interface CLI FR49-51'
---

# Product Requirements Document — BookForge

**Auteur :** JM
**Date :** 2026-04-05

## Executive Summary

**BookForge** est un pipeline de production de contenu qui transforme des fichiers Markdown en ebooks de qualité éditoriale professionnelle, publiables sur Amazon KDP — en une seule commande. Le produit cible un auto-éditeur technique (l'auteur lui-même) qui produit des livres business et non-fiction.

**Le problème :** Les outils existants (Pandoc, WeasyPrint, Typst seul) produisent des rendus visuellement amateurs — typographie générique, mise en page sans aération, diagrammes coupés, absence de couverture. Le fossé entre "auto-édité" et "édité par un professionnel" reste infranchissable sans compétences en design graphique ou recours à un maquettiste.

**La solution :** BookForge intègre un LLM multimodal comme directeur artistique automatisé dans une boucle de feedback : le pipeline rend le livre, capture des screenshots de pages représentatives, soumet au LLM-judge qui critique la mise en page, traduit le feedback en ajustements de configuration, et re-rend jusqu'à atteindre un seuil de qualité. Le pipeline génère l'ensemble des livrables KDP : PDF print (intérieur + couverture complète avec dos calculé), EPUB Kindle, et couverture optimisée pour la miniature Amazon 150px.

### Ce qui rend BookForge spécial

L'insight fondamental : les LLM multimodaux permettent pour la première fois d'automatiser le jugement esthétique — le dernier verrou de l'auto-édition professionnelle. BookForge applique un regard critique adaptatif là où les outils existants appliquent des règles statiques.

**Critère de réussite ultime :** Le résultat est indistinguable d'un livre d'éditeur traditionnel (test "Eyrolles sur l'étagère"). Il ne doit pas avoir l'air généré par IA.

**Avantage compétitif :** L'expertise d'un spécialiste pub Amazon encodée dans les design tokens et les critères du LLM-judge, garantissant que le rendu correspond à ce qui convertit sur le marché KDP.

## Classification du projet

| Critère | Valeur |
|---|---|
| **Type** | Content production pipeline (contrainte YAGNI) |
| **Scope** | Automated book production (Markdown -> PDF/EPUB/couverture KDP) |
| **Domaine** | Digital publishing KDP |
| **Complexité** | High sur le chemin critique (rendu pro + boucle LLM-judge), low-medium sur le reste |
| **Contexte** | Greenfield — contraintes de design issues de prototypes (Typst, Matplotlib 300 DPI, plan.yaml) |
| **QA** | Deux couches : checks objectifs programmatiques + critique subjective LLM multimodal |

## Critères de succès

### Succès utilisateur

- **Test de l'étagère :** Le PDF est visuellement indistinguable d'un livre d'éditeur professionnel
- **Test anti-IA :** Le rendu ne peut pas être identifié comme généré par IA ou auto-édité
- **Zéro retouche (cible MVP1+) :** Aucune intervention manuelle entre la commande et l'upload KDP
- **Couverture qui convertit (MVP1+) :** Lisible et attractive en miniature 150px sur Amazon
- **Gain de qualité perçue :** Amélioration notable dès MVP0 — si pas de gain perçu, le projet est un échec

### Succès business

- **Publication effective (MVP1) :** Au moins un livre complet publié sur KDP via BookForge
- **Ventes maintenues ou améliorées :** Le taux de conversion Amazon ne régresse pas
- **Temps de production réduit :** Cycle Markdown -> livre publiable plus court que le process actuel

### Succès technique

- **Fiabilité :** < 5 erreurs de mise en page par livre de 200 pages. Zéro erreur bloquante
- **Coût LLM maîtrisé (MVP2) :** < 0.50$ par livre via sampling intelligent
- **Performance :** Pipeline complet en < 10 minutes pour 200 pages
- **Convergence LLM-judge (MVP2) :** Le score qualité augmente entre itérations. Fallback N appels manuels si la boucle auto ne converge pas

### Résultats mesurables

| Métrique | Seuil d'échec | MVP0 | MVP1 | MVP2 | Vision |
|---|---|---|---|---|---|
| Qualité perçue vs ancien process | Pas de gain | Gain notable | Pro | Pro + itéré | Indistinguable éditeur |
| Erreurs mise en page / 200 pages | > 10 | < 10 | < 5 | < 2 | 0 |
| Couverture lisible 150px | - | Template statique | Oui | Oui | Optimisée taux de clic |
| Coût LLM par livre | > 2$ | 0$ | < 0.50$ (manuel) | < 0.50$ (auto) | < 0.20$ |
| Intervention manuelle | Autant qu'avant | Corrections attendues | Corrections mineures | Minimales | Zéro |
| Temps de génération (200p) | > 30 min | < 5 min | < 10 min | < 10 min | < 3 min |

## Parcours utilisateur

### Parcours 1 — Du Markdown au KDP (happy path)

L'auteur a terminé son manuscrit business en Markdown : 45 fichiers, 180 pages, 12 chapitres. Les diagrammes Matplotlib sont générés. Le `book.yaml` est prêt.

`python bookforge.py book.yaml` — 2-3 minutes plus tard, le dossier `output/` contient `livre-interieur.pdf`, `couverture-complete.pdf`, `couverture-kindle.jpg`. L'auteur feuillette le PDF : TDM cliquable, pages de garde, texte aéré, diagrammes nets, encadrés détachés. Upload direct sur KDP sans retouche.

**Moment critique :** L'ouverture du PDF. Si "wow" = succès. Si "bof" = échec.

### Parcours 2 — Itération (le rendu n'est pas parfait)

L'auteur repère des problèmes (diagramme trop large, titre collé, sous-titre de couverture trop petit). En MVP0-MVP1 : ajuste les tokens/template, relance, recheck. En MVP2 : `--judge` déclenche le LLM qui identifie et corrige automatiquement.

**Moment critique :** Plus de 2-3 boucles manuelles = friction excessive.

### Parcours 3 — Réutilisation (nouveau livre)

2 mois plus tard, nouveau manuscrit business. Copie le `book.yaml`, change titre/auteur/chapitres. Même qualité immédiatement grâce à la classe `business-manual` et aux tokens.

**Moment critique :** Si tout est à re-tuner = pas de valeur durable.

### Parcours 4 — Edge case (contenu problématique)

Tableau 8 colonnes, diagramme pleine page, chapitre de 3 pages. Le pipeline gère gracieusement : fallback image pour tableaux larges, protection contre coupure pour diagrammes, adaptation pour petits chapitres. Jamais de crash silencieux — warnings explicites.

### Parcours 5 — Publication multilingue [Vision]

Le livre business français se vend bien. L'auteur veut publier une édition anglaise sur le marché US. Dans `book.yaml`, il ajoute `targets: ["en"]`. `python bookforge.py book.yaml --lang en` traduit le Markdown via LLM, adapte les conventions typographiques (guillemets droits, pas d'espace insécable avant ponctuation), régénère les diagrammes avec labels traduits, ajuste titre et sous-titre de couverture, et produit le jeu complet PDF + EPUB + couverture en anglais.

**Moment critique :** Si la traduction casse la mise en page (titre trop long, tableau élargi) ou produit un résultat linguistiquement amateur = échec.

### Capacités révélées par les parcours

| Parcours | Capacités requises |
|---|---|
| Happy path | Pipeline bout-en-bout, couv/4e couv, TDM, pages de garde, `book.yaml` config unique |
| Itération | Preview rapide, tokens éditables, LLM-judge, boucle feedback |
| Réutilisation | Classe réutilisable, tokens persistants, `book.yaml` seul point de personnalisation |
| Edge cases | Gestion gracieuse, logging/warnings |
| Multilingue | Traduction LLM, adaptation typo par langue, couverture/diagrammes localisés |

## Innovation & Patterns Novateurs

### Zones d'innovation

**Innovation principale : La vitesse comme arme concurrentielle.**
BookForge inverse le calendrier de publication : vendredi manuscrit -> lundi sur Amazon. La vitesse est la proposition de valeur n°1, la qualité pro est le pré-requis.

**Innovation technique : LLM-as-Art-Director (couche optionnelle).**
Un LLM multimodal juge et critique le rendu visuel, traduit son jugement en ajustements paramétriques. Architecturalement, le pipeline produit un bon résultat sans le LLM — le LLM l'améliore.

**Innovation structurelle : Book-as-Code.**
Livre décrit par `book.yaml` + Markdown sémantique, versionnable, reproductible, 100% déterministe.

**Innovation design : Design-tokens-for-books.**
Concept de design tokens du web transféré à l'édition print. Set fini de 15-20 tokens pilotant une bibliothèque fermée de micro-templates.

### Ordre d'implémentation

1. **Book-as-Code** (fondation — MVP0)
2. **Design tokens** (configuration — MVP1)
3. **LLM-as-Art-Director** (couche optionnelle — MVP2)

### Paysage concurrentiel

| Catégorie | Concurrents | BookForge |
|---|---|---|
| Outils de conversion | Pandoc, Typst, LaTeX | Qualité pro out-of-the-box |
| Apps auto-édition | Atticus, Vellum, Reedsy | Pipeline automatisé, Markdown-in |
| Services de design | 99designs, Fiverr | Minutes au lieu de jours |
| Templates | Canva, BookBolt | Reproductible, paramétrique |
| Consulting pub | Accompagnement auto-édition | Expertise encodée dans tokens + LLM |

**Positionnement :** Compresseur de temps — la qualité d'un éditeur pro à la vitesse d'un script.

### Approche de validation

| Innovation | Validation | Groupe témoin | Fallback |
|---|---|---|---|
| Vitesse | Temps manuscrit -> livre KDP-ready (cible < 30 min) | Process actuel | - |
| Book-as-Code | Publier un livre piloté par book.yaml | - | Paramètres en dur |
| Design tokens | Comparer rendu tokens vs hardcodé, même contenu | Template Typst brut | Template classique |
| LLM-Art-Director | Comparer avec vs sans LLM, mêmes tokens | Livre sans LLM | N appels manuels |

### Risques et mitigations

| Risque | Mitigation |
|---|---|
| LLM-judge : biais systématique | Varier prompts, auditer sur 5+ livres |
| LLM-judge : hallucinations | Score confiance + max 3 itérations + fallback manuel |
| LLM-judge : écrase l'intention auteur | LLM ne modifie que les tokens, jamais le contenu |
| Design tokens trop limité | 15-20 tokens + escape hatch Typst |
| Book-as-Code non-déterministe | Tests régression visuels (screenshot diff) |
| API LLM indisponible | Mode offline-first |

## Exigences techniques

### Architecture du pipeline

```
Entrée (Markdown)
  → Parser (Markdown + extensions sémantiques)
    → AST intermédiaire
      → Renderer PDF (Typst, fallback HTML/CSS headless)
      → Renderer EPUB (Pandoc MVP0, ebooklib si nécessaire)
        → Post-processing (couverture, TDM, pages de garde)
          → QA (checks programmatiques + LLM-judge optionnel)
            → Export (PDF KDP + EPUB Kindle)
```

### Décisions techniques

| Décision | MVP0 | MVP1+ | Porte ouverte |
|---|---|---|---|
| Moteur PDF | Typst | Typst | HTML/CSS headless |
| Moteur EPUB | Pandoc | Pandoc | ebooklib |
| Format d'entrée | Markdown standard | Markdown + `:::` | RST, AsciiDoc |
| Diagrammes | Matplotlib PNG 300 DPI | idem | SVG |
| Formats sortie | PDF KDP + EPUB Kindle | idem | - |
| LLM API | - | Gemini Vision | Claude, GPT-4o, local |
| Config | `book.yaml` | idem | - |
| Fallback EPUB | Éléments déjà en image | Headless: HTML -> PDF -> PNG | - |

### Contraintes

- Python >= 3.10, Typst (standalone), Pandoc, Matplotlib
- Installation : `pip install` + Typst + Pandoc. Pas de GTK/Pango/Cairo
- Mode offline-first : PDF + EPUB sans appel réseau

### Stratégie double export

| Aspect | PDF (KDP print) | EPUB (Kindle) |
|---|---|---|
| Layout | Fixed | Reflowable |
| Diagrammes | Typst natif | Images PNG intégrées |
| Tableaux | Rendu Typst | Max 4 colonnes, sinon fallback image |
| TDM | Numéros de page | Liens cliquables |
| Couverture | Couv + dos + 4e | Couverture seule |

### Tests de sortie (dès MVP0)

- PDF valide, EPUB valide (epubcheck), images >= 300 DPI, snapshot testing

## Scoping & Développement phasé

### Stratégie MVP

Validation technique progressive. Chaque gate est une comparaison mesurable. Ressources : JM seul + Claude Code.

### MVP0 — "Un PDF en main" (~2 semaines)

**Jour 1-2 : Spike technique**
- Tester Typst avec les vrais fichiers Markdown
- Identifier frictions (chemins images, encodage, version Typst)

**Jour 3-10 : Implémentation**
- `book.yaml` comme point d'entrée unique
- Markdown -> Typst template hardcodé -> PDF
- TDM auto, pages de garde basiques, pages liminaires (titre, copyright)
- En-têtes/pieds de page (titre livre, chapitre, numéro de page)
- Couverture template statique
- Export métadonnées KDP (description, mots-clés)
- Validation des entrées + messages d'erreur
- Progression pipeline visible
- Dossier de sortie structuré
- Polices embarquées

**Hors scope :** EPUB, design tokens YAML, balises sémantiques, 4e de couv, LLM, ISBN

**Gate :** Comparaison côte-à-côte — même contenu, ancien process vs BookForge. Résultat visiblement meilleur.

### MVP0.5 — "Dual export" (~3-4 jours)

- Export EPUB via Pandoc + CSS Kindle basique + métadonnées EPUB complètes
- **Gate :** PDF + EPUB en une commande, les deux utilisables

### MVP1 — "Publiable KDP" (~2 semaines)

- Design tokens YAML, balises sémantiques (`:::framework`, `:::callout`)
- Couverture paramétrique, 4e de couv (pitch statique + dos calculé + ISBN)
- LLM-judge mode manuel, classe `business-manual`, numérotation romaine/arabe
- Pages finales optionnelles, miniature couverture 150px, escape hatch Typst
- **Gate :** Livre publié sur KDP, qualité >= livres précédents de JM

### MVP2 — "Pipeline intelligent" (~2 semaines)

- Boucle LLM-judge automatisée (fallback manuel), pitch 4e couv LLM
- Checks QA programmatiques, preview 5 pages, snapshot testing, coût LLM reporté
- **Gate :** Pipeline autonome, coût < 0.50$/livre

### Growth

- Hot reload, classes additionnelles (`fiction-novel`, `technical-guide`)
- Polish auto (lettrines, filets, ornements), preview multi-format, migration ebooklib
- Identité de collection réutilisable

### Vision

- Traduction LLM au build, web app, A/B testing couvertures, scraping Amazon, versioning livres

### Risques

| Risque | Mitigation |
|---|---|
| Typst ne produit pas un rendu pro | Spike jour 1-2. Pivot HTML/CSS headless |
| Boucle LLM ne converge pas | Fallback N appels manuels |
| EPUB casse sur certains contenus | Limiter complexité + fallback image |
| Dépendances cachées | Spike technique jour 1-2 |
| Pas de gain de ventes | Reste un gain de temps |
| JM seul, temps limité | Gates strictes, chaque MVP autonome |

## Exigences fonctionnelles

### Configuration & entrée

- **FR1 :** L'auteur peut définir un livre via `book.yaml` (titre, sous-titre, auteur, genre, chapitres, ISBN)
- **FR2 :** L'auteur peut fournir le contenu en fichiers Markdown standard
- **FR3 :** L'auteur peut utiliser des balises sémantiques (`:::framework`, `:::callout`, `:::chapter-summary`) [MVP1]
- **FR4 :** L'auteur peut référencer des images et diagrammes depuis le Markdown
- **FR5 :** Le système peut valider les entrées (`book.yaml`, Markdown, assets) avec messages d'erreur explicites [MVP0]

### Rendu intérieur

- **FR6 :** Le système peut transformer du Markdown en PDF avec typographie conforme aux standards éditoriaux (espaces insécables, ligatures, césure automatique, interligne 120-140% du corps)
- **FR7 :** Le système peut générer une table des matières depuis les headings Markdown
- **FR8 :** Le système peut générer des pages de garde de chapitre
- **FR9 :** Le système peut intégrer images et diagrammes sans coupure de page, redimensionnés et centrés automatiquement
- **FR10 :** Le système peut rendre encadrés et frameworks visuellement distincts du texte [MVP1]
- **FR11 :** Le système peut appliquer une classe de document (`business-manual`) [MVP1]
- **FR12 :** Le système peut générer les pages liminaires (titre, copyright, dédicace optionnelle) [MVP0]
- **FR13 :** Le système peut générer des en-têtes/pieds de page configurables (titre livre, chapitre, numéro) [MVP0]
- **FR14 :** Le système peut appliquer une numérotation différenciée (romaine liminaires, arabe corps) [MVP1]

### Export multi-format

- **FR15 :** Le système peut exporter en PDF valide conforme KDP print-on-demand
- **FR16 :** Le système peut exporter en EPUB conforme aux spécifications EPUB 3.x, avec métadonnées complètes, compatible Kindle [MVP0.5]
- **FR17 :** Le système peut rendre tous les éléments lisibles dans l'EPUB [MVP0.5]
- **FR18 :** Le système peut produire PDF + EPUB en une seule commande [MVP0.5]
- **FR19 :** Le système peut exporter les métadonnées KDP (description, mots-clés, catégories) prêtes à copier-coller [MVP0]

### Couverture & 4e de couverture

- **FR20 :** Le système peut générer une couverture depuis un template paramétrique
- **FR21 :** Le système peut générer une 4e de couverture (pitch, bio, code-barres ISBN) [MVP1]
- **FR22 :** Le système peut calculer la largeur du dos selon le nombre de pages [MVP1]
- **FR23 :** Le système peut assembler couverture + dos + 4e en image complète KDP [MVP1]
- **FR24 :** Le système peut générer une miniature couverture 150px pour vérification [MVP1]

### Design tokens & personnalisation

- **FR25 :** L'auteur peut personnaliser le rendu via design tokens YAML [MVP1]
- **FR26 :** L'auteur peut choisir une classe de document pré-chargeant un jeu de tokens [MVP1]
- **FR27 :** L'auteur peut surcharger ponctuellement le rendu via des instructions natives du moteur de rendu (escape hatch) [MVP1]

### LLM-judge & qualité

- **FR28 :** L'auteur peut soumettre des screenshots au LLM-judge et recevoir un feedback actionnable [MVP1]
- **FR29 :** Le système peut exécuter une boucle LLM-judge automatisée avec limite d'itérations [MVP2]
- **FR30 :** Le système peut fonctionner entièrement sans LLM (mode offline) [MVP0]

### QA & validation

- **FR31 :** Le système peut vérifier que les images sont >= 300 DPI
- **FR32 :** Le système peut détecter les erreurs de mise en page (orphelines/veuves, images débordant des marges, tableaux tronqués, titres isolés en bas de page) et émettre des warnings [MVP2]
- **FR33 :** Le système peut reproduire un rendu identique à partir des mêmes entrées [MVP0]
- **FR34 :** Le système peut embarquer les polices dans PDF et EPUB [MVP0]

### Preview, itération & sortie

- **FR35 :** L'auteur peut générer un preview rapide sur 5 pages représentatives [MVP2]
- **FR36 :** L'auteur peut relancer le pipeline après modification et voir le résultat mis à jour
- **FR37 :** Le système peut afficher la progression du pipeline (étape, pourcentage) [MVP0]
- **FR38 :** Le système peut organiser la sortie dans un dossier structuré avec noms explicites [MVP0]

### Logging & feedback

- **FR39 :** Le système peut logger warnings et erreurs dans un format structuré (timestamp, sévérité warn/error, composant source, message descriptif)
- **FR40 :** Le système peut reporter le coût LLM par livre [MVP2]

### Pages finales

- **FR41 :** Le système peut intégrer des pages finales optionnelles (bibliographie, "du même auteur", remerciements) [MVP1]

### Polish automatique

- **FR42 :** Le système peut appliquer des éléments de polish (lettrines, filets, ornements) selon la classe [Growth]

### Multi-langue & traduction

- **FR43 :** L'auteur peut spécifier langue source et cibles dans `book.yaml` [Vision]
- **FR44 :** Le système peut traduire le Markdown via LLM au build [Vision]
- **FR45 :** Le système peut adapter les conventions typographiques à la langue cible [Vision]
- **FR46 :** Le système peut générer couverture et 4e de couv dans la langue cible [Vision]
- **FR47 :** Le système peut régénérer les diagrammes avec labels traduits [Vision]

### Interface CLI

- **FR49 :** L'auteur peut lancer le pipeline via une commande unique acceptant le chemin vers `book.yaml` et des options (`--lang`, `--judge`, `--preview`) [MVP0]
- **FR50 :** Le système peut retourner des codes de sortie distincts (0 = succès, 1 = erreur d'entrée, 2 = erreur de rendu, 3 = erreur LLM) [MVP0]
- **FR51 :** Le système peut produire un output machine-readable (JSON) avec le statut, les chemins de sortie et les warnings pour usage scripté [MVP1]

### Identité de collection

- **FR48 :** L'auteur peut définir une identité de collection réutilisable entre livres [Growth]

## Exigences non-fonctionnelles

### Performance

- **NFR1 :** Pipeline Markdown -> PDF en < 5 minutes pour 200 pages (hors LLM)
- **NFR2 :** Boucle LLM-judge en < 10 minutes total (max 3 itérations)
- **NFR3 :** Preview 5 pages en < 10 secondes
- **NFR4 :** Export EPUB en < 2 minutes pour 200 pages

### Fiabilité & reproductibilité

- **NFR5 :** Résultat identique bit-for-bit pour mêmes entrées (hors LLM)
- **NFR6 :** Jamais de crash silencieux — erreur loggée, arrêt propre
- **NFR7 :** Tests régression visuels (snapshot diff) détectent toute modification

### Intégration

- **NFR8 :** Fonctionne entièrement offline. LLM = couche optionnelle
- **NFR9 :** Coût LLM < 0.50$ par livre (sampling 5-10 pages)
- **NFR10 :** Tolère indisponibilité API LLM sans bloquer l'export

### Maintenabilité

- **NFR11 :** Modules indépendants (parser, renderer PDF, renderer EPUB, cover, LLM-judge) testables isolément
- **NFR12 :** Ajout de renderer/format sans modifier le code existant
- **NFR13 :** Dépendances externes < 5 runtime (hors dev/test) et versionnées

### Portabilité

- **NFR14 :** Fonctionne sur Windows, macOS et Linux
- **NFR15 :** Installation en 3 commandes maximum
