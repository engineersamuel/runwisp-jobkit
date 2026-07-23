# RunWisp Jobs Harness Design

> Historical naming note (2026-07-23): the public harness described here was
> renamed to `runwisp-jobkit`; the private implemented-job repository now owns
> `runwisp-jobs`. See `2026-07-23-runwisp-repository-naming-design.md`.

**Status:** Approved

**Date:** 2026-07-22

## Summary

`runwisp-jobs` is a small, publishable filesystem harness for running job packages from RunWisp. It gives humans and LLMs one stable convention—`job.toml` plus a command—without turning RunWisp into a plugin host.

RunWisp remains the operational source of truth. A separate operator-owned repository contains real jobs, prompts, policies, and shared job code. The public harness contains no production jobs, personal paths, secret references, or private integrations.

## Goals

- Make a RunWisp job easy to create, inspect, copy, and test.
- Support Python, TypeScript, Rust, shell, and compiled executables through one command model.
- Keep schedules, retries, timeouts, retention, notifications, parameters, and host environment in `runwisp.toml`.
- Keep job behavior and job-owned content in filesystem packages.
- Fail early with exact configuration errors.
- Preserve subprocess behavior without a shell or output wrapper.
- Provide a Python 3.14 standard-library runtime with `pytest` used only for development and tests.

## Non-goals

V1 does not provide automatic job discovery, generated RunWisp configuration, dependency installation, dynamic language plugins, Python imports from the harness, job lifecycle hooks, remote registries, retries, notification policy, secret storage, or a scaffolding command.

## Ownership and Repository Split

### Public harness repository

The publishable `runwisp-jobs` repository owns:

- the `runwisp-job` CLI;
- the versioned `job.toml` schema;
- manifest validation and passive diagnostics;
- shell-free command execution;
- neutral, copyable language examples;
- documentation, packaging, and tests.

### Operator jobs repository

A separate, potentially private repository owns:

- production job packages;
- prompts, markers, validators, and other job policy;
- shared job-specific libraries;
- job tests and fixtures.

### RunWisp configuration

`runwisp.toml` owns:

- schedules and catch-up behavior;
- timeouts, retries, and retention;
- success and failure notification policy;
- operator-exposed parameters such as `--dry-run`;
- host-specific paths and environment values;
- references to externally protected secret files.

The integration is an explicit filesystem pointer:

```toml
run = "/home/operator/.local/bin/runwisp-job run /home/operator/runwisp-automations/jobs/nightly-news"
```

There is no discovery or configuration merge step.

## Public Interface

The CLI has two commands:

```text
runwisp-job run JOB_DIR [JOB_ARGS...]
runwisp-job doctor JOB_DIR
```

Everything after `JOB_DIR` in `run` is appended unchanged to the manifest command. This lets RunWisp parameters pass directly to a job:

```text
runwisp-job run /path/to/job --dry-run
```

The harness exposes no language-specific interface. Every job is a command.

## Manifest Contract

Every package contains `JOB_DIR/job.toml`:

```toml
schema = 1
id = "nightly-news"
kind = "command"
cwd = "."
argv = ["uv", "run", "--script", "run.py"]
required_env = ["COPILOT_TOKEN_FILE"]
required_files = ["run.py", "prompt.md"]
```

Fields:

| Field | Required | Meaning |
| --- | --- | --- |
| `schema` | yes | Integer schema version; V1 accepts only `1`. |
| `id` | yes | Nonempty diagnostic identifier. It is not a global registry key. |
| `kind` | yes | Execution model; V1 accepts only `"command"`. |
| `argv` | yes | Nonempty array of nonempty strings. |
| `cwd` | no | Working directory relative to `JOB_DIR`; defaults to `"."`. |
| `required_env` | no | Environment names that must exist with nonempty values; defaults to `[]`. |
| `required_files` | no | Readable files relative to `JOB_DIR`; defaults to `[]`. |

