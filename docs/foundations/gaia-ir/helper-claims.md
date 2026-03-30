# Helper Claims

> **Status:** Target design
>
> **⚠️ Protected Contract Layer** — 本文档定义 Gaia IR 中 helper claim 的建模纪律与 public/private 边界。

## 目的

Helper claim 用来命名那些既属于 `claim` 世界、又承担中间推理或结构支撑角色的命题。

它解决的是同一个问题：

- 哪些中间命题应该显式落成 `Knowledge(type=claim)`
- 这些 claim 何时只是某个 `FormalStrategy` 的内部节点
- 这些 claim 何时应被提升为可复用、可 canonicalize 的公共节点

## 1. 定位

Helper claim **不是新的 Knowledge 类型**。它始终编码为：

```text
Knowledge(type=claim)
```

也就是说，helper claim 和普通 claim 的差别不在 schema primitive，而在角色：

- 它可能是某个命名推理骨架里的中间命题
- 它可能是为了复用、审查或参数化而显式提炼出来的桥接命题
- 它可能只是一个结构性中间结果

一旦它进入 Gaia IR，就仍然遵循普通 `claim` 的规则：

- 可以被引用
- 可以被 canonicalize
- 在需要时可以携带 prior

## 2. 两类 Helper Claim

### 2.1 语义型 Helper Claim

这类 helper claim 有独立科学语义，未来可能被单独支持、质疑、复用或反驳。

当前最重要的几类是：

| helper_kind | 典型来源 | 默认角色 |
|-------------|----------|----------|
| `prediction` | abduction | 内部中间 claim，必要时可提升为公共 claim |
| `instance` | induction / deduction | 内部中间 claim，必要时可提升为公共 claim |
| `bridge` | analogy | 通常是公共 claim，并作为 `premises` 暴露 |
| `continuity` | extrapolation | 通常是公共 claim，并作为 `premises` 暴露 |

这里的关键不是名字，而是接口位置：

- `BridgeClaim` / `ContinuityClaim` 已经是 strategy 的外部输入，因此默认是公共 helper claim
- `prediction O` / `Instance_i` 更常见于某个 `FormalStrategy` 的内部 skeleton，因此默认是私有 helper claim

### 2.2 结构型 Helper Claim

这类 helper claim 没有独立科学语义，主要用于支撑确定性 skeleton 的显式落图。

典型例子：

| helper_kind | 来源 | 例子 |
|-------------|------|------|
| `conjunction_result` | conjunction | `M = A ∧ B` |
| `disjunction_result` | disjunction | `D = A ∨ B ∨ C` |
| `equivalence_result` | equivalence | `Eq = same_truth(A,B)` |
| `contradiction_result` | contradiction | `Contra = not_both_true(A,B)` |
| `complement_result` | complement | `Comp = opposite_truth(A,B)` |
| `formal_intermediate` | 其他 FormalExpr 局部步骤 | 某个仅为继续布线而显式存在的中间项 |

这些 helper claim 的共同点是：

- 它们通常由 compiler / reviewer 按 operator 结构确定性生成
- 它们本身仍是 `claim`
- 它们默认不是新的自由参数入口

当前 contract 下，**每个 Operator 都有 `conclusion`**。  
对 `equivalence` / `contradiction` / `complement` / `disjunction`，这个 `conclusion` 就是结构型 helper claim。

## 3. Public / Private 边界

Helper claim 的核心不是“语义型还是结构型”，而是它是否越过 strategy 的外部接口。

### 3.1 私有 Helper Claim

私有 helper claim 满足：

- 它是某个 `FormalStrategy` 内部 skeleton 的一部分
- 它不出现在该 Strategy 的 `premises` / `conclusion` 中
- 其他外部 Strategy 默认**不能**直接把它当作 `premises` 使用

这类节点在当前 Gaia IR 里仍然是**显式的 claim 节点**，不是隐藏对象；只是它们的可见性被 contract 限定在该 `FormalStrategy` 的内部边界内。

### 3.2 公共 Helper Claim

公共 helper claim 满足以下任一条件：

- 它本来就是某个 Strategy 的外部 `premise` 或 `conclusion`
- 它需要被多个 Strategy 共享
- 它需要被单独审查、引用、canonicalize 或比较

一旦满足这些条件，它就不再只是“内部中间节点”，而应被视为显式公共 `claim`。

### 3.3 提升规则

默认规则是：

- helper claim 可以先作为私有内部节点存在
- 一旦需要跨 Strategy 复用，就必须提升为公共 claim

提升后：

