# V1 Static Shared Knowledge Package Schema

## Purpose

This document defines the V1 static shared knowledge package schema used by both Gaia local/CLI and Gaia server.

It instantiates the shared vocabulary defined in [../domain-model.md](../domain-model.md).

It covers:

1. the core object layers used in shared Gaia knowledge packages
2. the static schema for `knowledge_artifact`, `step`, `module`, and `package`
3. the minimal subtype schemas for `claim`, `question`, `setting`, and `action`
4. the static relationships between package structure and global reusable artifacts

It does not cover:

- canonicalization
- review
- optional revision/materialization
- Gaia graph integration
- prior / belief / BP

Those belong to later documents:

- V1 file formats: shared package file formats and review-report contracts
- V2: global Gaia graph integration
- V3: probabilistic semantics and propagation

## Design Boundary

This document defines only the shared static knowledge package schema.

The key split is:

- `knowledge_artifact` is global and reusable
- `step` is a local occurrence of one knowledge artifact, with explicit logical dependencies
- `module` groups related steps into a single reasoning unit with one conclusion
- `package` is a reusable container of modules

The document intentionally does not define where any object is stored. It defines only the logical structure.

## Core Model

Gaia V1 static structure has four layers:

1. global `knowledge_artifact`
2. local `step`
3. local `module`
4. local `package`

The main idea is:

- reusable content and reusable actions are global `knowledge_artifact`s
- a `step` is one use of a knowledge artifact, with explicit `input` dependencies (strong or weak)
- a `module` groups related steps into a coherent reasoning thread that establishes exactly one conclusion claim — analogous to a module in a codebase
- a `package` contains one or more modules, analogous to a paper or research bundle
- logical dependencies are fully captured by `input` declarations on steps, not by narrative ordering
- the logical structure of a module is a hypergraph: each step's strong inputs jointly form the premises of a reasoning link to that step's conclusion

## Object Overview

### 1. Knowledge Artifact

A `knowledge_artifact` is a globally reusable object.

Current artifact kinds are:

- `claim`
- `question`
- `setting`
- `action`

V1 keeps this artifact set intentionally minimal.

More detailed epistemic distinctions such as `observation` and `assumption` are deferred to later graph and probabilistic layers. In V1 they are represented through `claim` or `setting` plus provenance and review context.

### 2. Step

A `step` is one local occurrence of a `knowledge_artifact` inside a module.

Steps are needed because:

- the same global knowledge artifact may appear in multiple modules and packages
- the same knowledge artifact may have different logical dependencies in different contexts
- logical dependencies (strong/weak) belong to the step, not to the global knowledge artifact

Each step declares its own `input` dependencies explicitly. There are no implicit dependencies from narrative ordering.

### 3. Module

A `module` groups related steps into a single reasoning unit.

Each module establishes exactly one conclusion (a `claim` artifact). This is analogous to a module in a codebase — it groups related logic and has a clear output.

The logical structure within a module is a **hypergraph**: each step with strong inputs implicitly defines a reasoning link where the strong input artifacts are the **premises** and the step's own artifact is the **conclusion**. This hypergraph is not declared as a separate object — it is derived from the step `input` declarations.

Modules within the same package can reference each other's steps or artifacts.

### 4. Package

A `package` is a reusable container of modules.

It corresponds to a paper, research bundle, project unit, structured note, or another portable knowledge package.

## Common Knowledge Artifact Schema

All knowledge artifacts share the following minimal structure:

```text
artifact_id
artifact_kind
content
content_mode = nl (default)
summary?
metadata?
embedding?
```

### `artifact_id`

Stable global identifier.

V1 should treat `artifact_id` as globally unique even when artifacts are first created locally.

Recommended shape:

```text
ka_<uuidv7>
```

The recommended rule is:

- use an opaque globally unique id as the primary artifact identity
- generate it locally at creation time
- do not use content hash as the primary id

If later layers need semantic deduplication or merge suggestions, they should use separate fingerprints rather than rewriting `artifact_id`.

### `artifact_kind`

Exactly one of:

- `claim`
- `question`
- `setting`
- `action`

### `content`

The canonical primary payload of the knowledge artifact.

### `content_mode`

Single-valued mode describing the canonical primary representation.

Default:

- `nl`

Common explicit values:

- `python`
- `lean`
- `config`

V1 keeps exactly one canonical primary representation per knowledge artifact.

### `summary`

Optional short human-readable summary.

### `metadata`

Optional extensible metadata container.

Suggested minimal shape:

```text
refs[]?
extra{}?
```

`refs[]` should point only to external resources such as papers, files, datasets, images, tables, or execution artifacts.

### `embedding`

Optional retrieval embedding.

## Claim

A `claim` is a truth-apt statement or result object that can be supported, challenged, or reused.

Examples:

- a natural-language scientific statement
- a gap statement written as a declarative sentence
- a Python code result
- a Lean theorem or proof artifact treated as a reusable result object

### Claim Schema

