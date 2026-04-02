# 包模型

> **Status:** Current canonical for Gaia Lang v5 Phase 1
>
> **Canonical spec:** [../../specs/2026-04-02-gaia-lang-v5-python-dsl-design.md](../../specs/2026-04-02-gaia-lang-v5-python-dsl-design.md)

本文档描述当前 Gaia Lang v5 的作者侧包模型。当前模型是一个 Python package + `.gaia/` 编译产物 + GitHub source release，而不是旧的 Typst project / local database workflow。

## Package

Package 是一个版本化的知识源码仓库，也是注册的基本单位。

- **源码形态：** 标准 Python repository
- **身份：** `name + version + namespace + uuid`
- **权威元数据：** `pyproject.toml`
- **编译产物：** `.gaia/ir.json` 和 `.gaia/ir_hash`
- **外部发布边界：** pushed GitHub commit + pushed git tag

最小形态通常是：

```text
my-package/
  pyproject.toml
  src/
    my_package/
      __init__.py
      ...
  .gaia/
    ir.json
    ir_hash
```

`[tool.gaia]` 当前至少应包含：

- `namespace`
- `uuid`

## Module

当前的 Module 就是普通 Python module。

- `src/<import_name>/__init__.py` 通常是 DSL 入口
- 作者可以把前提、推理链、辅助声明拆到多个 `.py` 文件
- 编译器按 Python import 执行这些声明，而不是按 Typst module 做抽取

Module 的作用是组织源码，不构成独立的推理边界。编译后的 graph 仍然是单个 package-local graph。

## Knowledge / Strategy / Operator

Package 执行时会收集三类运行时对象：

- `Knowledge`
- `Strategy`
- `Operator`

这些对象由 `with Package(...) as pkg:` 作用域中的 DSL 调用注册进包上下文，然后由 `gaia compile` 降低为 Gaia IR。

```python
from gaia.lang import Package, claim, contradiction, deduction, setting


with Package("galileo_falling_bodies", namespace="reg", version="4.0.3") as pkg:
    vacuum = setting("The experiment is conducted in a vacuum.")
    observation = claim("Objects of different mass fall at the same rate in a vacuum.")
    conclusion = claim("Mass alone does not determine falling speed.")

    deduction(
        premises=[vacuum, observation],
        conclusion=conclusion,
        reason="The controlled observation removes drag as a confounder.",
    )

    contradiction(
        variables=[conclusion, claim("Heavier bodies necessarily fall faster.")],
        reason="The two claims cannot both be true under the same experimental setup.",
    )
```

## 生命周期

当前作者侧生命周期是：

```text
authored
  -> compiled   (gaia compile)
  -> checked    (gaia check)
  -> tagged     (git push + git tag)
  -> registered (gaia register -> registry PR merged)
```

说明：

- `gaia compile` 只生成结构化 IR，不做推理或数据库摄入
- `gaia check` 只验证结构和注册前提
- `gaia register` 只创建或提交 registry metadata PR
- 官方 registry 当前是 source registry，不负责 wheel 发布

## Source Release

当前 official registry 注册的是一个可重建的 GitHub source release，而不是本地目录快照。

每个已注册版本都需要：

- package repo URL
- git tag
- pinned git SHA
- `ir_hash`
- dependency metadata

registry CI 会重新 clone 该 source release，重新运行 `gaia compile` 和 `gaia check`，然后再决定是否接受该版本。

## Historical Note

旧的 Typst-based package model、`gaia build` / `gaia infer` / `gaia publish`、本地 LanceDB/Kuzu 发布流都属于更早期的设计探索，不是当前 Gaia Lang v5 Phase 1 的 canonical package model。
