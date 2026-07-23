# runwisp-jobkit

`runwisp-jobkit` is a small, shell-free harness for validating and running
filesystem job packages.

## Install

After the first PyPI release, install the published tool with Python 3.14:

```console
uv tool install --python 3.14 runwisp-jobkit
```

For current development, install from a local Git checkout by running this
command at the repository root:

```console
uv tool install --force --python 3.14 .
```

## Use

```console
runwisp-job doctor JOB_DIR
runwisp-job run JOB_DIR [ARG ...]
```

`doctor` validates a package without running it. `run` appends each supplied
argument to the manifest command unchanged, then replaces the harness process
with the job process.

## Manifest

Every job directory contains a `job.toml`. This complete manifest shows all
seven fields:

```toml
schema = 1
id = "example-job"
kind = "command"
cwd = "."
argv = ["python", "run.py"]
required_env = ["EXAMPLE_MESSAGE"]
required_files = ["run.py"]
```

See [Authoring jobs](docs/authoring.md) for validation, execution, and error
semantics.

## Examples

The [nightly news brief](examples/nightly-news) is a sanitized, one-time
snapshot of a production-derived job and the featured real-world example. Its
private `runwisp-job-report` dependency is intentionally omitted, so it is not
immediately runnable from this repository. Live scheduler configuration,
deployment paths, credentials, and delivery setup are excluded.

These four minimal language templates are immediately runnable:

- [Python](examples/python)
- [TypeScript with Bun](examples/typescript)
- [Rust](examples/rust)
- [Shell](examples/shell)

## Scope

The harness does not install job dependencies, discover jobs, store secrets,
or manage RunWisp policy. Job packages and their deployment environment remain
responsible for those concerns.
