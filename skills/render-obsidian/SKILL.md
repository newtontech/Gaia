---
name: render-obsidian
description: "Use when user wants a browsable Obsidian wiki from a Gaia knowledge package — generates skeleton, rewrites all pages as rich knowledge documents from IR and original sources, audits cross-references."
---

# Render Obsidian Wiki

Generate a rich, browsable Obsidian vault (`gaia-wiki/`) from a Gaia knowledge package. The agent drives the full pipeline: skeleton generation, full rewrite into human-readable knowledge documents, and cross-reference audit.

## Vault Architecture

```
gaia-wiki/
├── claims/                 One page per claim, numbered by topological order
│   ├── 01 - BCS Theory.md              (layer 0, leaf premise)
│   ├── ...
│   └── 59 - Tc Prediction.md ★         (highest layer, exported conclusion)
├── modules/                Chapter-level narrative, numbered by paper order
│   ├── 01 - Introduction.md
│   └── ...06 - Results.md
├── meta/                   beliefs table, holes list
├── _index.md               Master index with numbered claim table
├── overview.md             Simplified Mermaid reasoning graph
└── .obsidian/              Graph view config
```

**Claims** are the atomic content units. Each has a topological order number — small numbers are leaf premises (evidence), large numbers are final conclusions. Reasoning/derivation is embedded in the claim page.

**Modules** are reading chapters. They provide human-readable narrative organized by claim numbers, with per-module Mermaid graphs. Modules link to claim pages — they don't duplicate full derivations.

**Wikilinks** use stable labels (`[[tc_al_predicted]]`). Filenames use titles (`Tc(Al) Ab Initio Prediction.md`). Obsidian `aliases` in frontmatter bridge labels to filenames.

## Full Pipeline

```
/gaia:render-obsidian
  ↓
Step 1: gaia compile + gaia infer (if review exists)
Step 2: gaia render --target obsidian → gaia-wiki/ skeleton
Step 3: Read inputs (IR, beliefs, artifacts/, DSL source, review sidecar)
Step 4: Rewrite every page as a complete knowledge document
Step 5: Cross-reference audit
Step 6: Report
```

## Step 1: Ensure Compile + Infer

```bash
gaia compile .
ls reviews/ && gaia infer .
```

## Step 2: Generate Skeleton

```bash
gaia render . --target obsidian
```

Produces numbered claim pages + module pages with frontmatter, wikilinks, and Mermaid graphs. The skeleton provides **structure only**.

## Step 3: Read Inputs

```bash
cat .gaia/ir.json                          # Full IR
cat .gaia/reviews/*/beliefs.json           # BP results
cat .gaia/reviews/*/parameterization.json  # Priors + strategy params
cat src/<package>/*.py                     # DSL source (claims, reasons, strategies)
cat src/<package>/reviews/*.py             # Review sidecars (justifications!)
ls artifacts/                              # Original paper, figures, data
```

Read `artifacts/` cover-to-cover. Read the review sidecar for `justification` fields.

## Step 4: Rewrite Every Page

**Core principle:** The skeleton is scaffolding. The agent rewrites every page so the reader understands the topic **without needing the original source**.

**Language:** Follow the user's language. Frontmatter keys, wikilinks `[[label]]`, and Mermaid stay in English (structural identifiers).

### Claim pages (`claims/*.md`)

Each claim page is a self-contained article. The claim number in the title shows its position in the reasoning chain.

**Completeness standard:** Faithful reproduction of the paper's treatment, not a summary. If the paper devotes 3 pages to a derivation, reproduce them in readable form.

**Section ordering:**

1. **Title**: Write descriptive title in user's language. Keep the `#XX` number prefix. Filename stays unchanged (wikilinks not affected).
2. **Content**: Expand the blockquote into a full explanation with all numbers, equations, conditions.
3. **Background**: Complete scientific context. What problem? What's known? What gap? Embed relevant figures with `![[filename]]` + italic caption.
4. **Derivation** (核心): Reproduce the paper's full argument:
   - All key equations with step-by-step explanation
   - Physical reasoning behind each step
   - Approximations and why they're justified
   - Numerical validations
   - Appendix material
   - Keep wikilinks (with claim numbers: `[[label|#XX label]]`)
