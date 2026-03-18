#import "../../../../libs/typst/gaia-lang/v2.typ": *

#module("laws", title: "力学基本定律")

#claim("second_law")[
  牛顿第二定律：物体所受合外力 F 等于其惯性质量 m_i
  与加速度 a 的乘积，即 F = m_i × a。
]

#claim("law_of_gravity")[
  万有引力定律：引力质量为 m_g 的物体受地球（质量 M）的引力为
  F = G × M × m_g / r²，
  其中 r 是物体到地心的距离，G 是引力常数。
]

#claim("mass_equivalence")[
  惯性质量 m_i（决定物体对力的响应）与引力质量 m_g（决定物体所受引力的大小）
  在实验精度范围内相等：m_i = m_g。
]

#setting("near_earth_surface")[
  在地球表面附近，物体到地心的距离 r 近似等于地球半径 R，
  因此引力加速度 g = G × M / R² 可视为常数（约 9.8 m/s²）。
]
