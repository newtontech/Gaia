# LKM Minimal Pipeline — Design Spec

| 文档属性 | 值 |
|---------|---|
| 版本 | 0.1 (draft) |
| 日期 | 2026-03-25 |
| 状态 | **Proposal** — 待 review |
| 关联文档 | [graph-ir/overview.md](../foundations/graph-ir/overview.md), [lkm/overview.md](../foundations/lkm/overview.md), [lkm/pipeline.md](../foundations/lkm/pipeline.md) |

## 1. 目标

在新的 `gaia/` 顶层包下，从零构建一条最小闭环 pipeline：

```
上传 LocalCanonicalGraph → 持久化 → Global Canonicalization → Global BP → 输出 BeliefState
```

不含 review（参数手工提供）、不含 curation、不含前端。验证新数据模型和 pipeline 架构在端到端场景下可用。

## 2. 设计决策

### 2.1 新旧代码分离

**决策：** 新代码放在 `gaia/` 顶层包，旧代码（`libs/`、`services/`、`scripts/`）原地不动。

**理由：**
- 零冲突——import 路径天然隔离（`from gaia.libs.models import ...` vs `from libs.storage import ...`）
- 不影响 CLI 合作者的工作
- 新 pipeline 跑通后，旧代码一次性 `git rm`

**约束：**
- 新代码不得 import 旧代码，除 `gaia/bp/__init__.py` 对 `libs.inference` 的桥接（见 §2.6）
- 旧测试继续跑，新测试写在 `tests/gaia/` 下
- 数据库表可清空重建，不考虑向后兼容

### 2.2 代码组织原则

**决策：** 按 `docs/foundations/` 的层次结构组织代码，而非按技术角色（libs/services/scripts）分。

```
gaia/
  libs/          ← 共享基础层（CLI + LKM 公用）
  bp/            ← BP 引擎（共享，本期占位）
  review/        ← Review pipeline（共享，本期占位）
  core/          ← 领域算法（CLI + LKM 公用）
  lkm/           ← LKM 服务端入口
  cli/           ← CLI 入口（占位，合作者 scope）
```

**对应关系：**

| docs/foundations/ 层 | 代码位置 | 本期 scope |
|---------------------|---------|-----------|
| theory/ | 无代码对应 | — |
| graph-ir/ | `gaia/libs/models/` | 全部重写 |
| bp/ | `gaia/bp/` | 占位，桥接旧代码 |
| review/ | `gaia/review/` | 占位 |
| cli/ | `gaia/cli/` | 占位 |
| lkm/ | `gaia/lkm/` | 全部重写 |

### 2.3 共享层设计

**libs/（CLI + LKM 共享）：**
- `models/` — Graph IR 的 Python 实现，单一数据来源
- `storage/` — 持久化后端（LanceDB + Neo4j）
- `embedding.py` — Embedding 接口
- `llm.py` — LLM client

**core/（CLI + LKM 共享）：**
- 领域算法层，不绑定任何入口（HTTP / batch / CLI）
- 包含：matching、canonicalize、global_bp、curation、search
- CLI 合作者将来可以直接 `from gaia.core.matching import ...`

**决策理由：** 最初 core/ 放在 `lkm/core/` 下，但考虑到 CLI 未来可能需要 matching 和 canonicalization 等算法，提升到顶层 `gaia/core/` 避免跨包依赖。

### 2.4 LKM 双入口

**决策：** LKM 分为 `pipelines/`（批量离线）和 `services/`（用户 API）两种入口，共享 `core/` 算法层。

```
lkm/
  ingest.py        ← LKM 专有写入逻辑
  pipelines/       ← 薄层：批量离线入口
  services/        ← 薄层：FastAPI API 入口
```

**依赖流向：**

```
lkm/pipelines/ ──┐
                  ├──→ core/ ──→ libs/ + bp/
lkm/services/  ──┘
```

- pipelines/ 和 services/ 都是薄编排层
- 具体业务逻辑全在 core/
- 现有 `services/gateway/` 整合进 `lkm/services/`

**LKM 专有逻辑（不放 core/）：**
- `ingest.py` — 绑定 StorageManager 的三写入流程
- 批量编排和 API 路由

### 2.5 存储层

**决策：**
- LanceDB 作为 content store（数据源）+ vector store
- Neo4j 作为 graph store（拓扑查询）
- 保留 `GraphStore` ABC，但只实现 Neo4j；Kuzu 留给 CLI 合作者
- 测试中默认只考虑 Neo4j，不写 Kuzu 相关 fixture/skip

**表结构完全重写**，对齐 `docs/foundations/graph-ir/`：

