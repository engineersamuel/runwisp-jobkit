---
description: Preserve RunWisp job harness safety invariants in Python source
applyTo: 'src/runwisp_jobkit/**/*.py'
---

# Source safety rules

When changing Python source under `src/runwisp_jobkit/`:

- Preserve shell-free command execution and argument ordering.
- Keep manifest paths confined to the job package.
- Reject invalid configuration with `JobConfigurationError`.
- Preserve documented CLI and child-process exit codes.
- Add regression tests for behavior and validation changes.
