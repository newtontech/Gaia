// Global state for collecting all knowledge graph data
#let _gaia_nodes = state("gaia-nodes", ())
#let _gaia_factors = state("gaia-factors", ())
#let _gaia_module_name = state("gaia-module", none)
#let _gaia_refs = state("gaia-refs", ())
#let _gaia_exports = state("gaia-exports", ())

#let module(name, title: none) = {
  _gaia_module_name.update(_ => name)
  // Render module heading
  if title != none {
    heading(level: 1)[#name — #title]
  } else {
    heading(level: 1)[#name]
  }
}

#let use(target) = {
  let alias = target.split(".").last()
  _gaia_refs.update(refs => {
    refs.push((alias: alias, target: target))
    refs
  })
  alias
}

#let package(name, modules: (), export: ()) = {
  _gaia_exports.update(_ => export)
}

#let export-graph() = context {
  [#metadata((
    nodes: _gaia_nodes.final(),
    factors: _gaia_factors.final(),
    refs: _gaia_refs.final(),
    module: _gaia_module_name.final(),
    exports: _gaia_exports.final(),
  )) <gaia-graph>]
}
