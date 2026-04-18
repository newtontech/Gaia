# Quick Start

> **Status:** Current canonical

Create, build, and publish your first Gaia knowledge package in 10 minutes.

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.12+ | [python.org](https://www.python.org/downloads/) |
| uv | latest | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |

Verify both are available:

```bash
python3 --version   # 3.12+
uv --version
```

## Install Gaia

```bash
pip install gaia-lang
```

Verify:

```bash
gaia --help
```

## Create a Package

```bash
gaia init my-first-gaia
```

The name **must** end with `-gaia`. This creates:

```
my-first-gaia/
  pyproject.toml              # [tool.gaia] metadata
  src/my_first/
    __init__.py               # DSL declarations
  .gitignore
```

## Edit Your Package

Open `src/my_first/__init__.py` and replace the template:

```python
"""Galileo's argument against Aristotle's theory of falling bodies."""

from gaia.lang import claim, setting, support, contradiction

# Background: Aristotle's law
aristotle_law = setting(
    "Aristotle claims heavier objects fall faster in proportion to their weight."
)

# Thought experiment setup
thought_experiment = setting(
    "Consider a heavy ball (H) and a light ball (L). "
    "Now tie them together into a composite body (H+L)."
)

# Two contradictory predictions from Aristotle's law
composite_slower = claim(
    "Under Aristotle's law, H+L falls slower than H alone, "
    "because L acts as a drag on H.",
    title="Composite slower prediction",
    background=[aristotle_law, thought_experiment],
)

composite_faster = claim(
    "Under Aristotle's law, H+L falls faster than H alone, "
    "because H+L is heavier than H.",
    title="Composite faster prediction",
    background=[aristotle_law, thought_experiment],
)

# These two predictions contradict each other
tied_balls = contradiction(
    composite_slower, composite_faster,
    reason="The same law predicts both slower and faster — a logical contradiction.",
    prior=0.99,
)

# Galileo's conclusion
equal_fall = claim(
    "In the absence of air resistance, all objects fall at the same rate "
    "regardless of mass.",
    title="Equal fall rate",
)

support(
    [tied_balls],
    equal_fall,
    reason="Aristotle's law is self-contradictory, so fall rate cannot depend on mass.",
    prior=0.9,
)

__all__ = ["equal_fall"]
```

Key points:

- `setting()` declares background context (no probability, not debatable)
- `claim()` declares propositions that carry probability in inference
- `contradiction()` declares two claims are mutually exclusive
- `support()` connects premises to a conclusion with a strength prior
- `__all__` lists exported conclusions (the package's external interface)

## Compile

```bash
cd my-first-gaia
gaia compile .
```

This produces `.gaia/ir.json` (the compiled knowledge graph) and `.gaia/ir_hash` (integrity hash).

## Validate

```bash
gaia check .
```

Check reports structural errors, independent premises, derived conclusions, and prior coverage. Fix any errors before proceeding.

Use `gaia check --brief .` for a per-module overview, or `gaia check --hole .` for a detailed prior coverage report.

## Assign Priors

Independent premises (leaf claims not derived by any strategy) need probability priors. Create `src/my_first/priors.py`:

```python
"""Priors for independent premises."""

from . import composite_slower, composite_faster

PRIORS: dict = {
    composite_slower: (0.85, "Follows directly from Aristotle's assumption about drag."),
    composite_faster: (0.85, "Follows directly from Aristotle's weight-speed relation."),
}
```

Each entry maps a claim to `(prior_probability, justification)`. Priors range from 0 to 1.

Re-compile to pick up the priors:

```bash
gaia compile .
gaia check --hole .    # Should show "All independent claims have priors assigned"
```

## Infer

Run belief propagation to compute posterior beliefs:

```bash
gaia infer .
```

Sample output:

```
Algorithm: junction_tree (exact, treewidth=2)
Converged after 2 iterations

Beliefs:
  composite_slower:  prior=0.85  →  belief=0.42
  composite_faster:  prior=0.85  →  belief=0.42
  equal_fall:        prior=0.50  →  belief=0.72
```

The contradiction forces one side down; `equal_fall` is pulled up by the supporting evidence.

## Render

Generate documentation from the compiled package:

```bash
gaia render . --target docs
```

This produces `docs/detailed-reasoning.md` with per-module Mermaid reasoning graphs.

## Next Steps

- [Language Reference](language-reference.md) — full cheat sheet for all knowledge types, operators, and strategies
- [CLI Commands](cli-commands.md) — complete reference for all `gaia` commands
- [Hole And Bridge Tutorial](hole-bridge-tutorial.md) — cross-package dependency resolution with `fills()`
