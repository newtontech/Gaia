# Theory 目录重组 Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure `docs/foundations/theory/` from 4 documents to 6 documents, repositioning noisy-AND from fundamental assumption to coarse approximation, based on first-principles re-examination of Jaynes framework.

**Architecture:** Six-document derivation chain: Jaynes → factor graph + logical operators → coarse reasoning operator → BP algorithm → science ontology → science formalization. The key theoretical insight: all fine factors are deterministic logical constraints (p=1); p<1 only appears in coarse reasoning factors representing incomplete formalization.

**Tech Stack:** Markdown documentation only. No code changes.

**Spec:** `docs/specs/2026-03-25-theory-restructuring-design.md`

---

## Chunk 1: New Foundation Documents

Three new documents that form the theoretical core. These have no dependencies on each other and can be written in parallel.

### Task 1: Create `reasoning-factor-graph.md`

**Files:**
- Create: `docs/foundations/theory/reasoning-factor-graph.md`
- Read: `docs/foundations/theory/reasoning-hypergraph.md` (§5, lines 95-149 — factor graph structure to migrate)

- [ ] **Step 1: Read source material**

Read `docs/foundations/theory/reasoning-hypergraph.md` §5 (lines 95-149) for factor graph definitions to migrate. Also read the spec §2.2 for the four primitive operators.

- [ ] **Step 2: Write `reasoning-factor-graph.md`**

Create `docs/foundations/theory/reasoning-factor-graph.md` with the following structure:

```markdown
# 推理因子图

> **Status:** Target design
>
> **上游依赖：** [plausible-reasoning.md](plausible-reasoning.md)（Jaynes 框架、Cox 定理、弱三段论）

本文档定义 Gaia 用于表示推理结构的因子图形式，以及因子图上的逻辑算子集合。

## §1 因子图表示

[从 reasoning-hypergraph.md §5 迁移因子图定义，重新表述]

- 二部图：变量节点（命题，携带 belief）+ 因子节点（约束，编码逻辑关系）
- 联合概率分解为因子势函数的乘积：P(x₁,...,xₙ) ∝ ∏ᵢ ψᵢ(xᵢ)
- 与 reasoning-hypergraph.md §5.4 的 Horn 子句类比

## §2 四种原语算子

[全新内容，基于 spec §2.2]

所有逻辑算子的势函数由真值表唯一确定：一致状态 ψ=1，不一致状态 ψ=0。因子层面无自由参数。

| 算子 | 一致状态 (ψ=1) | 不一致状态 (ψ=0) | 语义 |
|------|---------------|-----------------|------|
| 蕴含 A→C | (1,1)(0,1)(0,0) | (1,0) | 若 A 则 C |
| 合取 A∧B | (1,1) | (0,0)(0,1)(1,0) | A 且 B 同时成立 |
| 析取 A∨B | (1,1)(1,0)(0,1) | (0,0) | A 或 B 至少一个成立 |
| 否定 A⊕B | (1,0)(0,1) | (1,1)(0,0) | A 和 B 真值互补（二元约束，非一元 NOT） |

[每种算子详细解释其语义和在推理中的角色]

## §3 派生算子

[全新内容，基于 spec §2.2 派生算子部分]

- 等价 A↔B = 蕴含(A→B) + 蕴含(B→A)
- 矛盾 ¬(A∧B) = 否定(A,¬A) + 蕴含(B→¬A)，其中 ¬A 是辅助变量节点

[包含推导过程和真值表验证]

## §4 多变量推广

- 多前提蕴含：[A₁∧...∧Aₙ] → C（合取因子 + 蕴含因子的组合）
- 多变量合取/析取的势函数定义

## §5 完备性论证

两个二元变量有 2⁴ = 16 种真值函数。排除：
- 全一致（恒 ψ=1，无约束）
- 全不一致（恒 ψ=0，不可能）
- 单变量约束（仅依赖一个变量）

分析剩余的非平凡二元约束，论证 {→,∧,∨,¬} 的覆盖性。

## 跨层引用

- **上游：** [plausible-reasoning.md](plausible-reasoning.md) — Jaynes 框架
- **下游：** [coarse-reasoning.md](coarse-reasoning.md) — 粗推理算子（唯一的 p<1 因子）
- **下游：** [belief-propagation.md](belief-propagation.md) — BP 消息传递算法
- **Graph IR 层：** [../graph-ir/graph-ir.md](../graph-ir/graph-ir.md) — FactorNode schema

## 源码

- `libs/inference/factor_graph.py` — 因子图实现
```

