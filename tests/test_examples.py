from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).parents[1]


def _tool_available(command: str) -> bool:
    if os.environ.get("CI"):
        return True
    executable = shutil.which(command)
    if executable is None:
        return False
    try:
        result = subprocess.run(
            [executable, "--version"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError:
        return False
    return result.returncode == 0


def test_ci_never_skips_required_toolchains(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CI", "1")

    assert _tool_available("definitely-missing-runwisp-tool")


EXAMPLES = (
    pytest.param("python", id="python"),
    pytest.param("shell", id="shell"),
    pytest.param(
        "typescript",
        marks=pytest.mark.skipif(not _tool_available("bun"), reason="bun unavailable"),
        id="typescript",
    ),
    pytest.param(
        "rust",
        marks=pytest.mark.skipif(not _tool_available("cargo"), reason="cargo unavailable"),
        id="rust",
    ),
)


def _run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    environ = os.environ.copy()
    environ["RUNWISP_EXAMPLE_MESSAGE"] = "hello"
    return subprocess.run(
        ["runwisp-job", *arguments],
        cwd=PROJECT_ROOT,
        env=environ,
        check=False,
        text=True,
        capture_output=True,
    )


@pytest.mark.parametrize("language", EXAMPLES)
def test_example_passes_doctor_and_supports_dry_run(language: str) -> None:
    job_dir = PROJECT_ROOT / "examples" / language

    doctor = _run_cli("doctor", str(job_dir))

    assert doctor.returncode == 0, doctor.stderr
    assert f"doctor: {language}-example: healthy" in doctor.stdout

    dry_run = _run_cli("run", str(job_dir), "--dry-run")

    assert dry_run.returncode == 0, dry_run.stderr
    assert dry_run.stdout == "dry-run: hello\n"
