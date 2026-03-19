#import "../../../../libs/typst/gaia-lang/v2.typ": *

#module("prior_knowledge", title: "先验知识")

#observation("eotvos_experiment")[
  Eötvös 1889 年扭摆实验以 $10^(-9)$ 精度验证：
  物体的惯性质量 $m_i$（决定对力的响应）
  与引力质量 $m_g$（决定所受引力大小）在实验可区分范围内相等。
  $ frac(m_i - m_g, m_i) < 10^(-9) $
]

#claim("maxwell_electromagnetism")[
  麦克斯韦电磁理论：光是电磁波，
  在真空中以恒定速度 $c$ 传播，与光源运动状态无关。
]

#claim("soldner_deflection")[
  Soldner 1801 年基于牛顿力学将光视为质点（微粒说），
  计算得光线掠过太阳表面时偏折：
  $ theta_"Newton" = frac(2 G M_(dot.o), c^2 R_(dot.o)) approx 0.87'' $
]
