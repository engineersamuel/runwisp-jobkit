# Plan 001: Validate release artifacts and job working directories

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report; do not improvise. Use test-driven development: add each regression
> test first, run it, and confirm it fails for the expected missing behavior
> before changing production or package configuration. When dispatched by a
> reviewer, do not update `plans/README.md`; the reviewer maintains the index.
>
> **Drift check (run first)**:
> `rtk git diff --stat 0b519d8..HEAD -- pyproject.toml src/runwisp_jobs/manifest.py tests/test_doctor.py tests/test_distribution.py`
> Expected: no output. If any in-scope file changed, compare the current code
> against the excerpts below. A mismatch is a STOP condition.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: bug, dx
- **Planned at**: commit `0b519d8`, 2026-07-23

## Why this matters

The package declares the MIT license, but clean wheel and source-distribution
builds omit the repository's `LICENSE` notice and omit `License-File` metadata.
Publishing those artifacts would distribute substantial copies without the
notice required by the license. Separately, `doctor` reports `PASS cwd` after
checking only that the path is a directory. On POSIX, a directory without
search permission can pass `doctor`, then `run` raises an unhandled error at
`os.chdir`, violating the documented passive-preflight contract.

This plan fixes both release blockers with two focused regression tests and
minimal implementation/configuration changes. It does not automate publishing
or change job execution policy.

## Current state

- `pyproject.toml` defines package metadata and the `uv_build` backend.
- `src/runwisp_jobs/manifest.py` validates typed manifest paths.
- `tests/test_doctor.py` contains user-facing preflight tests and exact error
  assertions.
- `tests/test_distribution.py` does not exist.
- `.github/workflows/test.yml` already runs `uv run pytest`, so a distribution
  test under `tests/` automatically becomes a CI gate.

Current package metadata at `pyproject.toml:5-12`:

```toml
[project]
name = "runwisp-jobs"
version = "0.1.0"
description = "Filesystem job packages for RunWisp"
readme = "README.md"
requires-python = ">=3.14"
license = "MIT"
dependencies = []
```

Current working-directory validation at `src/runwisp_jobs/manifest.py:88-91`:

```python
cwd = _inside(root, raw_cwd, "cwd")
if not cwd.is_dir():
    raise JobConfigurationError(f"cwd is not a directory: {raw_cwd}")
```

The established permission-check convention immediately below it, at
`src/runwisp_jobs/manifest.py:92-95`, uses `os.access` and raises a precise
`JobConfigurationError`:

```python
for raw, resolved in zip(raw_files, files, strict=True):
    if not resolved.is_file() or not os.access(resolved, os.R_OK):
        raise JobConfigurationError(f"required file is not readable: {raw}")
```

Current execution at `src/runwisp_jobs/execution.py:68` calls
`os.chdir(prepared.manifest.cwd)` outside the handled `execvpe` block. Do not
move or broaden that error boundary; make `doctor` reject the known-invalid
configuration before execution.

Repository constraints from the approved design:

- Python 3.14 and the standard library remain the runtime contract.
- The harness remains shell-free and is not a sandbox.
- RunWisp remains the operational source of truth.
- Do not add discovery, dependency installation, language plugins, lifecycle
  hooks, retries, notification policy, secret storage, or scaffolding.

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Setup | `rtk uv sync --locked` | exit 0; locked environment ready |
| Baseline | `rtk uv run --python 3.14 pytest -q` | 30 passed, 1 Bun-dependent skip |
| Cwd test | `rtk uv run --python 3.14 pytest -q tests/test_doctor.py` | all doctor tests pass |
| Distribution test | `rtk uv run --python 3.14 pytest -q tests/test_distribution.py` | 1 passed |
| Lock validation | `rtk uv lock --check` | exit 0; no lock update required |
| Full suite | `rtk uv run --python 3.14 pytest -q` | 32 passed, 1 Bun-dependent skip |

## Suggested executor toolkit

- Read and follow the installed `test-driven-development` skill before edits.
- Read and follow `verification-before-completion` before reporting success.
- Use `apply_patch` for every file edit.

## Scope

**In scope** (the only files the executor may modify):

- `pyproject.toml`
- `src/runwisp_jobs/manifest.py`
- `tests/test_doctor.py`
- `tests/test_distribution.py` (create)

**Out of scope** (do not touch):

- `.github/workflows/test.yml` — pytest already gates CI.
- `uv.lock` — license metadata must not change dependency resolution.
- `LICENSE` — preserve the existing notice verbatim.
- `src/runwisp_jobs/execution.py` — execution and exit-code behavior are not
  being redesigned.
- `README.md`, `docs/`, and `examples/` — no documentation or product expansion.
- Release automation, PyPI publication, linting, typing, or formatting tools.

## Git workflow

- Work only on the isolated executor branch supplied by the reviewer.
- Produce one logical commit after all gates pass.
- Match the repository's conventional commit style. Commit message:
  `fix: validate release artifacts and job cwd`.
- Do not push, merge, or open a pull request.

## Steps

### Step 1: Establish a clean baseline

Run the drift check, setup, baseline suite, and lock validation from the
isolated worktree. Confirm `rtk git status --short` is empty before editing.

**Verify**:

- `rtk uv sync --locked` exits 0.
- `rtk uv run --python 3.14 pytest -q` reports 30 passed and one
  Bun-dependent skip.
- `rtk uv lock --check` exits 0.
- `rtk git status --short` has no tracked or untracked changes.

### Step 2: Reject a working directory that cannot be entered

RED first: add one POSIX-only regression test to `tests/test_doctor.py`, near
the other cwd tests. The test must:

