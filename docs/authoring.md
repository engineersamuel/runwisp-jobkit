# Authoring jobs

A job package is a directory containing a `job.toml` and the files needed by
its command. Run `runwisp-job doctor JOB_DIR` before scheduling or invoking a
new package.

## Manifest contract

Manifest fields are type checked, and unknown fields are rejected. `schema`
must be integer `1`, `id` must be nonempty, `kind` must be `"command"`, and
`argv` must contain at least one string. `cwd` defaults to `"."`;
`required_env` and `required_files` default to empty lists.

`cwd` and every `required_files` entry are resolved to typed absolute paths and
must remain inside the job directory. Parent traversal and symlink escapes are
rejected. The working directory must exist, and required files must be readable
regular files.

## Arguments and execution

Arguments after `JOB_DIR` are appended directly to `argv`, in order and without
shell parsing. The harness uses shell-free process execution, so quotes,
metacharacters, and substitutions have no special meaning. A job can explicitly
choose a shell in `argv`, but that shell then owns parsing and safety.

The job inherits the harness environment. Every name in `required_env` must
have a nonblank value before either `doctor` or `run` succeeds. Environment
values are not printed by `doctor`. Secrets must be supplied by the deployment
environment; the harness does not store them.

On `run`, the harness changes to the manifest `cwd` and replaces itself with the
job process. Once replacement succeeds, stdout, stderr, exit status, and signals
come directly from the job.

## Passive doctor

`doctor` reads and validates the manifest, confined paths, required environment
names, required files, and executable availability. It never executes the job
and never proves that the job's runtime behavior or external dependencies will
succeed.

## Exit codes

- `2`: CLI usage or job configuration failed before execution. A running job
  can also choose to return `2` for its own argument errors.
- `126`: the executable became non-runnable or had an invalid executable format
  at process replacement time.
- `127`: the executable disappeared at process replacement time.

Other job exit codes are preserved.

## Security boundary

Path confinement protects only the manifest `cwd` and declared required files.
The harness is not a sandbox. The job retains the filesystem, network, process,
and environment access granted by its operating-system account.

Job authors are responsible for installing runtimes and dependencies, declaring
required inputs, validating forwarded arguments, handling side effects, and
producing useful output and exit codes.