```text
claim {
  artifact_id
  artifact_kind = claim
  content
  content_mode = nl (default)
  summary?
  metadata?
  embedding?
}
```

### Modeling rule

- if the content is a statement-like result, model it as a `claim`
- do not put local roles such as `premise`, `context`, or `conclusion` on the claim itself

Those roles, when needed, belong to later local reasoning or review layers, not to the global claim object.

## Question

A `question` is an inquiry object. It is not a truth-apt statement.

Examples:

- "Why do a feather and a stone fall at different rates in air?"
- "Can this implementation be proven correct in Lean?"

### Question Schema

```text
question {
  artifact_id
  artifact_kind = question
  content
  content_mode = nl (default)
  summary?
  metadata?
  embedding?
}
```

### Modeling rule

- if the content is a genuine question, model it as a `question`
- if the content is a statement-form problem or gap, model it as a `claim`

## Setting

A `setting` is a context-setting object. It specifies the background under which later reasoning should be interpreted or executed.

Examples include:

- definitions
- logical assumptions or model setup
- execution environments
- experimental environments

### Setting Schema

```text
setting {
  artifact_id
  artifact_kind = setting
  setting_type
  content
  content_mode = nl (default)
  summary?
  metadata?
  embedding?
}
```

### `setting_type`

Recommended initial values:

- `definition`
- `logical_setup`
- `execution_environment`
- `experimental_environment`
- `other`

### Modeling rule

- if the object mainly sets the background for later reasoning, model it as a `setting`
- if the object mainly asserts that some fact is true, model it as a `claim`

Example:

- "This analysis adopts a near-vacuum model." -> `setting`
- "The experiment was in fact run in a near-vacuum chamber." -> `claim`

## Action

An `action` is a reusable atomic process object.

It represents a process such as inference, tool use, or another canonicalized local step.

The action itself is global; a specific use of the action inside a package is represented by a `step`.

### Action Schema

```text
action {
  artifact_id
  artifact_kind = action
  action_type
  content
  content_mode = nl (default)
  summary?
  tool_name?
  metadata?
  embedding?
}
```

### `action_type`

Recommended initial values:

- `infer`
- `tool_call`
- `other`

### `tool_name`

Optional stable tool identifier for `tool_call` actions.

Package-specific execution details such as concrete inputs, outputs, runtime context, and artifacts should not be placed on the global action object. They belong to the local step occurrence.

## Step

A `step` is one local occurrence of a global knowledge artifact inside a module.

### Step Schema

```text
step {
  step_id
  artifact_id
  input[]?
  metadata?
}
```

### `step_id`

Stable local identifier inside the module.

### `artifact_id`

Reference to a global knowledge artifact.

### `input[]`

Explicit logical dependencies of this step.

```text
input: [
  {
    ref,          # step_id or artifact_id
    strength,     # strong | weak
    note?
  }
]
```

**Dependency semantics:**

- **strong** — if the referenced artifact is wrong, this step is likely wrong too. This is a logical dependency that affects truth value.
- **weak** — the referenced artifact is relevant context, but this step can stand on its own even if the reference is wrong.

**Reference types:**

- `ref` may be a `step_id` (local to the same package) or an `artifact_id` (global, including cross-package references)
- a `step_id` reference can always be resolved to its underlying `artifact_id`
- cross-package references must use `artifact_id`

**Rules:**

- all logical dependencies must be declared explicitly via `input`
- the narrative ordering of steps does NOT imply any dependency
- a step with no `input` is a leaf (starting point of the reasoning)

### `metadata`

Optional local occurrence metadata.

This is the right place for package-specific details such as:

- local notes
- concrete tool invocation details
- local execution context
- local artifact references

## Module

A `module` groups related steps into a single reasoning unit that establishes one conclusion.

### Module Schema

```text
module {
  module_id
  summary?
  keywords[]?
  conclusion_artifact_id
  steps[]
  metadata?
}
```

### `module_id`

Stable identifier for the module within the package.

### `summary`

Optional short human-readable summary of what this module establishes.

### `keywords`

Optional keywords for search and discovery.

### `conclusion_artifact_id`

The single `claim` artifact that this module establishes. Every module must have exactly one conclusion, and it must be a `claim`.

If a reasoning thread naturally has multiple conclusions, split it into multiple modules.

### `steps[]`

Ordered list of steps representing the narrative flow of this module.

**Narrative ordering:**

- the list defines the recommended reading order for understanding the reasoning
- adjacent steps may be logically unrelated (the narrative can have "breaks")
- the ordering should not reverse the logical flow: conclusions should not precede their premises in the narrative
- this ordering carries no implicit logical dependency; all dependencies are declared via `input` on each step

**Starting points are derived:** steps with no `input` are leaves (premises, observations, questions that begin the reasoning).

**Reasoning gap rule:** if there is a nontrivial logical gap between two artifacts in the reasoning, it should be made explicit with an `action` step. If the reasoning is trivial or locally obvious, the `action` may be omitted.