Unknown fields are rejected so spelling errors do not silently change behavior.

`cwd` and `required_files` must remain inside the resolved job directory. Absolute paths, parent traversal, and symlink escapes are rejected. These checks apply to typed manifest paths, not arbitrary command arguments or job code; the harness is not a sandbox.

Environment variables are inherited unchanged. The harness does not expand variables in the manifest, redact or print their values, or synthesize job-specific variables.

## Execution Flow

`run` performs these steps:

1. Resolve `JOB_DIR` and load `job.toml` with `tomllib`.
2. Validate the schema, field types, confined paths, required environment, required files, working directory, and executable availability.
3. Append passthrough arguments to `argv` without parsing or rewriting them.
4. Change to the validated working directory.
5. Replace the harness process with the job using `os.execvpe`.

Process replacement gives the job RunWisp's stdin, stdout, stderr, PID lifecycle, signals, and exact exit status. `run` emits no progress or success text.

The harness launches without a shell. It does not install dependencies or interpret the command beyond the validation required to execute it.

## Doctor and Errors

`doctor JOB_DIR` runs the same passive preflight checks without executing job code or accessing the network. It prints named checks and a final pass/fail summary. It never prints environment values or secret contents.

Exit behavior:

- invalid harness input or job configuration: concise stderr error and exit `2`;
- executable missing at launch: exit `127`;
- executable present but not runnable: exit `126`;
- executed job: its exit status is RunWisp's exit status.

Errors identify the job and failed requirement, for example:

```text
runwisp-job: nightly-news: required environment variable COPILOT_TOKEN_FILE is not set
```

## Public Repository Layout

```text
runwisp-jobs/
├── pyproject.toml
├── src/runwisp_jobs/
│   ├── cli.py
│   ├── manifest.py
│   └── execution.py
├── examples/
│   ├── python/
│   ├── typescript/
│   ├── rust/
│   └── shell/
├── tests/
└── docs/
```

The CLI and manifest are the external seam. The internal Python modules may change without changing job packages or RunWisp configuration.

Examples are complete, neutral job packages that demonstrate required environment, required files, direct arguments, and `--dry-run`:

```toml
# Python
argv = ["uv", "run", "--script", "run.py"]

# TypeScript
argv = ["bun", "run", "run.ts"]

# Rust
argv = ["cargo", "run", "--quiet", "--"]

# Shell
argv = ["bash", "run.sh"]
```

No `init` command is included. Users and LLMs copy the closest example and edit its small manifest.

## Packaging and Distribution

The harness targets the current stable Python 3.14 line and declares `requires-python = ">=3.14"`. Its runtime uses only the standard library.

Published installation:

```bash
uv tool install --python 3.14 runwisp-jobs
```

Git installation is supported before or instead of a package-index release. Upgrades are explicit with `uv tool upgrade`. Development, tests, and all other Python execution use `uv`.

## Private Automation Layout

The initial operator repository uses a `uv` workspace:

```text
runwisp-automations/
├── pyproject.toml
├── uv.lock
├── packages/
│   └── copilot-report/
│       └── src/runwisp_automations/report.py
└── jobs/
    ├── nightly-news/
    │   ├── job.toml
    │   ├── pyproject.toml
    │   ├── run.py
    │   └── prompt.md
    ├── ai-tool-repo-scout/
    │   ├── job.toml
    │   ├── pyproject.toml
    │   ├── run.py
    │   └── prompt.md
    └── secondbrain-weekly-lint/
        ├── job.toml
        ├── prompt.md
        └── run.sh
```

The two report jobs share one private report package. Prompts, output markers, validators, and length policy remain job-owned. Shared Copilot execution, artifact handling, validation plumbing, Telegram delivery, and message chunking live in `copilot-report`.

RunWisp provides host-specific binary and work-directory paths, Telegram destination, and token-file references. Tokens remain outside both repositories.

