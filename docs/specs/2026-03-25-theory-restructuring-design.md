# Theory 目录重组设计

> **Status:** Design spec
>
> **日期：** 2026-03-25

## 1. 动机

当前 `docs/foundations/theory/` 的四个文档中，noisy-AND 被赋予了过高的理论地位——`belief-propagation.md` 称其为"Jaynes 规则之上唯一的建模假设"。经过从第一性原理的重新审视，我们发现：

1. **因子层面不需要条件概率 p**：在完全形式化的因子图中，所有因子都是逻辑约束，势函数由真值表唯一确定（一致状态 ψ=1，不一致状态 ψ=0）。
2. **p < 1 源于不完全形式化**：条件概率 p < 1 不是"逻辑关系有噪声"，而是推理过程未完全分解的近似。
3. **noisy-AND 不是基本假设**：它是粗因子图中的一种近似模型，可以进一步分解为"合取（p=1）+ 粗推理算子（p<1）"。
4. **Cromwell 规则不属于理论层**：Cromwell 是实用建议，不是 Jaynes 概率论的定理。theory 层不引入 ε。

需要重组文档结构以反映正确的理论层次。

## 2. 理论基础总结

### 2.1 从 Jaynes 到因子图

- **Cox 定理**：概率是唯一一致的不确定性量化方式
- **因子图**：二部图（变量节点 + 因子节点），联合概率 = 各因子势函数的乘积
- **势函数由逻辑确定**：一致状态 ψ=1，不一致状态 ψ=0，无自由参数
- **唯一的自由参数是节点先验 π**

### 2.2 四种原语算子

| 算子 | 一致状态 (ψ=1) | 不一致状态 (ψ=0) | 语义 |
|------|---------------|-----------------|------|
| 蕴含 A→C | (1,1)(0,1)(0,0) | (1,0) | 若 A 则 C |
| 合取 A∧B | (1,1) | (0,0)(0,1)(1,0) | A 且 B 同时成立 |
| 析取 A∨B | (1,1)(1,0)(0,1) | (0,0) | A 或 B 至少一个成立 |
| 否定 A⊕B | (1,0)(0,1) | (1,1)(0,0) | A 和 B 真值互补（二元约束，非一元 NOT） |

**派生算子：**
- 等价 A↔B = 蕴含(A→B) + 蕴含(B→A)
- 矛盾 ¬(A∧B) = 否定(A,¬A) + 蕴含(B→¬A)，其中 ¬A 是辅助变量节点

**多变量推广：**
- 多前提蕴含：[A₁∧...∧Aₙ] → C
- 多变量合取/析取：A₁∧...∧Aₙ / A₁∨...∨Aₙ

**完备性：** 两个二元变量有 16 种真值函数。排除平凡情况后，{→,∧,∨,¬} 覆盖所有非平凡二元约束。

### 2.3 粗推理算子

完全形式化不现实——作者无法总是把推理过程完全分解为逻辑算子。粗推理算子是对未分解推理步骤的近似：

**定义：** 二元因子，输入命题 M，输出命题 C，参数 p ∈ (0,1]。

**势函数：**

| M | C | ψ |
|---|---|---|
| 1 | 1 | 1 |
| 1 | 0 | f(p) |
| 0 | 1 | 1 |
| 0 | 0 | 1 |

**四种状态分析：**
- **(1,1)**：前提成立，结论成立——推理生效，最受偏好。ψ=1。
- **(1,0)**：前提成立，结论不成立——推理失败。p 越大越不被允许。ψ=f(p)，f(1)=0。
- **(0,1)**：前提不成立，结论为真——结论可因其他路径为真，因子不发言。ψ=1。
- **(0,0)**：前提不成立，结论不成立——同上，因子不发言。ψ=1。

**ψ(0,\*)=1 的选择理由：** 最小假设——前提不成立时因子对结论没有意见。

**与 Jaynes 弱三段论的一致性：** 此势函数加上 BP 消息传递，自然产生 C1-C4 行为：
- C1（C 为假 → M 更不可信）✓：反向消息，C belief 低时压低 M
- C2（M 为真 → C 更可信）✓：前向消息，M belief 高时提升 C
- C3（C 为真 → M 更可信）✓：反向消息，C belief 高时 M 的抑制减弱
- C4（M 为假 → C 变弱）✓：前向支持撤回，C 回落到先验

这是满足 C1-C4 的**一种**模型（最小假设选择），不是唯一的。

**p 的含义：**
- p < 1：推理的形式化不完整
- p → 1：粗推理算子收敛为蕴含
- p 是唯一的因子级自由参数

**f(p) 的约束条件：**
- f(1) = 0（p=1 时退化为蕴含，完全禁止 (1,0) 状态）
- f 关于 p 单调递减（p 越大，(1,0) 状态越受抑制）
- 0 ≤ f(p) ≤ 1

f(p) 的具体形式（如 1-p 或 (1-p)/p）留给 bp/ 层定义。

### 2.4 粗推理的分解模式

粗推理算子 + 四种逻辑原语可以表达所有不确定关系：

