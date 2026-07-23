from __future__ import annotations

import dataclasses
import os
import pathlib
import tomllib
from collections.abc import Mapping
from typing import Any


ALLOWED_FIELDS = frozenset(
    {"schema", "id", "kind", "cwd", "argv", "required_env", "required_files"}
)


class JobConfigurationError(ValueError):
    """The job package cannot be executed safely as configured."""


@dataclasses.dataclass(frozen=True, slots=True)
class JobManifest:
    job_dir: pathlib.Path
    job_id: str
    argv: tuple[str, ...]
    cwd: pathlib.Path
    required_env: tuple[str, ...]
    required_files: tuple[pathlib.Path, ...]


def _string_list(data: Mapping[str, Any], name: str) -> tuple[str, ...]:
    value = data.get(name, [])
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item for item in value
    ):
        raise JobConfigurationError(f"{name} must be an array of nonempty strings")
    return tuple(value)


def _inside(root: pathlib.Path, raw: str, field: str) -> pathlib.Path:
    candidate = pathlib.Path(raw)
    if candidate.is_absolute():
        raise JobConfigurationError(f"{field} must be relative to the job directory: {raw}")
    try:
        resolved = (root / candidate).resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, ValueError) as error:
        raise JobConfigurationError(
            f"{field} does not resolve inside the job directory: {raw}"
        ) from error
    return resolved


def load_manifest(job_dir: os.PathLike[str] | str) -> JobManifest:
    try:
        root = pathlib.Path(job_dir).resolve(strict=True)
    except OSError as error:
        raise JobConfigurationError(f"job directory does not exist: {job_dir}") from error
    if not root.is_dir():
        raise JobConfigurationError(f"job directory is not a directory: {root}")

    manifest_path = root / "job.toml"
    try:
        with manifest_path.open("rb") as stream:
            data = tomllib.load(stream)
    except (OSError, tomllib.TOMLDecodeError) as error:
        raise JobConfigurationError(f"cannot read job.toml: {error}") from error

    unknown = sorted(set(data) - ALLOWED_FIELDS)
    if unknown:
        raise JobConfigurationError(f"unknown job.toml field(s): {', '.join(unknown)}")
    if type(data.get("schema")) is not int or data["schema"] != 1:
        raise JobConfigurationError("schema must be integer 1")
    if not isinstance(data.get("id"), str) or not data["id"].strip():
        raise JobConfigurationError("id must be a nonempty string")
    if data.get("kind") != "command":
        raise JobConfigurationError('kind must be "command"')

    argv = _string_list(data, "argv")
    if not argv:
        raise JobConfigurationError("argv must contain at least one string")
    if any("\0" in argument for argument in argv):
        raise JobConfigurationError("argv must not contain NUL")
    required_env = _string_list(data, "required_env")
    raw_files = _string_list(data, "required_files")
    raw_cwd = data.get("cwd", ".")
    if not isinstance(raw_cwd, str) or not raw_cwd:
        raise JobConfigurationError("cwd must be a nonempty relative path")

    cwd = _inside(root, raw_cwd, "cwd")
    if not cwd.is_dir():
        raise JobConfigurationError(f"cwd is not a directory: {raw_cwd}")
    if not os.access(cwd, os.X_OK):
        raise JobConfigurationError(f"cwd is not accessible: {raw_cwd}")
    files = tuple(_inside(root, value, "required_files") for value in raw_files)
    for raw, resolved in zip(raw_files, files, strict=True):
        if not resolved.is_file() or not os.access(resolved, os.R_OK):
            raise JobConfigurationError(f"required file is not readable: {raw}")

    return JobManifest(
        job_dir=root,
        job_id=data["id"].strip(),
        argv=argv,
        cwd=cwd,
        required_env=required_env,
        required_files=files,
    )
