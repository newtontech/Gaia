#import "../../../../libs/typst/gaia-lang/v2.typ": *
#show: gaia-style

#package("newton_principia",
  title: "牛顿万有引力推导",
  author: "Isaac Newton",
  version: "3.0.0",
  date: "1687 · Philosophiæ Naturalis Principia Mathematica",
  abstract: [从运动定律（公理）与开普勒行星观测出发，经四步推导得出万有引力定律、
    惯性质量与引力质量等价，以及自由落体加速度与物体质量无关。],
  modules: ("motivation", "axioms", "observations", "derivation", "follow_up"),
  export: (
    "freefall_acceleration_equals_g",
    "law_of_gravity",
    "mass_equivalence",
    "galileo_newton_convergence",
    "apollo15_confirms_equal_fall",
    "apollo_galileo_convergence",
    "follow_up_question",
  ),
)

#include "motivation.typ"
#include "laws.typ"
#include "observations.typ"
#include "derivation.typ"
#include "follow_up.typ"

#export-graph()
