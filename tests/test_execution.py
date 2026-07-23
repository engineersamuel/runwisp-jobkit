from __future__ import annotations

import json
import signal
import subprocess
from collections.abc import Callable, Sequence
from pathlib import Path

import pytest

from runwisp_jobkit import execution
from runwisp_jobkit.manifest import load_manifest


@pytest.fixture
def bash_job(tmp_path: Path) -> Callable[[str, Sequence[str]], Path]:
    def create(script: str, argv: Sequence[str] = ("bash", "run.sh")) -> Path:
        job_dir = tmp_path / "job"
        job_dir.mkdir()
        (job_dir / "run.sh").write_text(
            f"#!/usr/bin/env bash\n{script}",
            encoding="utf-8",
        )
        (job_dir / "job.toml").write_text(
            "\n".join(
                (
                    "schema = 1",
                    'id = "execution-test"',
                    'kind = "command"',
                    'cwd = "."',
                    f"argv = {json.dumps(list(argv))}",
                    "",
                )
            ),
            encoding="utf-8",
        )
        return job_dir

    return create


def _run(job_dir: Path, *job_args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "uv",
            "run",
            "--python",
            "3.14",
            "runwisp-job",
            "run",
            str(job_dir),
            *job_args,
        ],
        check=False,
        text=True,
        capture_output=True,
    )


def test_run_appends_arguments_unchanged(bash_job):
    job_dir = bash_job("printf '%s\\n' \"$@\"\n")

    result = _run(job_dir, "plain", "two words", "", "--flag")

    assert result.returncode == 0
    assert result.stdout == "plain\ntwo words\n\n--flag\n"
    assert result.stderr == ""


def test_run_preserves_stdout_and_stderr(bash_job):
    job_dir = bash_job(
        "printf 'from stdout\\n'\nprintf 'from stderr\\n' >&2\n"
    )

    result = _run(job_dir)

    assert result.returncode == 0
    assert result.stdout == "from stdout\n"
    assert result.stderr == "from stderr\n"


def test_run_preserves_nonzero_exit_status(bash_job):
    job_dir = bash_job("exit 37\n")

    result = _run(job_dir)

    assert result.returncode == 37


def test_run_does_not_interpret_shell_metacharacters(bash_job):
    job_dir = bash_job("printf '%s\\n' \"$1\"\n")
    literal = "$(touch should-not-exist)"

    result = _run(job_dir, literal)

    assert result.returncode == 0
    assert result.stdout == f"{literal}\n"
    assert not (job_dir / "should-not-exist").exists()


def test_run_process_receives_termination_signal(bash_job):
    job_dir = bash_job("", ("bash", "-c", "kill -TERM $$"))

    result = _run(job_dir)

    assert result.returncode == 128 + signal.SIGTERM


def test_run_invalid_executable_format_maps_to_126(bash_job):
    job_dir = bash_job("", ("./invalid-executable",))
    executable = job_dir / "invalid-executable"
    executable.write_text("not an executable format\n", encoding="utf-8")
    executable.chmod(0o755)

    result = _run(job_dir)

    assert result.returncode == 126
    assert "Traceback" not in result.stderr


def test_exec_race_missing_maps_to_127(bash_job, monkeypatch):
    job_dir = bash_job("")
    prepared = execution.prepare_job(load_manifest(job_dir))
    monkeypatch.chdir(job_dir.parent)

    def missing(*_args, **_kwargs):
        raise FileNotFoundError

    monkeypatch.setattr(execution.os, "execvpe", missing)

    assert execution.execute_job(prepared) == 127


def test_exec_race_permission_maps_to_126(bash_job, monkeypatch):
    job_dir = bash_job("")
    prepared = execution.prepare_job(load_manifest(job_dir))
    monkeypatch.chdir(job_dir.parent)

    def denied(*_args, **_kwargs):
        raise PermissionError

    monkeypatch.setattr(execution.os, "execvpe", denied)

    assert execution.execute_job(prepared) == 126
