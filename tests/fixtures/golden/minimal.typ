// Template Typst de base — BookForge (Story 2.3)
// Format livre 6x9 pouces standard KDP

// Configuration page
#set page(
  width: 6in,
  height: 9in,
  margin: (inside: 2cm, outside: 1.5cm, top: 2.5cm, bottom: 2cm),
)

// Typographie professionnelle (Bringhurst)
#set text(
  font: "New Computer Modern",
  size: 11pt,
  lang: "fr",
  region: "FR",
  hyphenate: true,
)

// Paragraphes
#set par(
  justify: true,
  leading: 1.3em,
  first-line-indent: 1em,
)

// Headings h1-h4
#show heading.where(level: 1): set text(size: 24pt, weight: "bold")
#show heading.where(level: 1): set block(above: 2em, below: 1.2em)

#show heading.where(level: 2): set text(size: 18pt, weight: "bold")
#show heading.where(level: 2): set block(above: 1.8em, below: 1em)

#show heading.where(level: 3): set text(size: 14pt, weight: "bold")
#show heading.where(level: 3): set block(above: 1.4em, below: 0.8em)

#show heading.where(level: 4): set text(size: 12pt, weight: "bold")
#show heading.where(level: 4): set block(above: 1.2em, below: 0.6em)

// --- BEGIN CONTENT ---

= Introduction

Ceci est le contenu du premier chapitre.

== Section 1

Un paragraphe avec du texte explicatif.

#align(center)[#image("PLACEHOLDER_IMAGE_PATH", width: 80%)]

#table(
  columns: 2,
  [Colonne A], [Colonne B],
  [valeur 1], [valeur 2],
  [valeur 3], [valeur 4],
)

