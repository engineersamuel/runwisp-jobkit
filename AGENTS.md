# Agent Guide

## Project overview

`runwisp-jobkit` is a Python package that validates and runs filesystem
job packages without implicit shell parsing. Preserve strict validation,
confined path handling, argument ordering, process exit codes, and signal
behavior.

## Build and test

- Install locked development dependencies with `uv sync --locked`.
- Run static type checking with `uv run ty check`.
- Run the full test suite with `uv run pytest`.
- Build release artifacts with `uv build`.

## Architecture

- `src/runwisp_jobkit/cli.py` parses `doctor` and `run` commands.
- `src/runwisp_jobkit/manifest.py` validates manifests and confined paths.
- `src/runwisp_jobkit/execution.py` prepares jobs and replaces the process.
- `tests/` covers CLI, validation, execution, examples, and distribution.

## Agent customization

- Shared Codex and Copilot skills live in `.agents/skills/`.
- Copilot-specific instructions, prompts, and custom agents remain in
  `.github/`.
- Claude-specific commands, agents, hooks, and its compatibility skill remain
  in `.claude/`.

## Conventions

- Keep the implementation standard-library-first unless a dependency is
  clearly necessary.
- Add or update tests for behavior changes and validation edge cases.
- Reject invalid input explicitly; do not silently normalize unsafe values.
- Keep job execution shell-free unless a job explicitly names a shell.
- Preserve public CLI commands and documented manifest semantics.
- Keep changes narrow, typed, and consistent with existing modules.
