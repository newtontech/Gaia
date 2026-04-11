---
name: render-obsidian
description: "Use when user wants a browsable Obsidian wiki from a Gaia knowledge package — generates skeleton, rewrites all pages as rich knowledge documents from IR and original sources, audits cross-references."
---

# Render Obsidian Wiki

Generate a rich, browsable Obsidian vault (`gaia-wiki/`) from a Gaia knowledge package. The agent drives the full pipeline: skeleton generation, full rewrite into human-readable knowledge documents, and cross-reference audit.

## Full Pipeline

```
/gaia:render-obsidian
  ↓
Step 1: gaia compile + gaia infer (if review exists)
Step 2: gaia render --target obsidian → gaia-wiki/ skeleton
Step 3: Read inputs (IR, beliefs, artifacts/, DSL source)
Step 4: Rewrite every page as a complete knowledge document
Step 5: Cross-reference audit
Step 6: Report
```

## Step 1: Ensure Compile + Infer

```bash
gaia compile .
ls reviews/ && gaia infer .   # run inference if review exists
```

## Step 2: Generate Skeleton

```bash
gaia render . --target obsidian
```

This produces `gaia-wiki/` with YAML frontmatter, wikilinks, and Mermaid graphs on every page. The skeleton provides **structure only** — all prose content will be rewritten by the agent.

## Step 3: Read Inputs

Read thoroughly before writing:

```bash
cat .gaia/ir.json                          # Full IR
cat .gaia/reviews/*/beliefs.json           # BP results
cat .gaia/reviews/*/parameterization.json  # Priors + strategy params
cat src/<package>/*.py                     # DSL source (claims, reasons, strategies)
ls artifacts/                              # Original paper, figures, data
```

Read the original source material in `artifacts/` cover-to-cover. The agent must understand the paper's argument, data, and figures before writing any page.

## Step 4: Rewrite Every Page

**Core principle:** The skeleton is scaffolding, not content. The agent rewrites every page into a complete, self-contained knowledge document. After reading a page, the reader should understand the topic **without needing the original source**.

**Language:** Follow the user's language. If the user speaks Chinese, write all prose in Chinese. Frontmatter keys, wikilinks `[[label]]`, and Mermaid diagrams stay in English (they are structural identifiers).

### What to preserve vs rewrite

| Element | Action |
|---------|--------|
| YAML frontmatter | **Preserve exactly** — never modify |
| Wikilinks `[[label]]` | **Preserve exactly** — never change targets |
| Mermaid diagrams | **Preserve exactly** |
| `.obsidian/graph.json` | **Preserve exactly** |
| Section headings (`## Derivation`, etc.) | **Translate** to user's language |
| Claim content blockquotes (`> ...`) | **Rewrite** — expand terse claims into full explanations |
| `> [!REASONING]` callouts | **Rewrite** — translate and expand the reasoning |
| Premise/conclusion lists | **Rewrite** — keep wikilinks but add explanatory text |
| Everything else | **Write from scratch** |

### Per-page rewrite guide

#### Conclusion pages (`conclusions/*.md`)

Rewrite into a complete article about this claim:

**Completeness standard:** Each page should contain ALL information from the original source that is relevant to its topic. The reader should never need to go back to the paper. Don't aim for a word count — aim for information completeness. A claim that involves a 3-page derivation in the paper needs a proportionally detailed explanation in the wiki.

1. **Title**: Keep or translate the `# heading`
2. **Content**: Replace the terse blockquote with a full explanation of the claim — what it states, what evidence supports it, what method produced it. Include ALL relevant numbers, equations, experimental conditions, and comparisons from the original source. If the paper devotes a paragraph to this claim, the wiki page should contain equivalent information.
3. **Derivation**: Rewrite in prose. Don't just list premises — explain the complete logical chain: WHY each premise supports this conclusion, what the mathematical/physical argument is. Keep wikilinks but wrap them in explanatory sentences. Reproduce key equations from the paper.
4. **Supports**: Rewrite as prose — what downstream conclusions depend on this claim and why.
5. **Context**: Explain the claim's full scientific context from `artifacts/`. Embed all relevant figures with `![[filename]]` and informative captions. Include experimental setup, measurement methods, data tables, comparison with prior work.
6. **Significance**: Why this matters for the overall argument. What breaks if this claim is wrong?
7. **Caveats**: Limitations, alternative explanations, sources of uncertainty.

#### Evidence pages (`evidence/*.md`)

Rewrite into a complete source documentation page:

1. **Content**: Fully describe the evidence — not a one-liner but the complete statement with all quantitative details.
2. **Source**: Where does this evidence come from? Reproduce the relevant data: experimental method, measurement conditions, precision, error bars, known limitations. If the paper has a table or figure for this data, embed it.
3. **Supports**: Which conclusions depend on this evidence and why — the logical connection, not just a list.
4. **Figures**: Embed all relevant figures from `artifacts/images/`.

#### Module pages (`modules/*.md`)

Rewrite into a comprehensive chapter overview:

