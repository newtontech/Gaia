#import "../../../../libs/typst/gaia-lang/v2.typ": *

#module("galileo", title: "伽利略的论证")

// ── Cross-module imports ──
#use("aristotle.heavier_falls_faster")
#use("setting.thought_experiment_env")

// ── Observations (no proof needed) ──
#observation("medium_density_observation")[
  在水、油、空气等不同介质中比较轻重物体的下落，
  会发现介质越稠密，速度差异越明显；介质越稀薄，差异越不明显。
]

#observation("inclined_plane_observation")[
  伽利略的斜面实验把下落过程放慢到可测量尺度后显示：
  不同重量的小球在相同斜面条件下呈现近似一致的加速趋势，
  与"重量越大速度越大"的简单比例律并不相符。
]

// ── Fine-grained tied-ball decomposition ──
#claim("composite_is_slower")[
  由假设，轻球天然比重球慢，轻球应拖慢重球，
  所以复合体 HL 速度应慢于 H。
][
  #premise("heavier_falls_faster")
  #premise("thought_experiment_env")

  在假设"重者更快"的前提下 @heavier-falls-faster ，
  将轻球绑在重球上相当于附加了阻力。
  因此复合体的速度应介于二者之间，慢于重球单独下落。
]

#claim("composite_is_faster")[
  但复合体 HL 总重量大于 H，
  按同一定律应比 H 更快。
][
  #premise("heavier_falls_faster")
  #premise("thought_experiment_env")

  同样依据"重者更快" @heavier-falls-faster ，
  复合体的总质量 = H + L > H，
  因此预测其下落速度应比 H 更快。
]

#claim_relation("tied_balls_contradiction",
  type: "contradiction",
  between: ("composite_is_slower", "composite_is_faster")
)[两个预测由同一前提推出却互相矛盾，假设不自洽。]

// ── Medium elimination ──
#claim("air_resistance_is_confound")[
  日常观察到的速度差异更应被解释为介质阻力造成的表象，
  而不是重量本身决定自由落体速度的证据。
][
  #premise("medium_density_observation")

  如果速度差异由介质阻力造成，那么介质越稀薄差异越小。
  实验中恰好观察到了这一规律 @medium-density-observation ，
  说明介质阻力是更好的解释。
]

// ── Final synthesis ──
#claim("vacuum_prediction")[
  在真空中，不同重量的物体应以相同速率下落。
][
  #premise("tied_balls_contradiction")
  #premise("air_resistance_is_confound")
  #premise("inclined_plane_observation")

  + 绑球思想实验表明旧定律自相矛盾 @tied-balls-contradiction 。
  + 日常观察到的速度差异实为介质阻力的表象 @air-resistance-is-confound 。
  + 斜面实验从正面提供了等速趋势的证据 @inclined-plane-observation 。

  三条独立线索汇聚，在真空中结论成立。
]