- **单前提推理**：直接用粗推理 M→C (p<1)
- **多前提联合推理**：合取 A₁∧...∧Aₙ→M (p=1) + 粗推理 M→C (p<1)
- **粗等价**：两个粗推理 A→B (p<1) + B→A (p<1)
- **粗矛盾**：否定(A,¬A) (p=1) + 粗推理 B→¬A (p<1)

### 2.5 粗因子图与细因子图

- **细因子图**：所有因子 p=1（逻辑算子），不确定性完全在节点 belief 中
- **粗因子图**：含粗推理算子（p<1），是对未分解子图的近似
- **细化**：把粗推理算子展开为逻辑算子组合 + 中间命题
- **实践工作流**：先构建粗因子图（捕捉推理骨架），再逐步细化

### 2.6 科学本体论

**知识类型：**
- Claim：可判真的命题，携带先验 π，参与 BP
- Setting：上下文假设，不参与 BP
- Question：开放探究，不参与 BP
- Template：含自由变量的命题模式（v1 暂不暴露）

**关系类型：**
- 等价（equivalence）：双向蕴含
- 矛盾（contradiction）：否定 + 蕴含
- 否定（negation）：原语算子 ¬

**推理策略（七种）——从粗因子图到细因子图的展开模板：**

| 策略 | 类型 | 粗因子图 | 细因子图展开 |
|------|------|---------|-------------|
| Deduction（演绎） | 确定性 | M→C（粗推理） | M→C (p=1，蕴含) |
| Abduction（溯因） | 不确定 | []→H | H→O + O≡O' |
| Induction（归纳） | 不确定 | [A₁..Aₙ]→B | B→A₁, B→A₂, ... |
| Analogy（类比） | 不确定 | [source]→target | [source, analogy_claim]→target |
| Extrapolation（外推） | 不确定 | [source]→target | [source, extrap_claim]→target |
| Reductio（归谬） | 依赖否定 | contradict(P,R) | P→Q + contradict(Q,R) + negation(P,¬P) |
| Elimination（排除） | 依赖否定 | [E₁,E₂]→H₃ | contradict + negation + exhaustive entailment |

**表中记法说明：**
- `[]→H` 表示无显式前提，H 为结论（abduction 中假说无直接前提支撑）
- `[A₁..Aₙ]→B` 表示 A₁ 到 Aₙ 为前提，B 为结论
- `O` 为预测观测（编译器生成），`O'` 为实际观测（作者引用）
- `analogy_claim` / `extrap_claim` 为编译器自动生成的辅助命题

Deduction 是唯一直接产生 p=1 因子的策略——作者声明此步为确定性演绎，编译器将粗推理因子直接升级为蕴含。其余六种策略通过更复杂的拓扑实现间接支持，展开后各因子也是 p=1。

Modus tollens 不作为独立策略——它由蕴含因子的反向 BP 消息自动实现（C1 弱三段论），不需要专门的展开模板。

## 3. 文档重组方案

### 3.1 目标结构

```
docs/foundations/theory/
  plausible-reasoning.md         ← 修订（Jaynes 基础）
  reasoning-factor-graph.md      ← 新建（因子图 + 逻辑算子）
  coarse-reasoning.md            ← 新建（粗推理算子）
  belief-propagation.md          ← 重写（纯 BP 算法）
  science-ontology.md            ← 新建（科学本体论）
  science-formalization.md       ← 修订（科学推理形式化）
```

推导链：
```
plausible-reasoning.md          (Jaynes 基础)
  ↓
reasoning-factor-graph.md       (因子图 + 逻辑算子)
  ↓
coarse-reasoning.md             (粗推理算子)
  ↓
belief-propagation.md           (BP 算法)
  ↓
science-ontology.md             (科学知识本体论)
  ↓
science-formalization.md        (科学推理 → 因子图映射)
```

### 3.2 各文档详细设计

#### (1) `plausible-reasoning.md`（修订）

**变更范围：** 轻量修订。

- **保留**：Cox 定理、C1-C4 弱三段论、MaxEnt、Robot 隐喻、Polya 推理模式、矛盾处理
- **修改**：Cromwell 规则从"理论要求"降级为"实用建议"，明确 theory 层不引入 ε
- **新增**：定位说明——本文档是理论栈的起点，下游文档从这里推导

#### (2) `reasoning-factor-graph.md`（新建）

**内容结构：**

- §1 因子图表示：二部图定义、联合概率分解、从 reasoning-hypergraph.md §5 迁移
- §2 四种原语算子：蕴含、合取、析取、否定——定义、势函数真值表、语义
- §3 派生算子：等价 = 双向蕴含、矛盾 = 否定 + 蕴含（需辅助变量）
- §4 多变量推广：多前提蕴含、多变量合取/析取
- §5 完备性论证：16 种真值函数的分析，{→,∧,∨,¬} 的覆盖性

**来源：** reasoning-hypergraph.md §5（因子图结构）+ 新写内容（算子分析）。

#### (3) `coarse-reasoning.md`（新建）

**内容结构：**

