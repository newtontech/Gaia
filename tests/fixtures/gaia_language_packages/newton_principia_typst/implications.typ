#import "../../../../libs/typst/gaia-lang/lib.typ": *

#module("implications", title: "含义 — 牛顿推导与伽利略和亚里士多德的关系")

#use("derivation.acceleration_independent_of_mass")
#use("galileo_falling_bodies.vacuum_prediction")
#use("galileo_falling_bodies.tied_balls_contradiction")
#use("galileo_falling_bodies.heavier_falls_faster")

#equivalence("galileo_equivalence",
  premise: ("acceleration_independent_of_mass", "vacuum_prediction"),
)[
  牛顿从 F=ma 和 F=mg 推导出的"a=g 与质量无关"
  与伽利略从思想实验和经验分析预测的"真空中不同重量物体等速下落"
  在物理含义上等价。
  区别在于：伽利略是经验论证（归谬法 + 介质分析 + 斜面实验），
  牛顿是理论推导（从基本定律出发的演绎）。
]

#contradiction("newton_vs_aristotle",
  premise: ("acceleration_independent_of_mass", "heavier_falls_faster"),
)[
  牛顿的 a=g（加速度与质量无关）直接矛盾于
  亚里士多德的 v∝W（下落速度与重量成正比）。
  前者是理论推导，后者是未经控制的经验归纳。
]

#chain("theoretical_contradiction_chain")[
  #claim("newton_contradicts_aristotle",
    premise: ("acceleration_independent_of_mass", "heavier_falls_faster"),
  )[
    牛顿的 a=g 推导从理论上排除了"下落速度与重量成正比"的可能：
    如果加速度不依赖质量，那么亚里士多德的 v∝W 就不是自然界的规律。
    这与伽利略的归谬法反驳独立，提供了第二条反驳路径。
  ]
]

#chain("two_path_rejection_chain")[
  #claim("two_path_rejection_of_aristotle",
    premise: ("tied_balls_contradiction", "newton_contradicts_aristotle"),
  )[
    亚里士多德落体学说同时遭到两条方法上不同的反驳路径削弱：
    伽利略通过绑球归谬法暴露其内在矛盾，
    牛顿则从更基本的力学定律推导出与之不相容的结果。
    两条路径相互独立地汇聚到同一结论。
  ]
]