- 它仍然是 `Knowledge(type=claim)`
- 但不再享有“只能在单个 FormalStrategy 内部使用”的封装边界

## 4. 推荐元数据

Helper claim 不需要新增 schema 字段，但推荐在 `metadata` 中记录其角色：

| 字段 | 说明 |
|------|------|
| `helper_kind` | `prediction` / `instance` / `bridge` / `continuity` / `conjunction_result` 等 |
| `helper_origin` | `semantic` 或 `structural` |
| `helper_visibility` | `private` 或 `public` |
| `canonical_name` | 稳定、可复现的规范命名 |

这些字段是推荐约定，不是新的 core primitive。

## 5. Canonical Naming

`content` 负责给人看，`canonical_name` 负责稳定标识 helper claim 的规范身份。

推荐规则：

- 语义型 helper claim 优先使用 named-argument 形式
- 结构型 helper claim 优先使用稳定 functor 形式
- `canonical_name` 放在 `metadata` 中，而不是升级成新的顶层 schema 字段

推荐例子：

```text
prediction(model=H,target=ObsPattern)
instance(schema=Law,subject=Sample_i)
bridge(source=SourceLaw,target=Target)
continuity(left=KnownRegion,right=ExtendedRegion,axis=T)
all_true(A,B)
```

当前 contract 下，`all_true(...)` 主要用于 `conjunction` 结果类 helper claim。  
关系型 Operator 也推荐使用稳定 functor：

- `same_truth(A,B)`
- `not_both_true(A,B)`
- `opposite_truth(A,B)`
- `any_true(A,B,...)`

## 6. 与 Parameterization 的关系

Helper claim 不引入新的 `StrategyParamRecord` 规则，但它会影响哪些 claim 需要独立 prior。

推荐区分：

| helper 类型 | 默认是否需要独立 PriorRecord | 说明 |
|-------------|------------------------------|------|
| 语义型 helper claim | 是 | 它本身就是可被支持/质疑的不确定命题 |
| 结构型 helper claim | 否 | 它通常是 Operator 的确定性结果，不应再重复引入自由 prior |

因此：

- helper claim 仍然是 `claim`
- 但不是每个 helper claim 都自动成为新的参数输入口
- public/private 的区别在于接口暴露与复用边界，不在于是否是 claim

对直接 `FormalStrategy` 来说：

- public helper claim 和 private helper claim 都可能参与其导出的等效 conditional behavior
- 但只有 private helper claim 才允许在运行时被该 `FormalStrategy` 安全地 marginalize 掉
- 一旦某个 helper claim 被提升成公共 claim 并被外部复用，就不应再把包含它的 `FormalStrategy` 压成单个黑盒条件概率视图

## 7. 例子

### 7.1 Abduction

```text
FormalStrategy(type=abduction, premises=[Obs], conclusion=H):
  formal_expr:
    - implication([H, O], conclusion=O)
    - equivalence([O, Obs], conclusion=Eq_O_Obs)
```

这里：

- `Obs` 是外部接口输入，不是 helper claim 的特殊例外，它只是公共 `claim`
- `O` 是 `prediction` helper claim
- 若 `O` 只服务于这条 abduction skeleton，则默认是私有 helper claim
- 若未来别的 Strategy 也需要引用 `O`，则应把它提升为公共 helper claim

### 7.2 Analogy

```text
FormalStrategy(type=analogy, premises=[SourceLaw, BridgeClaim], conclusion=Target):
  formal_expr:
    - conjunction([SourceLaw, BridgeClaim, M], conclusion=M)
    - implication([M, Target], conclusion=Target)
```

这里：

- `BridgeClaim` 是公共语义型 helper claim，因为它已经作为 `premise` 暴露
- `M` 是私有结构型 helper claim，默认只属于这条 FormalStrategy 的内部 skeleton

### 7.3 Relation Operator

```text
Operator(operator=contradiction, variables=[A, B], conclusion=Contra_AB)
```

这里：

- `Contra_AB` 是结构型 helper claim
- 它推荐有稳定的 `canonical_name`，例如 `not_both_true(A,B)`
- 它不应默认再引入独立 prior
- 若未来有别的 Strategy 需要显式引用“`A` 与 `B` 不可同真”这一事实，它可以直接引用这个 helper claim

## 8. 当前边界

本文件当前**不**把以下内容写成 Gaia IR core contract：

- helper claim 的唯一 hash / ID 生成算法
- 结构型 helper claim 的统一 prior policy

这些都可以以后继续推进，但不影响当前 helper claim 重新进入主文档体系。
