# RunWisp Repository Rename Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rename the reusable harness to `runwisp-jobkit`, give `runwisp-jobs` to the implemented job collection, and migrate all active package and RunWisp references safely.

**Architecture:** Preserve both Git repositories and their behavioral boundaries while changing active project identities consistently. Keep the existing `runwisp-job` CLI stable, rename Python modules so imports match their owning repositories, and treat the installed tool plus live RunWisp task definitions as deployment state that must be migrated and verified.

**Tech Stack:** Python 3.14, uv workspaces/tools, pytest, TOML, RunWisp 0.12.0, Git

---

### Task 1: Rename the public toolkit identity

**Files:**
- Move: `src/runwisp_jobs/` to `src/runwisp_jobkit/`
- Modify: `tests/test_doctor.py`
- Modify: `tests/test_execution.py`
- Modify: `tests/test_manifest.py`
- Modify: `pyproject.toml`
- Modify: `README.md`
- Modify: `LICENSE`
- Modify: `uv.lock`
- Modify: `docs/superpowers/specs/2026-07-22-runwisp-jobs-design.md`

- [ ] Change test imports from `runwisp_jobs` to `runwisp_jobkit`.
- [ ] Run `uv run pytest -q` and confirm collection fails with `ModuleNotFoundError: runwisp_jobkit`.
- [ ] Move the source package, point `runwisp-job` at `runwisp_jobkit.cli:entrypoint`, and rename the distribution to `runwisp-jobkit`.
- [ ] Update current user-facing naming and add a supersession note to the historical design.
- [ ] Run `uv lock`, `uv run pytest -q`, and `uv build`; expect all tests and both package builds to pass.

### Task 2: Rename the private jobs identity

**Files:**
- Move: `packages/copilot-report/src/runwisp_automations/` to `packages/copilot-report/src/runwisp_jobs/`
- Modify: `tests/test_report.py`
- Modify: `jobs/nightly-news/run.py`
- Modify: `jobs/nightly-news/pyproject.toml`
- Modify: `jobs/ai-tool-repo-scout/run.py`
- Modify: `jobs/ai-tool-repo-scout/pyproject.toml`
- Modify: `packages/copilot-report/pyproject.toml`
- Modify: `pyproject.toml`
- Modify: `uv.lock`
- Modify: `docs/superpowers/plans/2026-07-22-runwisp-jobs-implementation.md`

- [ ] Change tests and job adapters to import `runwisp_jobs`.
- [ ] Run `uv run pytest -q` and confirm collection fails with `ModuleNotFoundError: runwisp_jobs`.
- [ ] Move the shared module, rename its distribution to `runwisp-job-report`, and rename the root workspace project to `runwisp-jobs`.
- [ ] Update workspace dependencies and add a supersession note to the historical implementation plan.
- [ ] Run `uv lock` and `uv run pytest -q`; expect the complete private suite to pass.

### Task 3: Rename directories and migrate live configuration

**Files:**
- Move: `/Users/smendenhall/projects/microsoft/runwisp-jobs/` to `/Users/smendenhall/projects/microsoft/runwisp-jobkit/`
- Move: `/Users/smendenhall/projects/microsoft/runwisp-automations/` to `/Users/smendenhall/projects/microsoft/runwisp-jobs/`
- Backup: `/Users/smendenhall/.config/runwisp/runwisp.toml.pre-repo-rename-20260723`
- Modify: `/Users/smendenhall/.config/runwisp/runwisp.toml`

- [ ] Confirm both destination paths are absent and both repositories are clean except for this plan's changes.
- [ ] Rename the public directory first, then move the private repository into the vacated `runwisp-jobs` path.
- [ ] Back up `runwisp.toml` and replace every `/runwisp-automations/jobs/` path with `/runwisp-jobs/jobs/`.
- [ ] Uninstall the `runwisp-jobs` uv tool distribution and install `runwisp-jobkit` from the renamed public checkout.
- [ ] Run `runwisp validate -c ~/.config/runwisp/runwisp.toml --data ~/.local/share/runwisp` and expect validation success.
- [ ] Run `runwisp-job doctor` for all three configured job directories and expect `OK`.
- [ ] Reload the live daemon with the explicit config and data paths.

### Task 4: Verify repositories, deployment, and graph indexes

**Files:**
- No additional source files.

- [ ] Run `uv run pytest -q` and `uv build` in `runwisp-jobkit`.
- [ ] Run `uv run pytest -q` in `runwisp-jobs`.
- [ ] Confirm `uv tool list --show-paths` reports `runwisp-jobkit` owning `runwisp-job`.
- [ ] Confirm active files and `runwisp.toml` contain no old repository or module identities, excluding explicitly marked historical documents.
- [ ] Query the live RunWisp API and confirm all three task definitions use `/runwisp-jobs/jobs/`.
- [ ] Reindex both repositories as `runwisp-jobkit` and `runwisp-jobs` in codebase-memory-mcp.
- [ ] Inspect `git status --short` and diffs in both repositories before reporting completion.