| 表 | 内容 | 对应 Graph IR 对象 |
|---|------|-------------------|
| `knowledge_nodes` | knowledge 节点（local + global 共用） | KnowledgeNode，以 `id` 前缀区分 (`lcn_` / `gcn_`) |
| `factor_nodes` | factor 节点（local + global 共用） | FactorNode，global 层 `steps`/`weak_points` 为 None |
| `canonical_bindings` | lcn → gcn 映射 | CanonicalBinding |
| `prior_records` | claim 先验（原子记录） | PriorRecord |
| `factor_param_records` | factor 概率（原子记录） | FactorParamRecord |
| `param_sources` | review 来源 | ParameterizationSource |
| `belief_states` | BP 输出 | BeliefState |

> **注意：** graph-ir.md §1.1 规定 local 和 global knowledge node 使用同一个 data class（`KnowledgeNode`），通过 `id` 前缀（`lcn_` vs `gcn_`）和字段填充（`content` vs `representative_lcn`）区分层级。Factor 节点同理。因此存储层不再按 local/global 拆分表，而是统一存储，查询时按前缀过滤。

**旧表（Knowledge, Chain, Module, Package 等）全部废弃。**

### 2.6 BP 引擎桥接

**决策：** `gaia/bp/__init__.py` 暂时 re-export `libs.inference` 中的 `FactorGraph`、`BeliefPropagation`。

**理由：** BP 算法本身不需要重写，只需要适配新的 Graph IR 模型。完整迁移放到 bp/ 专项。

**约束：** 这是新代码 import 旧代码的**唯一允许点**。`core/global_bp.py` 通过 `gaia.bp` 调用 BP，不直接 import `libs.inference`。

### 2.7 数据模型——完全重写

**决策：** 旧模型（`Knowledge`、`Chain`、`Module`、`Package`）全部废弃。新模型完全对齐 `docs/foundations/graph-ir/`。

**新模型清单：**

| 模型 | 文件 | 来源 |
|------|------|------|
| `KnowledgeNode` | `graph_ir.py` | graph-ir.md §1（local + global 共用同一 data class） |
| `FactorNode` | `graph_ir.py` | graph-ir.md §2（local + global 共用同一 data class） |
| `LocalCanonicalGraph` | `graph_ir.py` | graph-ir/overview.md |
| `GlobalCanonicalGraph` | `graph_ir.py` | graph-ir/overview.md |
| `PriorRecord` | `parameterization.py` | parameterization.md |
| `FactorParamRecord` | `parameterization.py` | parameterization.md |
| `ParameterizationSource` | `parameterization.py` | parameterization.md |
| `ResolutionPolicy` | `parameterization.py` | parameterization.md |
| `BeliefState` | `belief_state.py` | belief-state.md |
| `CanonicalBinding` | `binding.py` | graph-ir.md §3.4 |

> **注意：** `KnowledgeNode` 是 local 和 global 共用的唯一 data class。Local 层 `id` 以 `lcn_` 开头（content-addressed），global 层以 `gcn_` 开头（registry-allocated）。字段填充按层级不同：local 层有 `content`，global 层通常 `content=None` 但有 `representative_lcn`。不再有独立的 `GlobalCanonicalNode` class。`FactorNode` 同理。

**关键约束（来自 graph-ir 文档）：**
- KnowledgeNode ID: local 层 `SHA-256(type + content + sorted(parameters))`，前缀 `lcn_`；global 层注册分配，前缀 `gcn_`
- Cromwell's rule: 所有概率 clamp 到 `[ε, 1-ε]`，ε = 1e-3
- 只有 `type=claim` 的节点参与 BP、有 prior 和 belief
- `stage=candidate|permanent` + `category=infer` → `reasoning_type` 必填
- `equivalent`/`contradict` → `conclusion=None`，`premises >= 2`
- Global factor 不携带 `steps` 和 `weak_points`

## 3. Pipeline 流程

完整 pipeline 由 4 个独立模块组成，每个模块有清晰的输入/输出边界：

```
模块 1: persist_local    → 持久化 local graph
模块 2: canonicalize      → global canonicalization + 整合 parameterization
模块 3: persist_global    → 持久化 global 结果（graph IR + parameterization）
模块 4: global_bp         → 组装参数 → BP → 持久化 belief state
```

### 3.1 模块 1: persist_local（持久化本地图）

```
输入:
  - LocalCanonicalGraph
  - LocalParameterization（node_priors + factor_params，来自 CLI build/review）
  - package_id + version

操作:
  持久化 local graph → LanceDB (knowledge_nodes + factor_nodes)

输出: 无（side effect: 数据写入存储）
```

