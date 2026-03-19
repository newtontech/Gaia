#import "../../../../libs/typst/gaia-lang/v2.typ": *
#show: gaia-style

#package("galileo_falling_bodies",
  title: "伽利略落体论证",
  author: "Galileo Galilei",
  version: "3.0.0",
  date: "1638 · Discorsi e dimostrazioni matematiche",
  abstract: [从亚里士多德的"重者下落更快"出发，通过绑球思想实验揭示其自相矛盾，
    结合斜面实验与介质消除论证，最终推出"真空中一切物体以相同速率下落"。],
  modules: ("motivation", "setting", "aristotle", "galileo", "follow_up"),
  export: (
    "vacuum_prediction",
    "tied_balls_contradiction",
    "follow_up_question",
  ),
)

#include "motivation.typ"
#include "setting.typ"
#include "aristotle.typ"
#include "galileo.typ"
#include "follow_up.typ"

#export-graph()