- [ ] **Step 3: Commit**

```bash
git add docs/foundations/theory/reasoning-factor-graph.md
git commit -m "docs: create reasoning-factor-graph.md — logical operators and factor graph formalism"
```

---

### Task 2: Create `coarse-reasoning.md`

**Files:**
- Create: `docs/foundations/theory/coarse-reasoning.md`
- Read: `docs/specs/2026-03-25-theory-restructuring-design.md` §2.3-2.5 (primary source)

- [ ] **Step 1: Read spec sections §2.3-2.5**

These sections contain the complete theoretical content for this document: coarse reasoning operator definition, potential function, C1-C4 verification, decomposition patterns, coarse vs fine factor graphs.

- [ ] **Step 2: Write `coarse-reasoning.md`**

Create `docs/foundations/theory/coarse-reasoning.md` with the following structure:

```markdown
# 粗推理算子

> **Status:** Target design
>
> **上游依赖：** [reasoning-factor-graph.md](reasoning-factor-graph.md)（因子图、逻辑算子）

完全形式化不现实——作者无法总是把推理过程完全分解为逻辑算子。粗推理算子是对未分解推理步骤的近似，是因子图中唯一携带自由参数的因子类型。

## §1 动机

[为什么需要粗推理算子]
- 完全形式化的因子图中所有因子 p=1
- 现实中推理过程往往有未显式化的步骤和隐含假设
- 需要一种因子来近似这些未分解的推理

## §2 粗推理算子定义

二元因子，输入命题 M，输出命题 C，参数 p ∈ (0,1]。

势函数：
| M | C | ψ |
|---|---|---|
| 1 | 1 | 1 |
| 1 | 0 | f(p) |
| 0 | 1 | 1 |
| 0 | 0 | 1 |

### 四种状态的详细分析

[逐一分析每种 (M,C) 状态的含义和 ψ 值选择理由]

### ψ(0,*)=1 的选择理由

最小假设：前提不成立时因子对结论没有意见。

### f(p) 的约束条件

- f(1) = 0（p=1 时退化为蕴含）
- f 关于 p 单调递减
- 0 ≤ f(p) ≤ 1
- 具体形式留给 bp/ 层定义

## §3 与 Jaynes 弱三段论的一致性

[验证 C1-C4 均通过 BP 消息传递满足]

此势函数加上 BP 消息传递自然产生四种弱三段论行为：
- C1（C 为假 → M 更不可信）
- C2（M 为真 → C 更可信）
- C3（C 为真 → M 更可信）
- C4（M 为假 → C 变弱）

[每条附 BP 消息传递的推导]

说明：这是满足 C1-C4 的一种模型选择，不是唯一的。

## §4 p 的含义

- p < 1：推理的形式化不完整，不是"逻辑关系有噪声"
- p → 1：粗推理算子收敛为蕴含（真值表趋向蕴含的真值表）
- p 是唯一的因子级自由参数（逻辑算子无自由参数，节点先验 π 是节点级参数）

## §5 分解模式

粗推理算子 + 四种逻辑原语可以表达所有不确定关系：

- 单前提推理：直接用粗推理 M→C (p<1)
- 多前提联合推理：合取 A₁∧...∧Aₙ→M (p=1) + 粗推理 M→C (p<1)
- 粗等价：两个粗推理 A→B (p<1) + B→A (p<1)
- 粗矛盾：否定(A,¬A) (p=1) + 粗推理 B→¬A (p<1)

[每种模式附图示说明]

## §6 粗因子图与细因子图

- 细因子图：所有因子 p=1（逻辑算子），不确定性完全在节点 belief 中
- 粗因子图：含粗推理算子（p<1），是对未分解子图的近似
- 细化：把粗推理算子展开为逻辑算子组合 + 中间命题
- 展开后所有因子 p=1，不确定性从因子转移到节点

实践工作流：先构建粗因子图（捕捉推理骨架），再逐步细化。
粗因子图本身就有推理价值——BP 可以在粗因子图上运行，细化是持续改进过程。

## 跨层引用

- **上游：** [reasoning-factor-graph.md](reasoning-factor-graph.md) — 逻辑算子定义
- **上游：** [plausible-reasoning.md](plausible-reasoning.md) — C1-C4 弱三段论
- **下游：** [belief-propagation.md](belief-propagation.md) — BP 消息传递
- **下游：** [science-ontology.md](science-ontology.md) — 推理策略的展开模板
- **BP 层：** [../bp/potentials.md](../bp/potentials.md) — f(p) 的具体实现
```

