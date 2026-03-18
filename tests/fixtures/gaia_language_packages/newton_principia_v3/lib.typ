#import "../../../../libs/typst/gaia-lang/v2.typ": *

#include "motivation.typ"
#include "laws.typ"
#include "derivation.typ"
#include "follow_up.typ"

#package("newton_principia",
  modules: ("motivation", "laws", "derivation", "follow_up"),
  export: (
    "freefall_acceleration_equals_g",
    "follow_up_question",
  ),
)

#export-graph()