5. **Review**: Prior value + justification from review sidecar. Posterior belief from BP.
   - Format: `**Prior**: 0.95 — "Migdal theorem validated for ωD/EF ~ 0.005"`
6. **Supports**: Downstream claims that depend on this one.
7. **Significance**: Why this matters. What breaks if wrong?
8. **Caveats**: Limitations, alternatives, uncertainties.

### Module pages (`modules/*.md`)

Modules are **narrative chapters** organized by claim numbers. They tell the paper's story.

1. **Overview**: 2-3 paragraphs — scientific question, approach, key results. Write as a review paper section.
2. **Transition**: How this module connects to previous/next modules.
3. **Per-module Mermaid**: Keep as-is.
4. **Claims list**: For each claim in this module, provide a brief summary (2-3 sentences with key numbers) linking to the full claim page via `[[label|#XX title]]`. Don't duplicate full derivations here.

### Overview page

1. **Citation**: Bibliographic reference.
2. **Abstract**: Comprehensive summary (central question, methodology, results, limitations).
3. **Mermaid**: Keep simplified graph as-is.

### `_index.md`

Add package description. Keep statistics, Claim Index table, module table, and Reading Path.

### Meta pages

- `beliefs.md`: Chinese introduction + belief table.
- `holes.md`: Chinese introduction + leaf premises table.

### Quality bar

**Faithful reproduction, not summarization.** Rewrite the paper into a wiki, don't summarize it.

Every page must include:
- ALL relevant numerical values (with units, error bars)
- ALL key equations with explanation
- ALL derivation steps (including appendix material)
- Figure embeds with italic captions
- Cross-references with claim numbers

### Figure embeds

Every `![[filename]]` MUST have an italic caption:

```markdown
![[8_0.jpg]]
*图 4：vDiagMC 计算的 μ_{E_F}(r_s)，与 RPA 的对比。改编自 Cai et al.*
```

### DO NOT

- Leave any page with only skeleton English content
- Write thin summaries
- Use Gaia jargon (noisy_and, abduction, factor graph, BP, NAND)
- Describe graph structure ("derived from two premises via...")
- Modify frontmatter or wikilink targets
- Embed images without captions
- Duplicate full derivations in module pages (link to claim pages instead)

### Handling missing information

| Missing | Action | Annotation |
|---------|--------|------------|
| Terse claim | Expand from `artifacts/` | `> [!NOTE] 内容根据原文扩展` |
| No strategy reason | Reconstruct from source | `> [!NOTE] 推理根据原文重构` |
| No beliefs | Write structural description | `> [!WARNING] 未运行推断` |
| No artifacts | Write from IR only | `> [!WARNING] 原始文献不可用` |

## Step 5: Cross-Reference Audit

Wikilinks use labels, resolved via aliases. Check:

```bash
# Collect all aliases and filenames
all_aliases=$(grep -rh "^aliases:" gaia-wiki/ --include="*.md" | sed 's/aliases: \[//;s/\]//')
all_files=$(find gaia-wiki -name "*.md" -exec basename {} .md \;)
# Check each wikilink resolves
grep -roh '\[\[[^]!]*\]\]' gaia-wiki/ --include="*.md" | grep -v '.jpg' | \
  sed 's/\[\[//;s/\]\]//' | sed 's/#.*//' | sed 's/|.*//' | sort -u | \
  while read name; do
    echo "$all_aliases $all_files" | grep -qw "$name" || echo "BROKEN: [[$name]]"
  done
```

## Step 6: Report

```
Obsidian wiki: gaia-wiki/
- X claim pages (numbered 01-XX)
- Y module pages (numbered 01-YY)
- All pages rewritten in [language]
- Figures embedded: M
- Broken wikilinks: 0

Open in Obsidian: File → Open Vault → select gaia-wiki/
```
