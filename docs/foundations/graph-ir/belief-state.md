# BeliefState — 信念定义

> **Status:** Target design

BeliefState 是 BP 的**纯输出**——后验信念值。它绑定到产生它的特定 Graph IR 结构和 Parameterization。

Graph IR 结构定义见 [graph-ir.md](graph-ir.md)。概率参数见 [parameterization.md](parameterization.md)。三者的关系见 [overview.md](overview.md)。

## Schema

```
BeliefState:
    graph_hash:              str         # 绑定到哪个图结构
    parameterization_hash:   str         # 绑定到哪个参数化
    bp_run_id:               str         # 唯一运行 ID
    scope:                   str         # "local" | "global"

    # ── 信念 ──
    beliefs:                 dict[str, float]   # 以 knowledge node ID 为键
                                                 # 只有 type=claim 的节点有 belief

    # ── 诊断 ──
    converged:               bool
    iterations:              int
    max_residual:            float
```

## 关键规则

- **beliefs 只对 Claim**：只有 `type=claim` 的节点有 belief，与 Parameterization 中的 `node_priors` 对应。Setting、Question、Template 没有 belief。
- **双重绑定**：通过 `graph_hash + parameterization_hash` 绑定到产生它的结构和参数。如果图结构或参数化发生变化，BeliefState 失效。
- **可多次运行**：同一参数化可以有多次 BP 运行（不同调度策略、阻尼系数等），每次产出不同的 BeliefState。
- **belief 是后验**：belief 是 BP 计算后的后验信念值，不是 prior。prior 在 Parameterization 中，belief 在 BeliefState 中。

## Local vs Global

| | Local | Global |
|---|---|---|
| **范围** | 单个包内的 claim | 所有已摄入包的全局 claim |
| **ID 命名空间** | `lcn_` | `gcn_` |
| **产生者** | `gaia infer`（本地 BP） | LKM global BP |
| **用途** | 作者本地预览 | 全局知识体系的权威信念 |

## 诊断字段

- `converged`：BP 是否在容差内收敛
- `iterations`：实际运行的迭代数
- `max_residual`：停止时的最大消息变化量

这些字段用于判断 belief 的可靠性。未收敛的 BeliefState 仍然有效，但应标记为近似值。

## 源代码

- `libs/inference/bp.py` -- `BeliefPropagation.run()` 产出 beliefs
- `libs/storage/models.py` -- `BeliefSnapshot`
