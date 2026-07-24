import os

import pytest

from runwisp_jobs.cli import main


def _replace_argv(job_dir, replacement):
    manifest = job_dir / "job.toml"
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace(
            'argv = ["bash", "run.sh"]', replacement
        ),
        encoding="utf-8",
    )


def test_doctor_passes_without_running_job(job_dir, monkeypatch, capsys):
    sentinel = job_dir / "executed"
    (job_dir / "run.sh").write_text(
        f"#!/usr/bin/env bash\ntouch {sentinel}\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("EXAMPLE_MESSAGE", "secret-value")

    assert main(["doctor", str(job_dir)]) == 0
    assert not sentinel.exists()
    output = capsys.readouterr()
    assert "doctor: example-job: healthy" in output.out
    assert "secret-value" not in output.out + output.err


def test_doctor_rejects_missing_environment(job_dir, monkeypatch, capsys):
    monkeypatch.delenv("EXAMPLE_MESSAGE", raising=False)

    assert main(["doctor", str(job_dir)]) == 2
    output = capsys.readouterr()
    assert output.err == (
        "runwisp-job: example-job: required environment variable "
        "EXAMPLE_MESSAGE is not set\n"
    )


def test_doctor_rejects_empty_environment(job_dir, monkeypatch, capsys):
    monkeypatch.setenv("EXAMPLE_MESSAGE", "  ")

    assert main(["doctor", str(job_dir)]) == 2
    output = capsys.readouterr()
    assert output.err == (
        "runwisp-job: example-job: required environment variable "
        "EXAMPLE_MESSAGE is not set\n"
    )


def test_doctor_rejects_missing_executable(job_dir, monkeypatch, capsys):
    _replace_argv(job_dir, 'argv = ["missing-runwisp-job-executable"]')
    monkeypatch.setenv("EXAMPLE_MESSAGE", "configured")

    assert main(["doctor", str(job_dir)]) == 2
    output = capsys.readouterr()
    assert output.err == (
        "runwisp-job: example-job: executable is not available on PATH: "
        "missing-runwisp-job-executable\n"
    )


def test_doctor_does_not_consult_ambient_path(job_dir, monkeypatch, capsys):
    command = "ambient-only-runwisp-command"
    ambient_bin = job_dir.parent / "ambient-bin"
    ambient_bin.mkdir()
    ambient_command = ambient_bin / command
    ambient_command.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    ambient_command.chmod(0o755)
    _replace_argv(job_dir, f'argv = ["{command}"]')
    monkeypatch.setenv("PATH", str(ambient_bin))

    assert main(
        ["doctor", str(job_dir)], environ={"EXAMPLE_MESSAGE": "configured"}
    ) == 2
    output = capsys.readouterr()
    assert output.err == (
        "runwisp-job: example-job: executable is not available on PATH: "
        f"{command}\n"
    )


def test_doctor_resolves_relative_path_from_manifest_cwd(job_dir, capsys):
    command = "local-runwisp-command"
    executable = job_dir / command
    executable.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    executable.chmod(0o755)
    _replace_argv(job_dir, f'argv = ["{command}"]')

    assert main(
        ["doctor", str(job_dir)],
        environ={"EXAMPLE_MESSAGE": "configured", "PATH": "."},
    ) == 0
    output = capsys.readouterr()
    assert f"PASS executable: {executable.resolve()}" in output.out


@pytest.mark.skipif(
    os.name != "posix" or os.geteuid() == 0,
    reason="requires non-root POSIX permission enforcement",
)
def test_doctor_rejects_inaccessible_cwd(job_dir, monkeypatch, capsys):
    job_dir = job_dir.rename(job_dir.parent / "example-job")
    blocked = job_dir / "blocked"
    blocked.mkdir()
    manifest = job_dir / "job.toml"
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace(
            'cwd = "."', 'cwd = "blocked"'
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("EXAMPLE_MESSAGE", "configured")
    blocked.chmod(0)

    try:
        assert main(["doctor", str(job_dir)]) == 2
        output = capsys.readouterr()
        assert "doctor: example-job: healthy" not in output.out
        assert output.err == (
            "runwisp-job: example-job: cwd is not accessible: blocked\n"
        )
    finally:
        blocked.chmod(0o700)


def test_doctor_rejects_non_executable_explicit_path(job_dir, monkeypatch, capsys):
    executable = job_dir / "not-runnable"
    executable.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    _replace_argv(job_dir, 'argv = ["./not-runnable"]')
    monkeypatch.setenv("EXAMPLE_MESSAGE", "configured")

    assert main(["doctor", str(job_dir)]) == 2
    output = capsys.readouterr()
    assert output.err == (
        "runwisp-job: example-job: executable is not runnable: ./not-runnable\n"
    )


def test_doctor_rejects_nul_in_argv(job_dir, monkeypatch, capsys):
    _replace_argv(job_dir, 'argv = ["bash", "run\\u0000.sh"]')
    monkeypatch.setenv("EXAMPLE_MESSAGE", "configured")

    assert main(["doctor", str(job_dir)]) == 2
    output = capsys.readouterr()
    assert output.err.endswith(": argv must not contain NUL\n")
    assert "\0" not in output.out + output.err
    assert "Traceback" not in output.out + output.err


def test_doctor_never_prints_environment_values(job_dir, monkeypatch, capsys):
    secret = "top-secret-environment-value"
    monkeypatch.setenv("EXAMPLE_MESSAGE", secret)

    assert main(["doctor", str(job_dir)]) == 0
    output = capsys.readouterr()
    assert secret not in output.out + output.err