### 3.2 模块 2: canonicalize（全局规范化 + 整合参数）

```
输入:
  - LocalCanonicalGraph
  - LocalParameterization（node_priors + factor_params）
  - 当前 GlobalCanonicalGraph（从存储加载）
  - package_id + version

操作:
  1. 分类每个 local node: premise-only / conclusion / both
  2. 对每个 node，在 global graph 中找最佳匹配（core/matching.py）
  3. 应用 graph-ir.md §3.1 决策规则:
     ├─ premise-only + 匹配 → match_existing（直接绑定，global prior 不变）
     ├─ conclusion + 匹配 → equivalent_candidate（新建 gcn + equivalent factor + placeholder params）
     ├─ both → 按 conclusion 处理
     └─ 无匹配 → create_new
  4. Factor lifting: lcn→gcn ID 重写，丢弃 steps/weak_points
  5. 整合 parameterization:
     ├─ 将 LocalParameterization 中的 node_priors 转换为 PriorRecord（lcn→gcn 映射）
     ├─ 将 LocalParameterization 中的 factor_params 转换为 FactorParamRecord（lcn→gcn 映射）
     └─ 为 equivalent_candidate factor 和新建 gcn 生成 placeholder 记录

输出:
  CanonicalizationResult:
    bindings: list[CanonicalBinding]
    new_global_nodes: list[KnowledgeNode]   # gcn_ prefixed
    global_factors: list[FactorNode]         # gcn_ IDs, no steps/weak_points
    prior_records: list[PriorRecord]         # 从 local params 转换 + placeholders
    factor_param_records: list[FactorParamRecord]  # 从 local params 转换 + placeholders
    param_source: ParameterizationSource     # 记录来源
```

### 3.3 模块 3: persist_global（持久化全局结果）

```
输入: CanonicalizationResult

操作:
  1. 持久化 global knowledge nodes → LanceDB + Neo4j
  2. 持久化 global factor nodes → LanceDB + Neo4j
  3. 持久化 canonical bindings → LanceDB
  4. 持久化 prior records → LanceDB
  5. 持久化 factor param records → LanceDB
  6. 持久化 param source → LanceDB

输出: 无（side effect: 数据写入存储）
```

### 3.4 模块 4: global_bp（全局信念传播）

```
输入:
  - GlobalCanonicalGraph（从存储加载）
  - PriorRecord[]（从存储加载）
  - FactorParamRecord[]（从存储加载）
  - ResolutionPolicy

操作:
  1. 组装参数（core/global_bp.py:assemble_parameterization）
     ├─ 按 resolution policy 从原子记录中选值
     ├─ latest: 每个 node/factor 取最新记录
     ├─ source:<id>: 指定 source 的记录
     ├─ prior_cutoff: 只取截止时间前的记录
     └─ 验证完备性: 每个 claim 节点和每个 factor 都必须有值
  2. 构建 FactorGraph（gaia.bp.adapter — 桥接旧代码）
     ├─ 只有 claim 节点作为 variable
     ├─ 非 claim premise 跳过（不创建 BP edge）
     └─ factor potential 使用 Noisy-AND + Leak 语义
  3. 运行 BP（libs.inference.bp.BeliefPropagation）
     ├─ damping=0.5, max_iterations=50, threshold=1e-6
     └─ 输出: beliefs dict + diagnostics
  4. 包装为 BeliefState 并持久化
     ├─ bp_run_id, created_at
     ├─ resolution_policy + prior_cutoff（可重现）
     ├─ beliefs: {gcn_id → posterior}（只有 claim）
     └─ diagnostics: converged, iterations, max_residual

输出: BeliefState
```

### 3.5 端到端编排

`lkm/ingest.py` 编排模块 1-3，`core/global_bp.py` 是模块 4：

```
ingest_package(local_graph, local_params, package_id, version, storage, embedding_model):
  模块 1: persist_local(local_graph, package_id, version, storage)
  模块 2: result = canonicalize(local_graph, local_params, global_graph, package_id, version, embedding_model)
  模块 3: persist_global(result, storage)
  return result

run_global_bp(storage, policy):
  模块 4: belief_state = global_bp(global_graph, prior_records, factor_records, policy)
  return belief_state
```

### 3.6 关于 LocalParameterization

本期不含 review pipeline，但 ingest 的输入仍需要 `LocalParameterization`：

