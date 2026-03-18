#import "../../../../libs/typst/gaia-lang/v2.typ": *

#module("derivation", title: "推导")

#use("laws.second_law")
#use("laws.law_of_gravity")
#use("laws.mass_equivalence")
#use("laws.near_earth_surface")

#claim("freefall_acceleration_equals_g")[
  在地球表面附近，任何物体的自由落体加速度都等于
  g ≈ 9.8 m/s²，与物体质量无关。
][
  #premise("second_law")
  #premise("law_of_gravity")
  #premise("mass_equivalence")
  #premise("near_earth_surface")

  对地球表面附近的自由落体，作用力只有引力。
  由牛顿第二定律 @second-law 得 F = m_i × a；
  由万有引力定律 @law-of-gravity 得 F = G × M × m_g / r²。
  两式描述同一个力，因此 m_i × a = G × M × m_g / r²。
  由惯性质量等于引力质量 @mass-equivalence ，即 m_i = m_g，
  两边约去质量得 a = G × M / r²。
  在地球表面 @near-earth-surface r ≈ R，故 a = G × M / R² = g。
  加速度表达式中不含物体质量，因此自由落体加速度与质量无关。
]
