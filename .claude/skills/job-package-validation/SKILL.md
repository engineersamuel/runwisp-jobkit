---
name: job-package-validation
description: 'Use when authoring, reviewing, or debugging RunWisp job packages, job.toml manifests, doctor failures, confined paths, required environment values, executable lookup, or shell-free argument forwarding.'
---

# Job Package Validation

Validate RunWisp job packages without weakening their security or execution
semantics.

This Claude-compatible copy mirrors the canonical shared skill in
`.agents/skills/job-package-validation/`.

## When to Use This Skill

- A `job.toml` manifest is added or changed.
- `runwisp-job doctor` reports a configuration failure.
- Code changes affect manifest parsing, path confinement, executable lookup,
  environment requirements, forwarded arguments, or process replacement.
- Tests need to cover job package validation or execution edge cases.

## Workflow

1. Read `docs/authoring.md` and the affected source module.
2. Confirm the manifest uses only the seven documented fields.
3. Check `cwd` and `required_files` remain inside the job directory after
   resolving symlinks.
4. Run `uv run pytest` with a focused test selector while iterating.
5. Run `uv run ruff check .`, `uv run ty check`, and the full
   `uv run pytest` suite before completion.

## Gotchas

- **Never** introduce implicit shell parsing. Arguments must remain an exact
  sequence unless the manifest explicitly invokes a shell.
- **Never** print required environment values. Report only missing variable
  names.
- Preserve configuration exit code `2` and process replacement codes `126`
  and `127`.
- `doctor` is passive. It validates configuration and availability but never
  executes the job.
