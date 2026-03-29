# 去中心化架构

> **Status:** Current canonical

本文档是 Gaia 去中心化包管理和推理架构的总纲。具体的业务流程见各子文档。

## 参与者

| 参与者 | 性质 | 职责 |
|--------|------|------|
| **作者**（人类或 AI agent） | 用户侧 | 创建知识包，声明依赖，编译，本地推理，发布 |
| **Reviewer**（人类或 AI agent） | 用户侧 | 审核新证据，判定推理关系，赋予参数 |
| **作者的 GitHub 仓库** | 用户侧 | 托管知识包源码和编译产物 |
| **Official Repo**（官方注册仓库） | GitHub | 注册所有包的元数据，存储审核记录和推理结果 |
| **Review Service** | LKM 服务器 | 为 reviewer 提供工具支持，自动化部分审核决策 |
| **Curation Service** | LKM 服务器 | 自动发现包之间的关系，以提交新包的方式维护 official repo |

## GitHub 作为通用交互面

所有参与者通过 GitHub 交互——一切都是 git commit，一切通过 PR，一切可审计：

| 参与者 | 交互方式 |
|--------|---------|
| 作者 | git push 到自己的包仓库；向 official repo 请求注册 |
| Reviewer | 向 official repo 提交 review PR |
| Review Service | 自动验证 review PR 的合规性；为 reviewer 提供建议 |
| Curation Service | 向 official repo 提交 curation PR（发现的关系、合并提议等） |

服务器上的 Review Service 和 Curation Service **没有特殊权限**——它们和普通贡献者一样通过 PR 与 official repo 交互。

## 整体架构图

```mermaid
graph TB
    %% ── Layer 2: LKM Server ──────────────────────────
    subgraph L2["<b>Layer 2 · LKM Server</b>"]
        direction TB
        RS["Review Service<br/><i>为 reviewer 提供工具<br/>自动验证 review 合规性</i>"]
        CS["Curation Service<br/><i>自动发现跨包关系<br/>语义重复 · 矛盾 · 跨包连接</i>"]
        GBP["全局推理引擎<br/><i>十亿节点 · 定期全量<br/>跨 Registry 传播</i>"]
    end

    %% ── Layer 1: Official Repo ───────────────────────
    subgraph L1["<b>Layer 1 · Official Repo（GitHub 仓库）</b>"]
        direction TB
        OR["Official Repo<br/><i>包注册信息 · 审核记录<br/>推理结果 · 合并记录</i>"]
        CI["CI Workflows<br/><i>register.yml 编译重现<br/>review.yml 合规检查<br/>incremental-bp.yml</i>"]
        PQ["待审队列<br/><i>新推理链默认不生效<br/>等待 reviewer 审核</i>"]
        IBP["增量推理<br/><i>局部子图重算<br/>秒级响应</i>"]
    end

    %% ── Layer 0: Package（用户侧）────────────────────
    subgraph L0["<b>Layer 0 · Package（用户侧 · 完全自治）</b>"]
        direction TB
        Author["👤 作者<br/><i>人类或 AI agent</i>"]
        Reviewer["👤 Reviewer<br/><i>人类或 AI agent</i>"]
        PKG["包仓库（git repo）<br/><i>源码 · 编译产物 · 依赖</i>"]
        Build["gaia build<br/><i>确定性编译<br/>源码 → 推理图</i>"]
        Infer["gaia infer<br/><i>本地概率推理<br/>可信度预览</i>"]
    end

    %% ── Layer 0 内部流 ───────────────────────────────
    Author -->|"创建 · 编写"| PKG
    PKG -->|"源码 + 依赖"| Build
    Build -->|"推理图"| Infer
    Infer -->|"可信度预览"| Author

    %% ── Layer 0 → Layer 1 ────────────────────────────
    Author -->|"① 请求注册<br/>（@GaiaRegistrator）"| OR
    OR -->|"② CI 验证<br/>编译重现 · 依赖可解析"| CI
    CI -->|"③ 等待期 → 合并"| OR
    OR -->|"④ 去重<br/>embedding 匹配"| PQ

    %% ── Review 流 ────────────────────────────────────
    RS -.->|"展示上下文 · 建议"| Reviewer
    Reviewer -->|"⑤ 提交 review PR<br/>判定关系 · 赋参数"| OR
    RS -.->|"验证合规性"| OR
    OR -->|"⑥ review 合并"| IBP
    IBP -->|"更新可信度"| OR

    %% ── Curation 流 ──────────────────────────────────
    CS -->|"⑦ 发现关系 →<br/>提交 curation PR<br/>或注册新包"| OR
    Reviewer -->|"审核 curation PR"| OR

    %% ── 全局推理 ─────────────────────────────────────
    OR -->|"推理结果同步"| GBP
    GBP -->|"⑧ 全局可信度<br/>更新回写"| OR

    %% ── 可信度回流 ──────────────────────────────────
    OR -.->|"下游拉取<br/>最新可信度"| Infer

    %% ── 样式 ─────────────────────────────────────────
    style L0 fill:#e8f5e9,stroke:#388e3c,stroke-width:2px
    style L1 fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    style L2 fill:#fce4ec,stroke:#c62828,stroke-width:2px
    style Author fill:#fff,stroke:#388e3c
    style Reviewer fill:#fff,stroke:#388e3c
    style PKG fill:#fff,stroke:#388e3c
    style Build fill:#fff,stroke:#388e3c
    style Infer fill:#fff,stroke:#388e3c
    style OR fill:#fff,stroke:#1565c0
    style CI fill:#fff,stroke:#1565c0
    style PQ fill:#fff,stroke:#1565c0
    style IBP fill:#fff,stroke:#1565c0
    style RS fill:#fff,stroke:#c62828
    style CS fill:#fff,stroke:#c62828
    style GBP fill:#fff,stroke:#c62828
```

