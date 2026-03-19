#import "../../../../libs/typst/gaia-lang/lib.typ": *

#module("derivation", title: "推导 — 从牛顿定律推导出 a = g")

#use("laws.second_law")
#use("laws.law_of_gravity")
#use("laws.mass_equivalence")
#use("laws.near_earth_surface")

#chain("force_equating_chain")[
  #claim("force_equation_result",
    premise: ("second_law", "law_of_gravity", "mass_equivalence"),
  )[
    由牛顿第二定律得 F = m_i × a；由万有引力定律得 F = m_g × g。
    因为作用在同一物体上的合力相等，所以 m_i × a = m_g × g。
    又因 m_i = m_g，两边约去质量，得 a = g。
    加速度只取决于引力场强度 g，与物体质量完全无关。
  ]
]

#chain("mass_independence_chain")[
  #claim("acceleration_independent_of_mass",
    premise: ("force_equation_result",),
  )[
    在同一引力场中，无论物体质量多大，
    其自由落体加速度都相同。这不是经验归纳，而是从基本定律出发的
    纯理论推导。
  ]
]
