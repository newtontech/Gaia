// Gaia Language v2 entry point
// v2 replaces #chain with proof blocks on #claim
// v3 semantics: claim_relation description body is optional (uses ..args pattern)
#import "module.typ": module, use, package, export-graph
#import "declarations.typ": claim, setting, question, observation, claim_relation
#import "tactics.typ": premise

// ── Document style ──
// Apply via `#show: gaia-style` in the package's lib.typ.
// Cannot use show rules in an imported file — they must be in document scope.
#let gaia-style(body) = {
  // Page setup
  set page(margin: (x: 2.5cm, y: 2cm))
  set text(size: 11pt, lang: "zh")
  set par(justify: true, leading: 0.65em)

  // Heading styles — module headings
  show heading.where(level: 1): it => {
    v(0.8em)
    block(width: 100%, below: 0.5em)[
      #text(size: 14pt, weight: "bold")[#it.body]
      #v(0.2em)
      #line(length: 100%, stroke: 0.5pt + luma(200))
    ]
  }
  show heading.where(level: 3): it => {
    v(0.3em)
    text(size: 11.5pt, weight: "bold")[#it.body]
    v(0.2em)
  }

  // Gaia figures are structural wrappers, not display figures
  show figure.where(kind: "gaia"): set figure(numbering: none)
  show figure.where(kind: "gaia"): set block(above: 0.3em, below: 0.3em)

  // Cross-references render as compact pill badges
  show ref: it => {
    let name = str(it.target).replace("-", " ")
    h(1pt)
    box(
      inset: (x: 4pt, y: 1.5pt),
      radius: 3pt,
      fill: rgb("#eff6ff"),
      stroke: 0.5pt + rgb("#bfdbfe"),
    )[#text(size: 8pt, fill: rgb("#1d4ed8"), weight: "medium")[#name]]
    h(1pt)
  }

  body
}