- [ ] **Step 3: Commit**

```bash
git add docs/foundations/theory/coarse-reasoning.md
git commit -m "docs: create coarse-reasoning.md — coarse reasoning operator theory"
```

---

### Task 3: Create `science-ontology.md`

**Files:**
- Create: `docs/foundations/theory/science-ontology.md`
- Read: `docs/foundations/theory/reasoning-hypergraph.md` (§6 lines 150-211 — knowledge types; §7 lines 213-303 — operator types)

- [ ] **Step 1: Read source material**

Read reasoning-hypergraph.md §6 (knowledge type definitions) and §7 (operator types and semantics) for content to migrate. Also read spec §2.6 for the seven reasoning strategies.

- [ ] **Step 2: Write `science-ontology.md`**

Create `docs/foundations/theory/science-ontology.md` with the following structure:

```markdown
# 科学本体论

> **Status:** Target design
>
> **上游依赖：** [reasoning-factor-graph.md](reasoning-factor-graph.md)（逻辑算子）、[coarse-reasoning.md](coarse-reasoning.md)（粗推理算子）

本文档定义 Gaia 知识表示中的科学对象分类：知识类型、关系类型和推理策略。

## §1 知识类型

[从 reasoning-hypergraph.md §6 迁移，重新表述]

四种知识对象类型：

### Claim

可判真的科学断言。唯一携带先验 π、参与 BP 的知识类型。

### Setting

上下文假设、背景条件。不携带先验，不参与 BP。

### Question

开放的科学探究。不携带先验，不参与 BP。

### Template

含自由变量的命题模式（v1 暂不暴露）。通过实例化（instantiation）桥接到 claim。

| 类型 | 携带先验 π | 参与 BP | 说明 |
|------|----------|---------|------|
| Claim | 是 | 是 | 唯一的推理参与者 |
| Setting | 否 | 否 | 可作为结构性前提 |
| Question | 否 | 否 | 动机性，不参与推理 |
| Template | 否 | 否（通过实例化间接参与） | v1 暂不暴露 |

## §2 关系类型

关系类型描述命题之间的结构约束。每种关系类型对应逻辑算子的组合（参见 [reasoning-factor-graph.md](reasoning-factor-graph.md)）。

### 等价（Equivalence）

两个命题逻辑等价：A↔B = 蕴含(A→B) + 蕴含(B→A)。

### 矛盾（Contradiction）

两个命题不能同时为真：¬(A∧B) = 否定(A,¬A) + 蕴含(B→¬A)。需要辅助变量 ¬A。

### 否定（Negation）

两个命题真值互补：A⊕B，原语算子 ¬。是矛盾和归谬等复合关系的基础设施。

## §3 推理策略

推理策略是从粗因子图到细因子图的展开模板（参见 [coarse-reasoning.md](coarse-reasoning.md) §6）。每种策略定义了一种固定的结构变换规则。

### §3.1 Deduction（演绎）

确定性演绎推理，对应 modus ponens（肯定前件）。

**粗因子图：** M → C（粗推理）
**细因子图：** M → C（p=1，蕴含）

唯一直接产生 p=1 因子的策略。作者声明此步为确定性演绎，编译器将粗推理因子升级为蕴含。

Modus tollens（否定后件）不作为独立策略——它由蕴含因子的反向 BP 消息自动实现（C1 弱三段论）。

### §3.2 Abduction（溯因）

从观测推断假说。

**粗因子图：** [] → H（假说无直接前提支撑）
**细因子图：**
- O'（编译器生成的预测观测）
- 蕴含：H → O'（假说预测观测）
- 等价：O' ≡ O（预测观测 = 实际观测）

**BP 路径：** O belief 高（实验证据）→ equiv 传递给 O' → entailment 反向消息提升 H 的 belief。

**参数：**
- hypothesis: 指向一个 claim（要论证的假说）
- observation: 指向一个 claim（有独立证据链的观测）
- Body: justification（为什么 H 能预测 O）

### §3.3 Induction（归纳）

从多个实例归纳一般定律。

**粗因子图：** [A₁, A₂, ..., Aₙ] → B（实例为前提，定律为结论）
**细因子图：**
- 蕴含：B → A₁（p=1）
- 蕴含：B → A₂（p=1）
- ...
- 蕴含：B → Aₙ（p=1）

**BP 路径：** 多个 Aᵢ belief 高（观测）→ 各蕴含反向消息共同提升 B 的 belief。

**参数：**
- law: 指向一个 claim（一般性定律）
- instances: 标签引用元组（支撑定律的观测实例）

### §3.4 Analogy（类比）

从源系统的已知性质推断目标系统的对应性质。

**粗因子图：** [source] → target
**细因子图：**
- analogy_claim（编译器生成：两个系统具有结构类比关系）
- 蕴含：[source, analogy_claim] → target（p=1）

**BP 路径：** source belief 高 + analogy_claim belief 高 → target 获得支持。

### §3.5 Extrapolation（外推）

语法和编译结构与 analogy 相同。语义区别：跨范围外推而非跨系统迁移。

**粗因子图：** [source] → target
**细因子图：**
- extrapolation_claim（编译器生成：外推条件成立）
- 蕴含：[source, extrapolation_claim] → target（p=1）

### §3.6 Reductio（归谬）

假设 P 成立，推导出矛盾，因此结论 ¬P。

**粗因子图：** contradict(P, R)
**细因子图：**
- 蕴含：P → Q（从假设推导结果）
- 矛盾：contradict(Q, R)（推导结果与已知事实矛盾）
- 否定：negation(P, ¬P)（P 和 ¬P 真值互补）

**BP 路径：** R belief 高 → contradict(Q,R) 压低 Q → entailment P→Q 反向压低 P → negation(P,¬P) 提升 ¬P。

**依赖：** 需要 negation reasoning_type（当前 Graph IR 尚未支持）。

### §3.7 Elimination（排除）

在互斥且穷尽的假说中逐一排除，剩余的即为结论。

**粗因子图：** [E₁, E₂] → H₃（证据为前提，survivor 为结论）
**细因子图：**
- contradict(H₁, E₁)（证据与假说矛盾）
- contradict(H₂, E₂)（同上）
- negation(H₁, ¬H₁)
- negation(H₂, ¬H₂)
- 蕴含：[¬H₁, ¬H₂] → H₃（穷尽约束）

**BP 路径：** Eᵢ belief 高 → contradict 压低 Hᵢ → negation 提升 ¬Hᵢ → 穷尽 entailment 提升 H₃。

**依赖：** 需要 negation reasoning_type。

### 策略总结

| 策略 | 类型 | 粗因子图 | 细因子图 |
|------|------|---------|---------|
| Deduction | 确定性 | M→C（粗推理） | M→C (p=1) |
| Abduction | 不确定 | []→H | H→O' + O'≡O |
| Induction | 不确定 | [A₁..Aₙ]→B | B→A₁, B→A₂, ... |
| Analogy | 不确定 | [source]→target | [source, analogy_claim]→target |
| Extrapolation | 不确定 | [source]→target | [source, extrap_claim]→target |
| Reductio | 依赖否定 | contradict(P,R) | P→Q + contradict(Q,R) + negation(P,¬P) |
| Elimination | 依赖否定 | [E₁,E₂]→H₃ | contradict + negation + exhaustive entailment |

### 与 Graph IR reasoning_type 的关系

当前 Graph IR 定义五种 reasoning_type：entailment、induction、abduction、equivalent、contradict。推理策略展开后产生的因子使用这些 reasoning_type。Reductio 和 Elimination 策略需要未来在 Graph IR 层新增 negation reasoning_type。

## 跨层引用

- **上游：** [reasoning-factor-graph.md](reasoning-factor-graph.md) — 逻辑算子
- **上游：** [coarse-reasoning.md](coarse-reasoning.md) — 粗推理算子、粗/细因子图
- **下游：** [science-formalization.md](science-formalization.md) — 具体案例中的策略应用
- **Graph IR 层：** [../graph-ir/graph-ir.md](../graph-ir/graph-ir.md) — KnowledgeNode.type, FactorNode.reasoning_type
- **Gaia Lang 层：** [../gaia-lang/knowledge-types.md](../gaia-lang/knowledge-types.md) — DSL 声明函数
```