### `metadata`

Optional module-level metadata.

### Implicit hypergraph structure

The logical structure of a module is a hypergraph, derived from step `input` declarations:

- for each step with strong inputs, the strong input artifacts are the **premises** and the step's own artifact is the **conclusion** of one reasoning link
- weak inputs are relevant context but do not form reasoning links
- steps with no inputs are leaves (no incoming reasoning link)

This hypergraph is not declared as a separate schema object. It is always derived from the step `input` declarations, avoiding redundancy and inconsistency.

## Package

A `package` is a container of modules.

It is the closest V1 analog of a paper, research bundle, or structured project unit.

### Package Schema

```text
package {
  package_id
  summary?
  keywords[]?
  modules[]
  motivation_artifact_ids[]?
  key_claim_ids[]?
  follow_up_question_ids[]?
  shared_setting_ids[]?
  metadata?
}
```

### `package_id`

Stable identifier for the package.

### `summary`

Optional short human-readable summary of the package.

### `keywords`

Optional keywords for search and discovery.

### `modules[]`

One or more modules included in the package. A package with multiple modules is like a paper with multiple theorems or arguments.

Modules within the same package can reference each other's steps (via `step_id`) or artifacts (via `artifact_id`).

### `motivation_artifact_ids[]`

Optional references to knowledge artifacts that motivate the package. These capture editorial intent — "why this research was done" — which is not derivable from graph structure alone.

### `key_claim_ids[]`

Optional references to the package's most important conclusion claims. Not all module conclusions are equally important; this field captures editorial judgment about which conclusions matter most.

### `follow_up_question_ids[]`

Optional references to questions that this package opens for future work.

### `shared_setting_ids[]`

Optional references to settings shared across multiple modules in the package.

### `metadata`

Optional package-level metadata.

## Static Constraints

V1 static schema assumes:

1. logical dependencies are fully captured by explicit `input` declarations on steps, not by narrative ordering
2. dependency strength (`strong` / `weak`) determines whether a reference participates in later probabilistic evaluation
3. local reasoning structure belongs to steps, not to global knowledge artifacts
4. each module establishes exactly one conclusion claim
5. the implicit logical structure within a module is a hypergraph: each step's strong inputs jointly form the premises of a reasoning link
6. knowledge artifacts are global objects referenced by steps; they are not "owned" by any package

## Example

### Knowledge artifacts

```text
q1 = question("Why do a feather and a stone fall at different rates in air?")
s1 = setting(definition, "Air resistance depends on drag and shape.")
a1 = action(infer, "Contrast vacuum behavior with air-mediated behavior.")
c1 = claim("The observed difference in air is better explained by drag than by mass-dependent gravity.")
q2 = question("How can drag be modeled quantitatively for different shapes?")
```

### Module

```text
module {
  module_id = m1
  summary = "Air resistance, not mass, explains differential fall rates"
  keywords = ["air resistance", "drag", "falling bodies"]
  conclusion_artifact_id = c1

  steps = [                        # narrative order
    s01(artifact_id=q1, input=[]),
    s02(artifact_id=s1, input=[]),
    s03(artifact_id=a1, input=[
      {ref=s01, strength=weak},    # question motivates the action, but action is valid without it
      {ref=s02, strength=strong}   # setting is required for the action to make sense
    ]),
    s04(artifact_id=c1, input=[
      {ref=s02, strength=strong},  # definition is a logical premise
      {ref=s03, strength=strong}   # action result is a logical premise
    ]),
    s05(artifact_id=q2, input=[
      {ref=s04, strength=weak}     # conclusion motivates the follow-up, but question stands on its own
    ])
  ]
}
```

Implicit hypergraph (derived from strong inputs):

```text
premises: [s1]           → conclusion: a1    (setting enables the inferential action)
premises: [s1, a1]       → conclusion: c1    (definition + action result jointly establish the claim)
```

### Package

```text
package {
  package_id = p1
  summary = "Why feathers and stones fall differently in air"
  keywords = ["falling bodies", "air resistance", "drag"]

  modules = [m1]

  motivation_artifact_ids = [q1]
  key_claim_ids = [c1]
  follow_up_question_ids = [q2]
  shared_setting_ids = [s1]
}
```

Interpretation:

- `m1` is the sole module; its conclusion is `c1`
- `motivation_artifact_ids = [q1]` — editorial: this question motivated the research
- `key_claim_ids = [c1]` — editorial: this is the main takeaway
- `follow_up_question_ids = [q2]` — editorial: this question opens future work
- `shared_setting_ids = [s1]` — this setting applies across the package

## Deferred Topics

The following topics are intentionally deferred:

- how raw material is canonicalized into knowledge artifacts, steps, modules, and packages
- how review works
- how optional revised packages are materialized
- how packages integrate into the global Gaia graph (V2)
- how prior, belief, and BP are defined on top of the dependency graph (V3)

Those belong to later documents.
