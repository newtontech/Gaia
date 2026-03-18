#import "../../../../libs/typst/gaia-lang/v2.typ": *

#module("observation", title: "观测验证")

#use("general_relativity.gr_light_deflection")
#use("general_relativity.deflection_contradiction")

#observation("eddington_sobral")[
  1919 年 5 月 29 日日全食期间，巴西 Sobral 观测站测得
  恒星光线经过太阳附近时偏折 1.98 ± 0.16 角秒。
]

#observation("eddington_principe")[
  同一次日全食期间，西非 Príncipe 岛观测站测得
  恒星光线偏折 1.61 ± 0.30 角秒。
]

#observation("apollo15_feather_drop")[
  1971 年 Apollo 15 任务中，宇航员 David Scott 在月球表面（真空环境）
  同时释放一把锤子（1.32 kg）和一根羽毛（0.03 g），
  质量比约 44000:1，两者同时落地。
]

#claim("eddington_confirms_gr")[
  1919 年日食观测数据支持广义相对论的 1.75 角秒光线偏折预测，
  排除牛顿微粒说的 0.87 角秒预测。
][
  #premise("eddington_sobral")
  #premise("eddington_principe")
  #premise("gr_light_deflection")

  Sobral 站测得 1.98 ± 0.16 角秒 @eddington-sobral ，
  与广义相对论预测 1.75 角秒 @gr-light-deflection 一致（偏差 < 2σ），
  与牛顿预测 0.87 角秒偏离约 7σ。
  Príncipe 站测得 1.61 ± 0.30 角秒 @eddington-principe ，
  同样与广义相对论一致（偏差 < 1σ），与牛顿预测偏离约 2.5σ。
  两个独立观测站的结果一致，大幅降低系统误差的可能性。
]

#claim("soldner_prediction_disfavored")[
  在 1919 年日食观测之后，
  Soldner/牛顿的 0.87 角秒光线偏折预测被观测数据显著排除。
][
  #premise("eddington_confirms_gr")
  #premise("deflection_contradiction")

  爱丁顿观测 @eddington-confirms-gr 支持 1.75 角秒（广义相对论）
  而非 0.87 角秒（牛顿）。
  由于两个预测互相矛盾 @deflection-contradiction ，
  支持一方的观测同时构成对另一方的反对证据。
]

#claim("apollo15_confirms_equal_fall")[
  在月球真空条件下，质量相差约四万倍的物体仍然同时落地，
  直接验证自由落体加速度与质量无关。
][
  #premise("apollo15_feather_drop")

  Apollo 15 月面实验 @apollo15-feather-drop 在真正的真空环境中进行，
  锤子与羽毛的质量比约 44000:1。
  在如此极端的质量差异下两者仍然同时落地，
  为"自由落体加速度与质量无关"
  提供了近乎理想条件下的直接经验证据。
]
