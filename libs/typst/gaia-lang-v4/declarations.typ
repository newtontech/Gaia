// Gaia v4 — Knowledge declaration functions
// Each returns a single figure(kind: "gaia-node") with hidden metadata.

#let setting(body) = {
  figure(kind: "gaia-node", supplement: "Setting", {
    hide(metadata(("gaia-type": "setting")))
    body
  })
}

#let question(body) = {
  figure(kind: "gaia-node", supplement: "Question", {
    hide(metadata(("gaia-type": "question")))
    body
  })
}

#let claim(from: (), kind: none, body, ..args) = {
  let proof-body = if args.pos().len() > 0 { args.pos().at(0) } else { none }
  figure(kind: "gaia-node", supplement: "Claim", {
    hide(metadata(("gaia-type": "claim", "from": from, "kind": kind)))
    body
    if proof-body != none {
      v(0.3em)
      block(
        inset: (left: 1em, top: 0.5em, bottom: 0.5em),
        stroke: (left: 2pt + gray),
        proof-body,
      )
    }
  })
}

#let action(from: (), kind: none, body, ..args) = {
  let proof-body = if args.pos().len() > 0 { args.pos().at(0) } else { none }
  figure(kind: "gaia-node", supplement: "Action", {
    hide(metadata(("gaia-type": "action", "from": from, "kind": kind)))
    body
    if proof-body != none {
      v(0.3em)
      block(
        inset: (left: 1em, top: 0.5em, bottom: 0.5em),
        stroke: (left: 2pt + gray),
        proof-body,
      )
    }
  })
}

#let relation(type: "contradiction", between: (), body, ..args) = {
  let proof-body = if args.pos().len() > 0 { args.pos().at(0) } else { none }
  let supplement = if type == "contradiction" { "Contradiction" } else { "Equivalence" }
  figure(kind: "gaia-node", supplement: supplement, {
    hide(metadata(("gaia-type": "relation", "rel-type": type, "between": between)))
    body
    if proof-body != none {
      v(0.3em)
      block(
        inset: (left: 1em, top: 0.5em, bottom: 0.5em),
        stroke: (left: 2pt + gray),
        proof-body,
      )
    }
  })
}
