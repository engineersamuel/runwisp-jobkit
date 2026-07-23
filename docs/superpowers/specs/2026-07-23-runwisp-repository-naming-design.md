# RunWisp Repository Naming Design

## Decision

Use `runwisp-jobkit` for the public reusable job-package harness and
`runwisp-jobs` for the private collection of implemented jobs.

The public project keeps the `runwisp-job` command because it operates on one
job package at a time. Its Python distribution and import package become
`runwisp-jobkit` and `runwisp_jobkit`.

The private repository becomes `runwisp-jobs`. Its shared report distribution
and import package become `runwisp-job-report` and `runwisp_jobs`, removing the
old `automation` vocabulary from active project identities.

## Runtime migration

Rename both repository directories without changing Git history. Update the
absolute job paths in `~/.config/runwisp/runwisp.toml`, reinstall the public
CLI from `runwisp-jobkit`, validate all job manifests, reload the live RunWisp
task definitions, and confirm the persisted task set uses only the new paths.

Historical design and implementation documents retain their original names as
records of the earlier migration, with a supersession note pointing here.