- **测试/开发中：** fixture builder 生成默认 prior（0.5）和 factor probability（0.8）
- **批量 pipeline 中：** 从 CLI build 产出的 JSON 文件加载（`.gaia/infer/` 目录）
- **API 中：** POST 请求包含 local_graph + local_params

将来 review pipeline 完成后，会在 canonicalize 之前运行 review，review 产出的参数直接作为 LocalParameterization 输入。

## 4. 完整目录结构

```
gaia/
  __init__.py

  libs/
    __init__.py
    models/
      __init__.py              # Re-exports 所有模型类
      graph_ir.py              # KnowledgeNode, FactorNode, LocalCanonicalGraph, GlobalCanonicalGraph
      parameterization.py      # PriorRecord, FactorParamRecord, ResolutionPolicy
      belief_state.py          # BeliefState
      binding.py               # CanonicalBinding
    storage/
      __init__.py
      config.py                # StorageConfig
      base.py                  # ABC: ContentStore, GraphStore
      lance.py                 # LanceDB 实现
      neo4j.py                 # Neo4j 实现
      manager.py               # StorageManager（三写入）
    embedding.py               # 从旧代码搬运
    llm.py                     # 从旧代码搬运

  core/
    __init__.py
    matching.py                # Embedding cosine + TF-IDF
    canonicalize.py            # Global canonicalization
    global_bp.py               # 参数组装 + BP 编排

  lkm/
    __init__.py
    ingest.py                  # 验证 + 三写入 + canonicalize
    pipelines/
      __init__.py
      run_ingest.py            # 批量 ingest
      run_global_bp.py         # 批量 global BP
      run_full.py              # 全流程编排
    services/
      __init__.py
      app.py                   # FastAPI app factory
      deps.py                  # DI
      routes/
        __init__.py
        packages.py            # POST /packages/ingest
        knowledge.py           # GET /knowledge/{id}
        inference.py           # POST /inference/run

  bp/
    __init__.py                # 桥接: re-export libs.inference
  review/
    __init__.py                # 占位
  cli/
    __init__.py                # 占位
  frontend/                    # 占位（将来搬）

tests/gaia/
  libs/models/                 # 模型单元测试
  libs/storage/                # 存储集成测试
  core/                        # 算法单元+集成测试
  lkm/                         # ingest + API 测试
  fixtures/
    graphs.py                  # galileo/newton/einstein 图构造器
    parameterizations.py       # 参数 fixture
  test_e2e_pipeline.py         # 端到端集成测试
```

## 5. 测试策略

### 5.1 测试金字塔

| 层 | 测试类型 | 依赖 | 重点 |
|----|---------|------|------|
| models | 单元测试 | 无 | 锁定 Graph IR spec 的每个约束 |
| storage | 集成测试 | LanceDB (tmp_path)，Neo4j (标记跳过) | 读写 roundtrip，三写入原子性 |
| core | 单元+集成 | fixtures，StubEmbeddingModel | §3.1 决策规则、BP 正确性 |
| lkm/ingest | 集成测试 | storage + core | 端到端写入路径 |
| lkm/services | E2E | 全栈 (httpx + ASGITransport) | HTTP roundtrip smoke test |

### 5.2 Fixtures

- 使用现有 galileo/newton/einstein 例子构造 `LocalCanonicalGraph`
- galileo 的 "vacuum prediction" 和 newton 的同一 claim 内容一致，用来测跨包匹配
- 不自行编造合成数据

### 5.3 Neo4j 测试

- 标记 `@pytest.mark.neo4j`
- CI 有 Neo4j 服务就跑，没有就跳过
- 不考虑 Kuzu

## 6. 不在 scope 内

| 项目 | 原因 |
|------|------|
| Review pipeline | 本期手工提供参数，review 是独立模块 |
| Curation | 后续 plan |
| Search | 后续 plan |
| CLI 迁移 | 合作者 scope |
| BP 迁移 | 桥接即可，独立 plan |
| 前端 | 后续 plan |
| 旧代码删除 | 新 pipeline 跑通后再统一清理 |

## 7. 验收标准

1. `pytest tests/gaia/` 全部通过（不含 neo4j 标记的测试）
2. 端到端测试 `test_e2e_pipeline.py` 通过：galileo + newton + einstein 三个包 ingest → global BP → 输出有效 BeliefState
3. `python -m gaia.lkm.pipelines.run_full --input-dir <dir> --clean` 能在真实 fixture 上跑通
4. FastAPI 服务能启动，`/health` 返回 200，`POST /api/packages/ingest` 能接受 LocalCanonicalGraph 并返回结果
5. 所有新模型的 JSON 序列化与 `docs/foundations/graph-ir/` 中的示例结构一致
