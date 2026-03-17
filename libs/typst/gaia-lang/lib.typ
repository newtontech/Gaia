// v1 (kept for backwards compatibility)
#import "module.typ": module, use, package, export-graph
#import "knowledge.typ": claim as v1-claim, setting as v1-setting, question as v1-question, contradiction, equivalence
#import "chain.typ": chain

// v2
#import "declarations.typ": claim, setting, question, observation, claim_relation
#import "tactics.typ": premise, derive, contradict, equate