- §1 动机：完全形式化不现实，需要近似机制
- §2 粗推理算子定义：势函数、四种状态逐一分析、ψ(0,\*)=1 的理由
- §3 与 Jaynes 弱三段论的一致性：验证 C1-C4、说明这是一种模型选择
- §4 p 的含义：不完全形式化的度量、p→1 收敛为蕴含、唯一因子级自由参数
- §5 分解模式：多前提联合、粗等价、粗矛盾
- §6 粗因子图与细因子图的关系：细化过程、先粗后细

**来源：** 全新内容（基于本次讨论）。

#### (4) `belief-propagation.md`（重写）

**内容结构：**

- §1 BP 算法：变量→因子消息、因子→变量消息更新公式、belief 计算
- §2 消息传递语义：逻辑算子(p=1)上的行为、粗推理算子(p<1)上的行为、弱三段论如何通过消息传递实现
- §3 收敛性：loopy BP 收敛条件、消息调度策略

**移除内容：**
- noisy-AND 作为核心假设的论述（当前 §2、§5）
- "silence model" 讨论（已被 coarse-reasoning.md 中 ψ(0,\*)=1 的分析取代）
- Cromwell 规则相关内容
- 局部/全局推理的讨论（属于 cli/ 和 lkm/ 架构层）

**来源：** 当前 belief-propagation.md §3-§4（算法和收敛性）+ 重写框架。

#### (5) `science-ontology.md`（新建）

**内容结构：**

- §1 知识类型：claim、setting、question、template——定义、BP 参与规则、先验携带
- §2 关系类型：等价、矛盾、否定——定义、与逻辑算子的对应
- §3 推理策略：七种策略（deduction、abduction、induction、analogy、extrapolation、reductio、elimination），每种包含：
  - 定义和语义
  - 粗因子图
  - 细因子图展开规则
  - BP 路径分析

**来源：** reasoning-hypergraph.md §6（知识类型）+ §7（算子类型）+ 新写内容（推理策略展开规则）。

**注意：** 当前 reasoning-hypergraph.md §7 定义的五种 reasoning_type（entailment、induction、abduction、equivalent、contradict）是 Graph IR 层的概念。本文档的七种推理策略是 theory 层的概念，描述粗→细展开模板。两者关系：策略展开后产生的因子使用 Graph IR 的 reasoning_type。未来可能需要在 Graph IR 层新增 reasoning_type（如 negation）以支持 reductio 和 elimination 策略。

#### (6) `science-formalization.md`（修订）

**变更范围：** 框架性修订。

- **保留**：伽利略案例（§3）、形式化方法论（§2）
- **修订**：
  - §2.4 标题从"noisy-AND 主链 + 约束"改为"粗因子图与细因子图"
  - 粗/细因子图表述基于新理论——引用 coarse-reasoning.md
  - 论证策略引用 science-ontology.md 中的定义
- **新增**：§ 形式化工作流——从粗到细
  - 第一步：构建粗因子图（识别命题和推理关系）
  - 第二步：细化为细因子图（将粗推理算子展开为逻辑算子组合）
  - 关键认识：粗因子图本身有推理价值，细化是持续改进过程
- **移除**：对 noisy-AND 作为独立概念的引用

### 3.3 归档

`reasoning-hypergraph.md` 内容拆分后移至 `docs/archive/`。内容去向：

| 来源章节 | 目标文档 |
|---------|---------|
| §5 因子图数学结构 | reasoning-factor-graph.md |
| §6 知识类型 | science-ontology.md |
| §7 算子类型、推理类型 | science-ontology.md |
| §4 合取语义 | coarse-reasoning.md（重新表述） |
| §8 图不变性、可废止性 | 留在归档文档中，视需要迁移到 review/ 层 |
| §9 Review/curation 边界 | 留在归档文档中，视需要迁移到 review/ 层 |
| §1-3 目的、第一性原理 | 分散融入各新文档的动机章节 |

## 4. 下游影响

### 4.1 需要更新引用的文档

以下文档引用了 theory/ 下的文件，需要在实现后更新链接：

- `docs/foundations/graph-ir/graph-ir.md` — 引用 reasoning-hypergraph.md
- `docs/foundations/graph-ir/overview.md` — 引用 reasoning-hypergraph.md
- `docs/foundations/gaia-lang/spec.md` — 引用 reasoning-hypergraph.md、science-formalization.md
- `docs/foundations/gaia-lang/knowledge-types.md` — 引用 reasoning-hypergraph.md、graph-ir.md
- `docs/foundations/bp/potentials.md` — 引用 belief-propagation.md
- `docs/foundations/bp/inference.md` — 引用 belief-propagation.md
- `docs/ideas/` 下多个文件 — 引用 theory/ 文档

### 4.2 不修改的层

- `docs/foundations/graph-ir/` — 受保护层，仅做机械性链接更新（如 reasoning-hypergraph.md → reasoning-factor-graph.md），不改语义内容
- `docs/foundations/theory/` 以外的文档 — 仅更新链接，不改内容

## 5. 实现注意

- theory/ 属于受保护层，但本次是经用户批准的理论重组
- reasoning-hypergraph.md 的归档应在内容完全迁移后进行
- 下游引用更新应在同一 PR 中完成，保持一致性