1. **Overview**: What scientific question this module addresses, what approach is taken, and the key results. Write as you would a section of a review paper — the reader should understand the module's complete contribution.
2. **Transition**: How this module builds on previous modules and what it enables for subsequent ones. Name specific concepts and results that flow between modules.
3. **Claims section**: For each claim:
   - Exported claims: expand into a substantive summary with key numbers and the reasoning behind them.
   - Inlined claims: rewrite the content and derivation into readable prose with full explanations. Include equations, data, and physical reasoning — not just "Derived via X from Y."

#### Strategy pages (`reasoning/*.md`)

Rewrite into a complete reasoning explanation:

1. **Overview**: What type of reasoning and what it establishes.
2. **Premises → Conclusion**: For each premise, explain the full scientific argument for WHY it supports the conclusion. Reproduce the mathematical derivation or physical reasoning from the paper.
3. **Strength assessment**: How strong is this reasoning? What assumptions does it depend on? What could weaken it?

#### Overview page (`overview.md`)

1. **Citation**: Proper bibliographic reference to original work.
2. **Abstract**: A comprehensive summary of the entire package — central question, methodology, key quantitative results, limitations. The reader should be able to decide whether to explore further.
3. **Reasoning graph**: Keep the Mermaid diagram as-is.

Target: 300-500 words.

#### `_index.md`

Add a package description (3-5 sentences) with the most striking quantitative results. Keep all statistics tables and navigation as-is.

#### Meta pages (`meta/*.md`)

- `beliefs.md`: Add a brief introduction explaining what the table shows.
- `holes.md`: Add a brief introduction explaining what leaf premises are and why they matter.

### Quality bar

**The standard is information completeness, not word count.** If the paper devotes 2 pages to a topic, the wiki page should contain equivalent depth. If a claim is a single well-known fact, a short page is fine. Length follows content, not a target.

**Every page must include:**
- ALL relevant numerical values from the original source (with units, error bars)
- Key equations in LaTeX — reproduce derivations where they are central to the argument
- Cross-references via wikilinks to related pages
- Figure embeds from `artifacts/images/` for every figure relevant to the topic

**BAD — thin rewrite:**
```
## 背景
铝的 r_s = 2.07，预测 T_c = 0.96 K，接近实验值 1.2 K。
```

**GOOD — rich rewrite:**
```
## 背景

铝是超导理论的基准测试材料。Wigner-Seitz 半径 $r_s = 2.07$，
带质量 $m_b = 1.05$，处于弱耦合区间。声子吸引（$\lambda = 0.44$，
来自 DFPT 计算，$\omega_{\log} = 320$ K）与 Coulomb 排斥
（$\mu^* = 0.13$，来自 [[mu_vdiagmc_values]] 在 $r_s = 2.07$
处的值经 BTS 重正化）之间的竞争仅留下很小的净配对相互作用。

唯象方法预测 $T_c = 1.9$ K，比实验值 1.2 K 高估 58%——根本
原因是传统取值 $\mu^* \approx 0.10$ 低估了 Coulomb 排斥。
第一性原理值 $\mu^* = 0.13$ 恰好增大了足够的排斥，将 $T_c$
降低到 0.96 K，偏差在 20% 以内。

![[8_0.jpg]]
*图 4：vDiagMC 计算的 $\mu_{E_F}(r_s)$（圆圈带误差棒），
与静态 RPA（虚线）、动态 RPA（点线）和 Morel-Anderson 常数
（点划线）的对比。改编自 Cai et al., arXiv:2512.19382。*
```

### DO NOT

- Leave any page with only skeleton English content
- Write thin summaries — every page should be a substantive knowledge document
- Use Gaia jargon (noisy_and, abduction, factor graph, BP, NAND)
- Describe graph structure ("this claim derives from two premises via...")
- Modify frontmatter or wikilink targets
- Skip evidence pages — they are important for completeness

### Handling missing information

| Missing | Action | Annotation |
|---------|--------|------------|
| Terse claim (< 20 words) | Read `artifacts/`, find relevant section, write full explanation | `> [!NOTE] 内容根据原文扩展` |
| No `reason` in strategy | Reconstruct from premises + source | `> [!NOTE] 推理根据原文重构` |
| No beliefs | Write structural description, note gap | `> [!WARNING] 未运行推断` |
| No `artifacts/` | Write from IR only, note prominently | `> [!WARNING] 原始文献不可用` |

## Step 5: Cross-Reference Audit

```bash
grep -roh '\[\[[^]]*\]\]' gaia-wiki/ | sort -u | while read link; do
  name=$(echo "$link" | sed 's/\[\[//;s/\]\]//' | sed 's/#.*//' | sed 's/|.*//')
  if ! find gaia-wiki -name "${name}.md" | grep -q .; then
    echo "BROKEN: $link"
  fi
done
```

## Step 6: Report

```
Obsidian wiki: gaia-wiki/
- X pages total (Y conclusions, Z evidence, W modules)
- All pages rewritten in [language]
- Figures embedded: M
- Broken wikilinks: 0

Open in Obsidian: File → Open Vault → select gaia-wiki/
```