The lint job is a small adapter that invokes the existing secondbrain lint script through a host-provided repository path. This preserves lint behavior and keeps lint implementation with the repository it validates.

All three entrypoints accept `--dry-run`. Report dry-runs generate and validate without Telegram delivery. The lint adapter's dry-run validates its environment and target script, then reports the planned command without running the lint.

## Report Compatibility Requirements

The private report package preserves the existing operator behavior:

- `[SILENT]` suppresses delivery;
- a generated artifact is preferred over stdout;
- the marker must be the artifact's first line;
- stdout fallback is accepted only when the marker is a standalone line;
- progress or conversational output is rejected;
- an otherwise valid brief may be delivered when Copilot exits nonzero;
- invalid output reports an exact reason, exits nonzero, and sends no direct failure notification;
- RunWisp remains the sole failure notifier;
- dry-run performs generation and validation but no Telegram network request;
- successful Telegram delivery is the report task's success message.

News validation requires 120–3000 characters, a headline, four to seven news bullets, and at least four public source URLs.

Tool-repository validation requires 200–6000 characters and either one to three complete seven-field tool sections with a source URL per tool, or a sourced `No strong fit` section.

## Testing

Both repositories use `pytest`. Test execution always runs through `uv` on Python 3.14. The public runtime remains standard-library-only.

Public harness coverage includes:

- strict schema validation and unknown fields;
- malformed fields and missing requirements;
- traversal and symlink escapes;
- environment, file, working-directory, and executable checks;
- argument passthrough;
- stdout, stderr, signal, and exit behavior;
- shell-free execution;
- passive `doctor` behavior;
- language-example smoke tests.

Private automation coverage includes Copilot command construction, `[SILENT]`, marker rules, stdout fallback, progress rejection, both report validators, length limits, Telegram chunking and mocked delivery, nonzero Copilot behavior, and dry-run's no-network guarantee.

CI runs the public harness suite and language smoke tests. Tests that need Bun or Rust install those runtimes in isolated CI jobs rather than making them harness dependencies.

## Rollout and Rollback

Rollout order:

1. Commit the existing scheduler scripts as a recoverable baseline.
2. Preserve a timestamped copy of the live, non-versioned RunWisp configuration.
3. Implement, test, and commit the public harness.
4. Install the local CLI through `uv tool install --python 3.14`.
5. Implement, test, and commit the private automation repository.
6. Replace each RunWisp task's command with its explicit `runwisp-job run` pointer.
7. Validate the configuration and reload RunWisp.
8. Run all three tasks through RunWisp with `--dry-run`.
9. Run one real news brief and confirm exactly one report message and no generic success message.
10. Trigger a controlled invalid report and confirm exactly one global failure notice.
11. Remove superseded report scripts only after live verification.

Scheduling after migration:

- weekly lint: Sunday 22:00 with `catch_up = "latest"`;
- tool scout: daily 03:00 with `catch_up = "latest"`;
- news: daily 06:00 with `catch_up = "skip"`.

Report tasks retain zero retries, use only the global failure notifier, and have no RunWisp success notification. Weekly lint retains its success notification. Redundant failure notifiers and `NOTIFY_ON_EMPTY` are removed.

Rollback restores the saved RunWisp configuration, validates it, reloads RunWisp, and continues using the retained scheduler scripts. The configuration backup remains after successful rollout.

## Acceptance Criteria

- A new job can be authored by copying one example and editing `job.toml`.
- RunWisp invokes every language through the same one-line filesystem pointer.
- The harness adds no job-specific behavior and no runtime third-party dependency.
- `doctor` identifies invalid packages without executing them.
- Valid jobs behave like directly executed processes.
- Public repository contents are safe to publish.
- Production jobs and secrets do not enter the public repository.
- All public and private tests pass through `uv` on Python 3.14.
- Live RunWisp tasks pass dry-run and notification acceptance checks.
