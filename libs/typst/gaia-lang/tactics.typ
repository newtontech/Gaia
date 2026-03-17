#import "declarations.typ": _proof_active, _proof_conclusion
#import "module.typ": _gaia_proof_premises, _gaia_proof_steps

// ── premise: declare an independent premise (noisy-AND input edge) ──
// Must be inside a proof block. Pushes (conclusion, name) to global accumulator.
#let premise(name) = context {
  let active = _proof_active.get()
  if not active {
    text(fill: red)[⚠ premise used outside proof block]
  } else {
    let concl = _proof_conclusion.get()
    _gaia_proof_premises.update(p => { p.push((concl, name)); p })
    _gaia_proof_steps.update(s => {
      s.push((concl, (tactic: "premise", name: name)))
      s
    })
    block(inset: (left: 1em))[
      — *Premise:* #ref(label(name.replace("_", "-")))
    ]
  }
}

// ── derive: derive intermediate conclusion (invisible to factor graph) ──
// NOTE: Uses ref(label(...)) for dynamic references — @label syntax requires literals.
#let derive(name, body) = context {
  let active = _proof_active.get()
  if not active {
    text(fill: red)[⚠ derive used outside proof block]
  } else {
    let concl = _proof_conclusion.get()
    _gaia_proof_steps.update(s => {
      s.push((concl, (tactic: "derive", name: name, content: body)))
      s
    })
    block(above: 0.4em, inset: (left: 1em))[
      *#name.replace("_", " "):* #body #label(name.replace("_", "-"))
    ]
  }
}

// ── contradict: annotate contradiction between two derives (narrative only) ──
#let contradict(a, b) = context {
  let active = _proof_active.get()
  if not active {
    text(fill: red)[⚠ contradict used outside proof block]
  } else {
    let concl = _proof_conclusion.get()
    _gaia_proof_steps.update(s => {
      s.push((concl, (tactic: "contradict", between: (a, b))))
      s
    })
    block(above: 0.3em, inset: (left: 1em))[
      ⊥ #ref(label(a.replace("_", "-"))) ↔ #ref(label(b.replace("_", "-")))
    ]
  }
}

// ── equate: annotate equivalence between two derives (narrative only) ──
#let equate(a, b) = context {
  let active = _proof_active.get()
  if not active {
    text(fill: red)[⚠ equate used outside proof block]
  } else {
    let concl = _proof_conclusion.get()
    _gaia_proof_steps.update(s => {
      s.push((concl, (tactic: "equate", between: (a, b))))
      s
    })
    block(above: 0.3em, inset: (left: 1em))[
      ≡ #ref(label(a.replace("_", "-"))) ↔ #ref(label(b.replace("_", "-")))
    ]
  }
}
