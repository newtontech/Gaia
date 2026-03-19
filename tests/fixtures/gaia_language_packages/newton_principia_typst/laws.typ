#import "../../../../libs/typst/gaia-lang/lib.typ": *

#module("laws", title: "牛顿定律 — 力学基本定律")

#claim("first_law")[
  牛顿第一定律（惯性定律）：不受外力作用的物体保持静止或匀速直线运动。
]

#claim("second_law")[
  牛顿第二定律：物体的加速度与所受合外力成正比、与惯性质量成反比。
  F = m_i × a，其中 m_i 是惯性质量。
]

#claim("third_law")[
  牛顿第三定律（作用与反作用定律）：两个物体之间的力总是大小相等、方向相反。
]

#claim("law_of_gravity")[
  万有引力定律：任意两个物体之间存在引力，大小为 F = G × M × m_g / r²，
  其中 m_g 是引力质量，M 是地球质量，r 是距离，G 是引力常数。
]

#claim("mass_equivalence")[
  惯性质量与引力质量在实验精度范围内相等：m_i = m_g。
  这是一个经验事实，牛顿注意到了它但没有给出理论解释。
]

#setting("near_earth_surface")[
  在地球表面附近，距离 r 近似等于地球半径 R，
  因而引力加速度 g = GM/R² 可视为常数（约 9.8 m/s²）。
]
