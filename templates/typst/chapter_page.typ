// Template page de garde de chapitre — BookForge (Story 2.5)
// Reference seulement — le code inline dans pdf.py est la source de verite.
//
// Pattern genere par _render_chapter_title_page() :
//
// #pagebreak(weak: true)
// #align(center + horizon)[
//   #text(size: 28pt, weight: "bold")[Titre du Chapitre]
// ] <chapter-start>
// #pagebreak()
//
// Le label <chapter-start> est utilise par le header context pour
// supprimer l'en-tete sur les pages de garde de chapitre.
