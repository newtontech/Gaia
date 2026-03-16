#import "knowledge.typ": _chain_active, _chain_pipeline, _chain_name, _chain_step_index

#let chain(name, body) = {
  // Activate chain context
  _chain_active.update(_ => true)
  _chain_pipeline.update(_ => none)
  _chain_name.update(_ => name)
  _chain_step_index.update(_ => 0)

  // Render chain heading
  block(above: 1em)[
    == Chain: #name
    #body
  ]

  // Deactivate chain context
  _chain_active.update(_ => false)
  _chain_pipeline.update(_ => none)
  _chain_name.update(_ => none)

  name  // return chain name as handle
}
