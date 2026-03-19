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
  // Gaia figures are structural wrappers, not display figures
  show figure.where(kind: "gaia"): set figure(numbering: none)
  // Cross-references show human-readable name instead of figure number
  show ref: it => {
    emph(str(it.target).replace("-", " "))
  }
  body
}
