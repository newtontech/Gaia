#import "../../../../libs/typst/gaia-lang/v2.typ": *
#show: gaia-style

#package("einstein_gravity",
  title: "爱因斯坦广义相对论与引力",
  author: "Albert Einstein",
  version: "3.0.0",
  date: "1915 · Die Feldgleichungen der Gravitation",
  abstract: [从等价原理出发，经广义相对论场方程推导光线偏折与水星进动两个独立预测，
    以 1919 年日食观测和天文记录分别验证。],
  modules: ("prior_knowledge", "equivalence_principle", "general_relativity", "observation", "follow_up"),
  export: (
    "equivalence_principle",
    "gr_light_deflection",
    "gr_mercury_precession",
    "deflection_contradiction",
    "eddington_confirms_gr",
    "gr_dual_confirmation",
    "gravitational_waves_question",
  ),
)

#include "prior_knowledge.typ"
#include "equivalence_principle.typ"
#include "general_relativity.typ"
#include "observation.typ"
#include "follow_up.typ"

#export-graph()
