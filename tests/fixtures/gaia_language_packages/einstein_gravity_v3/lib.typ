#import "../../../../libs/typst/gaia-lang/v2.typ": *
#show: gaia-style

#include "prior_knowledge.typ"
#include "equivalence_principle.typ"
#include "general_relativity.typ"
#include "observation.typ"
#include "follow_up.typ"

#package("einstein_gravity",
  modules: ("prior_knowledge", "equivalence_principle", "general_relativity", "observation", "follow_up"),
  export: (
    "equivalence_principle",
    "gr_light_deflection",
    "deflection_contradiction",
    "eddington_confirms_gr",
    "apollo15_confirms_equal_fall",
    "gravitational_waves_question",
  ),
)

#export-graph()
