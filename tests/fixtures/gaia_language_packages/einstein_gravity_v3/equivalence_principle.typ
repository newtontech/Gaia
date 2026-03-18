#import "../../../../libs/typst/gaia-lang/v2.typ": *

#module("equivalence_principle", title: "等价原理")

#use("prior_knowledge.eotvos_experiment")
#use("prior_knowledge.maxwell_electromagnetism")

#setting("elevator_env")[
  密闭电梯思想实验：电梯中的观察者无法看到外界，
  需要判断自己是静止在引力场中还是在无引力空间中匀加速上升。
]

#claim("equivalence_principle")[
  爱因斯坦等价原理：在足够小的时空区域内，
  均匀引力场的效应与匀加速参考系的效应不可区分。
][
  #premise("eotvos_experiment")
  #premise("elevator_env")

  Eötvös 实验 @eotvos-experiment 以极高精度表明 m_i = m_g，
  即引力对一切物体施加相同的加速度，与其组成和质量无关。
  在密闭电梯 @elevator-env 中，
  静止于引力场所感受的"重力"
  与无引力空间中匀加速上升所感受的"惯性力"
  对任何局部实验都给出完全相同的结果。
  如果两种情况在原则上不可区分，
  那么引力与加速度在物理上等价。
]

#claim("light_bends_in_gravity")[
  光线在引力场中会发生弯曲。
][
  #premise("equivalence_principle")
  #premise("maxwell_electromagnetism")

  由等价原理 @equivalence-principle ，引力场等价于匀加速参考系。
  在向上匀加速的电梯中，
  水平射入的光束相对电梯地板呈现向下弯曲的路径——
  这是加速参考系中的运动学效应。
  由麦克斯韦理论 @maxwell-electromagnetism ，光是电磁波，
  作为物理实体同样适用等价原理。
  因此在等价的引力场中，光线同样必须弯曲。
]
