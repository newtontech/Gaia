// Core (shared v1 + v2)
#import "module.typ": module, use, package, export-graph

// v1
#import "knowledge.typ": claim, setting, question, contradiction, equivalence
#import "chain.typ": chain

// v2/v3 — import directly from declarations.typ / tactics.typ
// Not re-exported here to avoid shadowing v1 names.
// Usage: #import "declarations.typ": claim, setting, question, observation, claim_relation
//        #import "tactics.typ": premise