**图例：** 实线箭头 = 数据/控制流，虚线箭头 = 辅助/拉取。编号 ①–⑧ 标注主流程顺序。

## 三层分离

```
Layer 0: Package（作者的 git 仓库，完全自治）
Layer 1: Official Repo（GitHub 仓库，可选的聚合层）
Layer 2: LKM Server（Review Service + Curation Service + 全局推理）
```

- **Layer 0** 是基础——两个人各建一个包，互相引用，就能在本地推理中让可信度流动。
- **Layer 1** 提供跨包的去重、审核记录和增量推理。
- **Layer 2** 提供自动化审核、策展和十亿节点的全局推理。

每一层都是可选增强。用户可以只用 Layer 0 完全离线工作。

## 业务流程总览

上图中的编号对应以下主流程：

| 步骤 | 描述 | 详见 |
|------|------|------|
| ① 请求注册 | 作者 release tag 后向 Official Repo 请求注册 | [authoring-and-publishing.md](authoring-and-publishing.md) |
| ② CI 验证 | 编译重现、依赖可解析、Schema 合法 | [registry-operations.md](registry-operations.md) |
| ③ 等待期 → 合并 | 新包 3 天，版本更新 1 小时 | [registry-operations.md](registry-operations.md) |
| ④ 去重 | embedding 匹配，区分前提引用 vs 独立结论 | [registry-operations.md](registry-operations.md) |
| ⑤ Reviewer 审核 | 判定独立/重复/细化，赋予推理参数 | [review-and-curation.md](review-and-curation.md) |
| ⑥ 触发增量推理 | 局部子图重算，秒级更新可信度 | [belief-flow-and-quality.md](belief-flow-and-quality.md) |
| ⑦ Curation 发现 | 语义重复、跨包连接、矛盾检测 | [review-and-curation.md](review-and-curation.md) |
| ⑧ 全局推理 | 十亿节点全量推理，跨 Registry 传播 | [belief-flow-and-quality.md](belief-flow-and-quality.md) |

各环节的详细业务逻辑：

- [包的创建与发布](authoring-and-publishing.md) — 作者从创建包到发布的完整旅程
- [Official Repo 的运作](registry-operations.md) — 注册、去重、待审队列
- [审核与策展](review-and-curation.md) — Review Service 和 Curation Service 的业务逻辑
- [多级推理与质量涌现](belief-flow-and-quality.md) — 三级推理、错误修正、质量如何涌现

## 设计原则

| 原则 | 体现 |
|------|------|
| 包即 git 仓库 | 不依赖任何中心服务 |
| GitHub 是通用协议 | 作者、reviewer、服务全部通过 PR 交互 |
| Official Repo 可选 | 增值服务，不是基础设施；可 fork 可联邦 |
| 服务器无特权 | Review Service 和 Curation Service 通过 PR 贡献，和人类一样 |
| 新证据默认静默 | 未经审核的推理不影响结果，reviewer 确认后激活 |
| 模糊判断归 review | 独立性、重复性等需要理解推理过程的判断由 reviewer 决定 |
| 多级推理 | 包级 + Official Repo 增量 + LKM 全局，各层各司其职 |
| 错误可修正 | 合并重复命题 + 暂停受影响的推理 + re-review |

## 参考文献

- [architecture-overview.md](architecture-overview.md) — 三层编译管线（Gaia Lang → Gaia IR → BP）
- [product-scope.md](product-scope.md) — 产品定位（CLI 优先，服务器增强）
