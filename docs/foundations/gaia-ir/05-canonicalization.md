# Canonicalization — 规范化

> **Status:** Target design
>
> **⚠️ Protected Contract Layer** — 本目录定义 CLI↔LKM 结构契约。变更需要独立 PR 并经负责人审查批准。

## 1. Scope 划分

Gaia IR 管理 **local package 内部的结构表示**。跨包整合（全局图、跨包去重、global ID 分配）是 LKM 的职责。

| 概念 | 所属层 | 说明 |
|------|--------|------|
| QID（name-addressed identity） | IR | `{namespace}:{package_name}::{label}`，包内唯一 |
| content_hash（内容指纹） | IR | `SHA-256(type + content + sorted(params))`，跨包去重快速路径 |
| Equivalence Operator | IR | 作者显式声明两个 claim 语义等价 |
| `binding` Strategy | IR | 合并等价论证的结论，averaging CPT |
| `independent_evidence` CompositeStrategy | IR | 标记独立证据块，供 reviewer 验证 |
| CanonicalBinding（local→global 映射） | LKM | 详见 [dp-gaia 04-curation.md](https://github.com/SiliconEinstein/dp-gaia/blob/main/docs/foundations/lkm/04-curation.md) |
| Global Knowledge（`gcn_` ID） | LKM | 注册中心分配的跨包身份 |
| Global Strategy 提升 | LKM | local Strategy 的全局化 |

## 2. 等价与独立——两种跨论证关系

当同一命题被多条推理链支持时，IR 需要区分两种本质不同的情况：

### 2.1 等价论证 → `binding` Strategy

两条推理链推导出等价的结论，但它们的论据**不独立**（前提集重叠或本质相同）。此时不能让两条链在 BP 中各自贡献一份证据（double counting），需要合并为一条。

**IR 表达方式：**

1. 用 `equivalence` Operator 声明两个结论 claim 语义等价
2. 用 `binding` leaf Strategy 将两个结论合并为一个公共结论

```text
# 两条等价的推理链
Strategy_A: {P1, P2} → A
Strategy_B: {Q1, Q2} → B

# A 和 B 等价（不独立的论据）
equivalence(A, B) → helper claim

# 合并
binding_strategy (type: binding):
  premises: [A, B]
  conclusion: C
  CPT: P(C=1|a,b) = (a+b)/2
```

**BP 效果：** 公共结论 C 的 belief 等于 A 和 B 的 belief 的算术平均，不会 double count。binding factor 的反向消息会校准 A 和 B 的 belief 使之趋于一致。

**典型场景：**

- LKM curation 发现两个包的推理链论据等价，发布 curation package 做合并
- 包内作者声明两种表述等价
- 多个 reviewer/agent 对同一推理给出不同强度评估

### 2.2 独立证据 → `independent_evidence` CompositeStrategy

多条推理链从**不重叠的前提集**独立推导出同一结论。这是真正的独立证据——BP 应当累积它们的贡献。

**IR 表达方式：**

多条 sub-strategy 共享同一 conclusion 变量，用 `independent_evidence` CompositeStrategy 将它们组织在一起。

```text
# 两条独立的推理链
Strategy_theory: {bcs_theory, e_ph_coupling} → ybco_sc
Strategy_expt:   {meissner_observed}          → ybco_sc

# 声明独立性
CompositeStrategy (type: independent_evidence):
  sub_strategies: [Strategy_theory.id, Strategy_expt.id]
  conclusion: ybco_sc
```

**BP 效果：** 不需要特殊处理——两条独立的 factor 连接到同一结论变量，BP 标准 message product 自然累积（log-odds 空间中的加法）。

**Reviewer 验证：**

1. 每条 sub-strategy 内部推理 sound？
2. 各 sub-strategy 前提集不重叠？

### 2.3 判断方式

"等价还是独立"是语义判断。前提集合的重叠度是最重要的结构信号：

- 前提集完全不重叠 → 通常独立（`independent_evidence`）
- 前提集高度重叠或可通过 equivalence 关联 → 通常等价（`binding`）
- 部分重叠 → 需要人工/LLM 判断

IR 层不规定具体判定策略。作者在包内声明，reviewer/curation 层验证或 override。

## 3. Content Hash 的角色

`content_hash = SHA-256(type + content + sorted(parameters))` 不含 package 信息。

| 用途 | 说明 |
|------|------|
| 跨包同内容精确匹配 | LKM curation 的快速路径 |
| 包内变更检测 | 同一 label 的 content 变更时 hash 变化 |
| 去重候选筛选 | 作为 embedding 匹配前的预过滤 |

Content hash **不是**身份标识——两个不同包的 Knowledge 可以有相同 content_hash 但不同 QID。身份由 QID 决定，content_hash 是辅助索引。

## 4. FormalExpr 中间 Knowledge 的创建

展开操作可能需要创建中间 Knowledge（如 deduction 的 conjunction 结果 `M`、abduction 自动补齐的 `AlternativeExplanationForObs`、以及相应的 helper claim）。这些 Knowledge 由执行展开的 compiler/reviewer/agent **显式创建**，不由 FormalExpr 自动产生。

在当前 IR API 中，这一步通常通过专门的 formalization 入口一次性完成：调用方提供 leaf `Strategy`（或等价输入），IR 侧生成中间 Knowledge 与 canonical `FormalExpr`，再落成最终 `FormalStrategy`。**中间 Knowledge 仍然是显式对象，但一般不要求用户手写每个 Operator 与中间 claim ID。**

中间 Knowledge 获得 QID（`{ns}:{pkg}::{generated_label}`），generated_label 以 `__` 开头表示自动生成。

## 5. FormalExpr 的生成方式

- **所有当前已启用的命名策略**（`deduction`、`elimination`、`mathematical_induction`、`case_analysis`、`abduction`、`analogy`、`extrapolation`）：其 canonical `FormalExpr` 骨架由 `type` 和接口节点唯一确定，IR 侧应自动生成
- 对 `abduction` 这类家族，formalization 还可以自动补齐所需的 public interface claim（如 `AlternativeExplanationForObs`），并生成配套的 structural helper claim 与 canonical `FormalExpr`
- `reductio` 与 `induction` 在 theory 层保留，但 Gaia IR core 当前 defer；若需要表达 `induction`，先展开成多条共享同一结论的 abduction
- 对 `analogy`、`extrapolation`，formalization 复用显式给定的接口 claim（如 `BridgeClaim`、`ContinuityClaim`），再生成所需 helper claim
- 规范中的 `formal_expr` 示例应理解为 **formalization 之后的 canonical stored form**，而不是要求用户在正常构图时手写 `operators`
- **`toolcall` / `proof`**：deferred，未引入
