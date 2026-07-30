# Validate a job package

Validate the job package at `$ARGUMENTS` without executing it.

1. Read its `job.toml` and `docs/authoring.md`.
2. Check field types, required values, confined paths, required environment
   names, required files, and executable availability.
3. Run `uv run runwisp-job doctor "$ARGUMENTS"` without exposing environment
   values.
4. Run the smallest relevant pytest selector if a failure requires code
   changes.
5. Report exact failures, fixes, and validation evidence.

Do not execute the job unless the user explicitly requests `run`.
