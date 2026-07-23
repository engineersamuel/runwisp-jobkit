from __future__ import annotations

import dataclasses
import errno
import os
import pathlib
import shutil
from collections.abc import Mapping, Sequence

from .manifest import JobConfigurationError, JobManifest


@dataclasses.dataclass(frozen=True, slots=True)
class PreparedJob:
    manifest: JobManifest
    argv: tuple[str, ...]
    executable: pathlib.Path


def _find_executable(manifest: JobManifest, environ: Mapping[str, str]) -> pathlib.Path:
    command = manifest.argv[0]
    if os.sep in command:
        candidate = pathlib.Path(command)
        if not candidate.is_absolute():
            candidate = manifest.cwd / candidate
        resolved = candidate.resolve()
        if not resolved.is_file():
            raise JobConfigurationError(f"executable does not exist: {command}")
        if not os.access(resolved, os.X_OK):
            raise JobConfigurationError(f"executable is not runnable: {command}")
        return resolved

    search_entries: list[str] = []
    for entry in os.get_exec_path(environ):
        candidate = pathlib.Path(entry)
        if not candidate.is_absolute():
            candidate = manifest.cwd / candidate
        search_entries.append(str(candidate.resolve()))
    search_path = os.pathsep.join(search_entries)
    found = shutil.which(command, path=search_path)
    if found is None:
        raise JobConfigurationError(f"executable is not available on PATH: {command}")
    return pathlib.Path(found).resolve()


def prepare_job(
    manifest: JobManifest,
    job_args: Sequence[str] = (),
    environ: Mapping[str, str] | None = None,
) -> PreparedJob:
    effective_env = os.environ if environ is None else environ
    for name in manifest.required_env:
        if not effective_env.get(name, "").strip():
            raise JobConfigurationError(f"required environment variable {name} is not set")
    executable = _find_executable(manifest, effective_env)
    return PreparedJob(
        manifest=manifest,
        argv=manifest.argv + tuple(job_args),
        executable=executable,
    )


def execute_job(
    prepared: PreparedJob,
    environ: Mapping[str, str] | None = None,
) -> int:
    effective_env = dict(os.environ if environ is None else environ)
    os.chdir(prepared.manifest.cwd)
    try:
        os.execvpe(prepared.argv[0], list(prepared.argv), effective_env)
    except FileNotFoundError:
        return 127
    except PermissionError:
        return 126
    except OSError as error:
        if error.errno == errno.ENOEXEC:
            return 126
        raise
    raise AssertionError("os.execvpe returned unexpectedly")


def doctor_lines(prepared: PreparedJob) -> tuple[str, ...]:
    manifest = prepared.manifest
    return (
        f"PASS manifest: {manifest.job_dir / 'job.toml'}",
        f"PASS cwd: {manifest.cwd}",
        f"PASS environment: {len(manifest.required_env)} required value(s)",
        f"PASS files: {len(manifest.required_files)} required file(s)",
        f"PASS executable: {prepared.executable}",
        f"doctor: {manifest.job_id}: healthy",
    )
