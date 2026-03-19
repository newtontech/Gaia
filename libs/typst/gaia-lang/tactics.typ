#import "declarations.typ": _proof_active, _proof_conclusion
#import "module.typ": _gaia_proof_premises

// ── premise: declare an independent premise (noisy-AND input edge) ──
// The ONLY tactic that affects the factor graph.
// Must be inside a proof block. Pushes (conclusion, name) to global accumulator.
#let premise(name) = {
  context {
    let active = _proof_active.get()
    if not active {
      text(fill: red)[premise used outside proof block]
    } else {
      let concl = _proof_conclusion.get()
      _gaia_proof_premises.update(p => { p.push((concl, name)); p })
    }
  }
  block(above: 2pt, below: 2pt, inset: (left: 0.8em))[
    #text(size: 9pt, fill: luma(120))[▸ #name.replace("_", " ")]
  ]
}