1. Create a child directory under `job_dir` and set manifest `cwd` to it.
2. Remove search/execute permission from that child directory.
3. Call `main(["doctor", str(job_dir)])` with the required environment value.
4. Assert exit code `2`, no healthy line on stdout, and this exact stderr:
   `runwisp-job: example-job: cwd is not accessible: blocked\n`.
5. Restore directory permissions in `finally` so pytest can clean its temp
   directory.
6. Skip on non-POSIX platforms; do not pretend Windows permission behavior is
   equivalent.

Run only this test and confirm it fails because `doctor` currently returns 0.
If it errors during fixture setup or cleanup, fix the test until it produces
the intended assertion failure before editing production code.

GREEN: in `load_manifest`, retain the existing `is_dir` error unchanged, then
add an `os.access(cwd, os.X_OK)` check that raises:

```python
JobConfigurationError(f"cwd is not accessible: {raw_cwd}")
```

Use the existing imported `os` module. Do not add a helper or change execution.

**Verify**:

- RED command before implementation:
  `rtk uv run --python 3.14 pytest -q tests/test_doctor.py -k inaccessible_cwd`
  fails on the expected `0 != 2` behavior.
- GREEN command after implementation: the same command reports 1 passed.
- `rtk uv run --python 3.14 pytest -q tests/test_doctor.py` reports all doctor
  tests passing.

### Step 3: Include and verify the MIT notice in both artifacts

RED first: create `tests/test_distribution.py` using only standard-library
`pathlib`, `subprocess`, `tarfile`, and `zipfile`. The single test must:

1. Resolve the repository root from the test file.
2. Run `uv build --out-dir <tmp_path>/dist` from the repository root with
   `check=True`.
3. Locate exactly one wheel and one `.tar.gz` sdist.
4. Read the repository `LICENSE` bytes as the expected notice.
5. Assert the wheel contains that exact notice at a path ending in
   `.dist-info/licenses/LICENSE`.
6. Assert wheel `METADATA` contains the header `License-File: LICENSE`.
7. Assert the sdist contains that exact notice at its top-level
   `<name>-<version>/LICENSE` path.

Prefer context managers and exact content assertions. Do not install the
artifact, call the network, or inspect a pre-existing `dist/` directory.

Run the test and confirm it fails because the current artifacts contain no
license file. Then add this field directly after `license = "MIT"` in
`pyproject.toml`:

```toml
license-files = ["LICENSE"]
```

Run the distribution test again. If `uv_build` chooses a standards-compliant
license path differing only in the distribution-name normalization, make the
test robust to that prefix while preserving the exact `.dist-info/licenses/`
and notice-content requirements.

**Verify**:

- RED: `rtk uv run --python 3.14 pytest -q tests/test_distribution.py` fails on
  the missing license-file assertion before `pyproject.toml` changes.
- GREEN: the same command reports 1 passed after the metadata change.
- `rtk uv lock --check` exits 0 and `uv.lock` remains unmodified.

### Step 4: Run all gates and commit once

Run the full suite, lock check, and scope check. Read the full diff before
committing. Confirm every hunk implements a plan step.

**Verify**:

- `rtk uv run --python 3.14 pytest -q` reports 32 passed and one
  Bun-dependent skip.
- `rtk uv lock --check` exits 0.
- `rtk git status --short` lists only the four in-scope paths.
- `rtk git diff --check` exits 0 with no output.
- `rtk git diff -- .github/workflows/test.yml uv.lock LICENSE README.md docs examples src/runwisp_jobs/execution.py`
  has no output.

Commit once with `fix: validate release artifacts and job cwd`, then report the
commit hash and verification outputs to the reviewer.

## Test plan

- Add `test_doctor_rejects_inaccessible_cwd` to `tests/test_doctor.py`.
  Model its exact CLI/error assertions on
  `test_doctor_rejects_non_executable_explicit_path` in the same file.
- Add one artifact-level test in `tests/test_distribution.py` that performs a
  clean temporary build and checks the wheel, metadata, and sdist contents.
- Demonstrate RED then GREEN separately for both behaviors.
- Run the entire existing suite after both changes.

## Done criteria

- [ ] Both new tests were observed failing for the expected missing behavior
  before implementation/configuration changes.
- [ ] `rtk uv run --python 3.14 pytest -q` reports 32 passed and one permitted
  Bun-dependent skip.
- [ ] `rtk uv lock --check` exits 0 and `uv.lock` is unchanged.
- [ ] A temporary wheel contains the exact repository `LICENSE` notice under
  `.dist-info/licenses/` and declares `License-File: LICENSE`.
- [ ] A temporary sdist contains the exact repository `LICENSE` notice.
- [ ] `doctor` returns exit 2 with a concise error for an inaccessible cwd.
- [ ] No out-of-scope files changed.
- [ ] One conventional commit exists on the isolated executor branch.

## STOP conditions

Stop and report without improvising if:

- The drift check is nonempty or current excerpts do not match.
- The baseline suite or lock check fails before edits.
- The cwd test cannot reliably produce an inaccessible directory on POSIX.
- Adding `license-files` requires changing the build backend or `uv.lock`.
- Either fix requires modifying an out-of-scope file.
- A verification step fails twice after one focused correction.

## Maintenance notes

- Future packaging changes must keep artifact-level license assertions green;
  declaring a license expression alone does not ship the notice.
- Future cwd validation changes must preserve passive `doctor` behavior and
  exact, non-traceback configuration errors.
- PyPI publication remains a separate maintainer decision after this plan.
- Review permission checks carefully on non-POSIX systems; this plan makes no
  new cross-platform support promise.

