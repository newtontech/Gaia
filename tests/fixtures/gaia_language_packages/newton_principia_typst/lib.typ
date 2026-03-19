#import "../../../../libs/typst/gaia-lang/lib.typ": *
#include "motivation.typ"
#include "laws.typ"
#include "derivation.typ"
#include "implications.typ"

#package("newton_principia",
  modules: ("motivation", "laws", "derivation", "implications"),
  export: (
    "law_of_gravity",
    "acceleration_independent_of_mass",
    "newton_contradicts_aristotle",
    "two_path_rejection_of_aristotle",
    "galileo_equivalence",
  ),
)

#export-graph()