- [ ] **Step 3: Commit**

```bash
git add docs/foundations/theory/science-ontology.md
git commit -m "docs: create science-ontology.md — knowledge types, relations, and reasoning strategies"
```

---

## Chunk 2: Revise and Rewrite Existing Documents

These tasks modify existing documents. They depend on Chunk 1 being complete (for cross-references to be valid).

### Task 4: Revise `plausible-reasoning.md`

**Files:**
- Modify: `docs/foundations/theory/plausible-reasoning.md` (lines 245-251 — Cromwell section; add positioning note at top)

- [ ] **Step 1: Read current document**

Read `docs/foundations/theory/plausible-reasoning.md`. Focus on §3.5 Cromwell's Rule (lines 245-251).

- [ ] **Step 2: Revise Cromwell section**

In §3.5 (Cromwell's Rule), add a note clarifying that Cromwell is a practical recommendation, not a theoretical requirement of Jaynes' probability theory. The theory layer does not introduce ε. Cromwell's engineering applications (numerical clamping) belong in the bp/ and implementation layers.

- [ ] **Step 3: Add positioning note**

Add a paragraph after the status header (around line 8) positioning this document as the foundation of the theory stack:

```markdown
本文档是 theory/ 层理论栈的起点。下游文档：
- [reasoning-factor-graph.md](reasoning-factor-graph.md) — 因子图形式和逻辑算子
- [coarse-reasoning.md](coarse-reasoning.md) — 粗推理算子
- [belief-propagation.md](belief-propagation.md) — BP 消息传递算法
- [science-ontology.md](science-ontology.md) — 科学知识本体论
- [science-formalization.md](science-formalization.md) — 科学推理形式化
```

- [ ] **Step 4: Commit**

```bash
git add docs/foundations/theory/plausible-reasoning.md
git commit -m "docs: revise plausible-reasoning.md — demote Cromwell, add stack positioning"
```

---

### Task 5: Rewrite `belief-propagation.md`

**Files:**
- Modify: `docs/foundations/theory/belief-propagation.md` (major rewrite — keep §3 algorithm core, rewrite framing)
- Read: Current `belief-propagation.md` (286 lines)

This is the largest single change. The current document frames noisy-AND as the fundamental assumption; the rewrite removes this framing and focuses on the BP algorithm itself.

- [ ] **Step 1: Read current document thoroughly**

Read all of `docs/foundations/theory/belief-propagation.md` (286 lines). Note:
- §3 (lines 174-226): Sum-product algorithm — **preserve** this section largely intact
- §4 (lines 227-249): Loopy BP convergence — **preserve** core convergence content
- §1-2, §5: These sections frame noisy-AND as central — **rewrite** entirely

- [ ] **Step 2: Rewrite the document**

Replace the entire document with a new version structured as:

```markdown
# 置信传播

> **Status:** Target design
>
> **上游依赖：**
> - [plausible-reasoning.md](plausible-reasoning.md) — Jaynes 框架、弱三段论 C1-C4
> - [reasoning-factor-graph.md](reasoning-factor-graph.md) — 因子图、逻辑算子
> - [coarse-reasoning.md](coarse-reasoning.md) — 粗推理算子

本文档定义因子图上的置信传播（Belief Propagation, BP）算法。BP 是一种通用的消息传递算法，与具体的势函数选择无关。

## §1 Sum-Product 消息传递

[从当前 §3 迁移算法定义，保留核心公式]

### 消息更新

变量→因子消息：
$$\mu_{x \to f}(x) = \prod_{g \in N(x) \setminus \{f\}} \mu_{g \to x}(x)$$

因子→变量消息：
$$\mu_{f \to x}(x) = \sum_{\sim x} \psi_f(\mathbf{x}_f) \prod_{y \in N(f) \setminus \{x\}} \mu_{y \to f}(y)$$

### Belief 计算

$$b(x) \propto \pi(x) \cdot \prod_{f \in N(x)} \mu_{f \to x}(x)$$

其中 π(x) 是节点先验——因子图中唯一的自由参数（细因子图）或与粗推理因子的 p 一起构成两个参数类别（粗因子图）。

### 调度

同步调度：所有消息同时更新。

### Exclude-self 规则

变量到因子的消息排除来自该因子的消息，防止自我强化。

## §2 消息传递语义

### 逻辑算子上的消息传递

逻辑算子（蕴含、合取、析取、否定）的势函数是 0/1 值。消息传递在这些因子上实现确定性逻辑推理。

蕴含因子 A→C 上的消息传递行为：
[详细推导前向和反向消息]

### 粗推理算子上的消息传递

粗推理算子的势函数含参数 p（参见 [coarse-reasoning.md](coarse-reasoning.md) §2）。

[详细推导消息传递行为，展示 C1-C4 弱三段论如何自然实现]

### 弱三段论的实现

BP 消息传递在粗推理算子上自然产生 Jaynes 弱三段论（参见 [plausible-reasoning.md](plausible-reasoning.md) §1.3）的四种行为：

- C1（modus tollens 方向）：[推导]
- C2（modus ponens 方向）：[推导]
- C3（确认后件）：[推导]
- C4（否认前件）：[推导]

## §3 收敛性

[从当前 §4 迁移收敛性内容]

### Loopy BP

因子图含环时，BP 不保证收敛。实践中通过阻尼（damping）改善：

$$\mu^{(t+1)} = \alpha \cdot \mu^{(new)} + (1-\alpha) \cdot \mu^{(t)}$$

### Bethe 自由能

Loopy BP 的不动点对应 Bethe 自由能的驻点。

### 收敛判据

消息变化量 max|Δμ| < threshold 时终止。

## 跨层引用

- **上游：** [plausible-reasoning.md](plausible-reasoning.md) — Jaynes 框架
- **上游：** [reasoning-factor-graph.md](reasoning-factor-graph.md) — 因子图定义
- **上游：** [coarse-reasoning.md](coarse-reasoning.md) — 粗推理算子势函数
- **BP 层：** [../bp/potentials.md](../bp/potentials.md) — f(p) 具体实现
- **BP 层：** [../bp/inference.md](../bp/inference.md) — 工程实现细节

## 源码

- `libs/inference/bp.py` — BP 算法实现
- `libs/inference/factor_graph.py` — 因子图数据结构
```

- [ ] **Step 3: Verify cross-references**

Check that all links to other theory/ documents point to the correct new filenames.

- [ ] **Step 4: Commit**

```bash
git add docs/foundations/theory/belief-propagation.md
git commit -m "docs: rewrite belief-propagation.md — pure BP algorithm, remove noisy-AND framing"
```

---

### Task 6: Revise `science-formalization.md`

**Files:**
- Modify: `docs/foundations/theory/science-formalization.md` (§2.4 title change, terminology updates, add workflow section)
- Read: Current `science-formalization.md` (470 lines)

- [ ] **Step 1: Read current document**

Read `docs/foundations/theory/science-formalization.md`. Focus on:
- §2.4 (lines ~127-137): Section titled "组装：noisy-AND 主链 + 约束" — rename
- References to "noisy-AND" throughout — replace with new terminology
- §4 (lines ~419-461): "为什么 p 可以被客观化" — may need minor updates

- [ ] **Step 2: Rename §2.4**

Change section title from "组装：noisy-AND 主链 + 约束" (or similar) to "组装：粗因子图与细因子图".

- [ ] **Step 3: Replace noisy-AND references**

Throughout the document, replace references to "noisy-AND" as a fundamental concept with references to the coarse reasoning operator and the coarse/fine factor graph distinction. Add cross-references to `coarse-reasoning.md`.

- [ ] **Step 4: Update status header references**

Update the upstream dependency list to reference the new theory/ documents instead of the old ones (e.g., reasoning-hypergraph.md → reasoning-factor-graph.md + coarse-reasoning.md + science-ontology.md).

- [ ] **Step 5: Add workflow section**

Add a new section "§ 形式化工作流——从粗到细" covering:
- 第一步：构建粗因子图（识别命题和推理关系，用粗推理算子连接）
- 第二步：细化为细因子图（将粗推理算子展开为逻辑算子组合 + 中间命题）
- 关键认识：粗因子图本身有推理价值，细化是持续改进过程

- [ ] **Step 6: Update cross-references to reasoning strategies**

Where the document discusses abduction, induction, analogy patterns (§2.3, §3.4), add cross-references to `science-ontology.md §3` for the formal definitions.

- [ ] **Step 7: Commit**

```bash
git add docs/foundations/theory/science-formalization.md
git commit -m "docs: revise science-formalization.md — replace noisy-AND framing, add coarse-to-fine workflow"
```

---

## Chunk 3: Archive and Update References

### Task 7: Archive `reasoning-hypergraph.md`

**Files:**
- Move: `docs/foundations/theory/reasoning-hypergraph.md` → `docs/archive/foundations-v2/theory/reasoning-hypergraph.md`
- Modify: `docs/archive/` index if one exists

- [ ] **Step 1: Verify content migration is complete**

Before archiving, verify that all key content from reasoning-hypergraph.md has been migrated:
- §5 (factor graph structure) → reasoning-factor-graph.md ✓
- §6 (knowledge types) → science-ontology.md ✓
- §7 (operator types) → science-ontology.md ✓
- §4.1 (conjunctive semantics) → coarse-reasoning.md ✓

- [ ] **Step 2: Move file to archive**

```bash
mkdir -p docs/archive/foundations-v2/theory
git mv docs/foundations/theory/reasoning-hypergraph.md docs/archive/foundations-v2/theory/reasoning-hypergraph.md
```

- [ ] **Step 3: Commit**

```bash
git commit -m "docs: archive reasoning-hypergraph.md — content migrated to new theory structure"
```

---

### Task 8: Update downstream references

**Files:**
- Modify: `docs/foundations/graph-ir/graph-ir.md` (link updates only)
- Modify: `docs/foundations/graph-ir/overview.md` (link updates only)
- Modify: `docs/foundations/gaia-lang/spec.md` (link updates only)
- Modify: `docs/foundations/gaia-lang/knowledge-types.md` (link + terminology updates)
- Modify: `docs/foundations/bp/potentials.md` (link updates only)
- Modify: `docs/foundations/bp/inference.md` (link updates only)
- Modify: `docs/foundations/rationale/product-scope.md` (link updates only)
- Modify: `docs/foundations/rationale/domain-vocabulary.md` (link verification)
- Modify: `docs/foundations/README.md` (index + descriptions update)
- Modify: `docs/documentation-policy.md` (link updates only)
- Modify: `docs/ideas/*.md` (link updates only)

- [ ] **Step 1: Find all references to old theory/ filenames**

Search across **all** of `docs/` for references to archived/restructured files:

```bash
grep -r "reasoning-hypergraph" docs/ --include="*.md" -l
grep -r "noisy-AND\|noisy.AND" docs/foundations/ --include="*.md" -l
grep -r "belief-propagation" docs/foundations/ docs/ideas/ --include="*.md" -l
```

Note: search scope includes `docs/foundations/rationale/`, `docs/foundations/README.md`, and `docs/documentation-policy.md` — not just the four subdirectories.

- [ ] **Step 2: Update `reasoning-hypergraph.md` references**

For each file, replace references to `reasoning-hypergraph.md` with the appropriate new target:
- Factor graph / structure references → `reasoning-factor-graph.md`
- Knowledge type references → `science-ontology.md`
- Operator type references → `science-ontology.md`
- Conjunctive semantics references → `coarse-reasoning.md`

Choose the target based on which section of reasoning-hypergraph.md was being referenced.

- [ ] **Step 3: Update `docs/foundations/README.md`**

This is the foundations index and needs content updates, not just link swaps:
- Replace the single `reasoning-hypergraph.md` entry with the new six-document list
- Update the BP description from "势函数模型（noisy-AND + leak）、和积算法" to reflect the new framing (pure BP algorithm)
- Ensure the theory/ section accurately describes the derivation chain

- [ ] **Step 4: Update noisy-AND terminology in `knowledge-types.md`**

`docs/foundations/gaia-lang/knowledge-types.md` contains "noisy-AND 语义" references that contradict the new theory framing. Update:
- Replace "noisy-AND 语义（联合必要条件）" with "合取语义（联合必要条件）" or "粗推理语义"
- Add cross-reference to `coarse-reasoning.md` for the theoretical basis

Similarly check `docs/foundations/gaia-lang/spec.md` for noisy-AND references.

- [ ] **Step 5: Verify `belief-propagation.md` references still work**

The filename hasn't changed, but the section structure has. Check that section-level references (e.g., `belief-propagation.md §2`) still point to valid sections.

- [ ] **Step 6: Update internal theory/ cross-references**

Check that `plausible-reasoning.md` and `science-formalization.md` reference the new filenames correctly (reasoning-factor-graph.md, coarse-reasoning.md, science-ontology.md instead of reasoning-hypergraph.md).

- [ ] **Step 7: Commit**

```bash
git add docs/
git commit -m "docs: update downstream references to new theory/ document structure"
```

---

### Task 9: Final verification and PR

- [ ] **Step 1: Verify all six theory/ documents exist**

```bash
ls docs/foundations/theory/
```

Expected:
```
plausible-reasoning.md
reasoning-factor-graph.md
coarse-reasoning.md
belief-propagation.md
science-ontology.md
science-formalization.md
```

- [ ] **Step 2: Verify reasoning-hypergraph.md is archived**

```bash
ls docs/archive/foundations-v2/theory/reasoning-hypergraph.md
```

- [ ] **Step 3: Check for broken links**

```bash
grep -r "reasoning-hypergraph" docs/ --include="*.md" | grep -v "docs/archive/" | grep -v "docs/specs/"
```

Expected: No results (all references updated). The only remaining references should be in `docs/archive/` and `docs/specs/`.

Also check for stale noisy-AND references:
```bash
grep -r "noisy-AND\|noisy.AND" docs/foundations/ --include="*.md"
```

Expected: No results in foundations/ docs (all replaced with new terminology).

- [ ] **Step 4: Verify derivation chain in document headers**

Read the status/dependency headers of all six theory/ documents and verify the derivation chain:
```
plausible-reasoning.md → reasoning-factor-graph.md → coarse-reasoning.md → belief-propagation.md → science-ontology.md → science-formalization.md
```

- [ ] **Step 5: Create PR**

```bash
git push origin HEAD
gh pr create --title "docs: restructure theory/ directory — reposition noisy-AND as coarse approximation" --body "..."
```

Include in PR description:
- Link to spec: `docs/specs/2026-03-25-theory-restructuring-design.md`
- Summary of the six-document structure
- Key theoretical change: noisy-AND → coarse reasoning operator
