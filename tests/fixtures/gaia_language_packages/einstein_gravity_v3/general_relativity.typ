#import "../../../../libs/typst/gaia-lang/v2.typ": *

#module("general_relativity", title: "广义相对论")

#use("equivalence_principle.light_bends_in_gravity")
#use("prior_knowledge.soldner_deflection")

#claim("einstein_field_equations")[
  爱因斯坦场方程 G_μν + Λg_μν = (8πG/c⁴) T_μν：
  引力不是超距力，而是质能分布（T_μν）导致的时空弯曲（G_μν）。
]

#observation("mercury_perihelion")[
  天文观测显示水星近日点每世纪有约 43 角秒的异常进动，
  无法由牛顿引力理论单独解释。
]

#claim("gr_light_deflection")[
  广义相对论预测：光线掠过太阳表面时偏折 1.75 角秒。
][
  #premise("light_bends_in_gravity")
  #premise("einstein_field_equations")

  等价原理已定性预测光线在引力场中弯曲 @light-bends-in-gravity 。
  爱因斯坦场方程 @einstein-field-equations 将引力量化为时空曲率，
  可精确计算光线在太阳引力场中的偏折。
  完整计算包含时间弯曲和空间弯曲两部分贡献，
  结果为 1.75 角秒——
  恰好是 Soldner 仅考虑时间弯曲的牛顿微粒说结果（0.87 角秒）的两倍。
]

#claim_relation("deflection_contradiction",
  type: "contradiction",
  between: ("gr_light_deflection", "soldner_deflection")
)[广义相对论预测光线偏折 1.75 角秒，牛顿微粒说预测 0.87 角秒，两者不能同时正确。]
