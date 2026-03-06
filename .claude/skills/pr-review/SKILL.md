---
name: pr-review
description: "Pull request review assistant for this repo. Use when the user asks to review a PR, audit whether a PR really matches its code/tests/docs/issues, prepare GitHub review comments, or check if a PR's claimed scope is actually implemented."
---

# PR Review Assistant

Review pull requests by combining code inspection with targeted validation.

The goal is to find real issues, not to restate the PR.

Focus on:
- behavior bugs
- regressions
- test gaps
- implementation gaps versus PR claims
- design doc / issue mismatches that affect correctness or scope

## Output Standard

Lead with findings.

Each finding should be:
- specific
- reproducible when possible
- tied to files and lines
- clear about whether it is a code bug, test gap, or scope mismatch

Use severity in this order:
- `High`: shipped path is broken, unusable, or the PR claim is materially false
- `Medium`: common flow is incomplete, misleading, or likely to fail
- `Low`: minor inconsistency or non-blocking polish

Do not waste time on style-only comments unless the user explicitly wants them.

## Review Workflow

### 1. Get the actual PR code

Start from the diff, not the PR body.

Recommended commands:

```bash
git fetch origin pull/<PR_NUMBER>/head:pr-<PR_NUMBER>
git diff --stat main...pr-<PR_NUMBER>
git diff --name-only main...pr-<PR_NUMBER>
```

If stable line references help, create a worktree:

```bash
git worktree add /tmp/repo_pr<PR_NUMBER> pr-<PR_NUMBER>
```

### 2. Read PR metadata

Check:
- title
- body
- claimed test results
- linked issues

Useful command:

```bash
gh pr view <PR_NUMBER> --repo <OWNER/REPO> --json title,body,headRefName,baseRefName,commits,files
```

### 3. Read only the critical code paths

Prioritize:
- user-facing commands / endpoints
- serialization and payload construction
- storage / persistence
- tests that are supposed to validate the changed behavior

### 4. Validate important claims with minimal reproductions

Prefer proving or disproving one behavior with a tiny script over long speculation.

Strong evidence looks like:
- “I ran X and got Y”
- “This payload only contains Z”
- “The documented input format crashes here with `ValueError`”

### 5. Check tests, but do not stop at green tests

Ask:
- do tests cover the production path?
- do tests rely on manual setup not done in production?
- do they assert behavior or only command success?
- do they skip the hard case?

### 6. Compare against linked issues and design docs

Only after understanding the implementation.

Look for:
- issue acceptance criteria not implemented
- user-facing commands documented but missing
- partial implementations presented as complete
- infrastructure landed, but feature claim says “done”

Only raise these as findings when they affect correctness, scope, or user expectations.

## Repo-Specific Heuristics

For this Gaia repo, pay special attention to:
- CLI command wiring versus docs and issue claims
- `publish` payload correctness
- cross-package reference handling
- whether `review` results actually flow into `build` / BP / persistence
- Kuzu versus Neo4j production-path differences
- tests that hide bugs with mocks or manual initialization
- PRs claiming to close many issues while only partially implementing them

## Good Findings

Examples of strong findings:
- a documented command path throws on valid-looking input
- a PR claims JSON output but still prints plain text
- publish drops required objects so remote reconstruction is impossible
- review results are saved but never consumed
- issue says “support X” but code only implements a stub or partial path

Examples of weak findings:
- “this could be cleaner”
- “I would structure this differently”
- “docs are long”

## Comment Templates

### Summary comment

```text
Review summary:

I reviewed this PR against the code, tests, linked issues, and any added design docs.
I found N material gaps:

1. ...
2. ...
3. ...

I left inline comments on the concrete code locations for each point.
```

### Inline comment

```text
This path does X, but the PR / issue claims Y. I reproduced Z by running ...
As written, ...
```

## Final Response To User

When reporting back:
- findings first
- file references with line numbers
- then open questions / assumptions
- then a short note on what was validated

If GitHub comments were posted, include:
- whether a summary comment was posted
- whether inline comments were posted
- links when available

## Minimal Checklist

Before finishing a review, make sure you have:
- fetched the PR branch
- inspected changed files
- read relevant tests
- validated at least one important claim with execution or a minimal reproduction
- checked linked issues if the PR claims to close them
- separated code bugs from scope mismatches
- written findings in severity order
