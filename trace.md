# Trace: Gaia

<!-- concepts: legacy-cleanup, documentation-lifecycle -->

## 2026-04-18: Legacy code cleanup

- Part A (disk-only): Removed 13 ghost `__pycache__` dirs, 8 stale worktrees (~1.6 GB), node_modules/egg-info/.coverage
- Part B (git-tracked): Removed 17 obsolete scripts, 4 Typst v4 fixture dirs, 6 orphan fixture dirs, 2 Typst-era docs
- Caught mistake: `hole-bridge-tutorial.md` and `cli-commands.md` are v5 content, not Typst-era — restored them
- User feedback: outdated docs should be marked "Needs upgrade to v5" and upgraded in a follow-up PR, not simply deleted

### EARS — Progress (2026-04-18 10:34)
<!-- concepts: repo-split, lkm-cleanup -->
- LKM code has been split to SiliconEinstein/gaia-lkm repo. Now removing all LKM remnants from main Gaia repo.
- Boundary is clean: gaia.lkm is fully self-contained, zero reverse deps from cli/ir/bp.
- Removing: gaia/lkm/ (44 files), tests/gaia/lkm/ (16 files), frontend/, scripts/, LKM fixtures, LKM docs/plans/specs.
- pyproject.toml: removing `[server]` optional-deps, LKM pytest markers, coverage excludes.
