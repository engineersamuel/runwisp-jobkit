from pathlib import Path

import pytest


@pytest.fixture
def job_dir(tmp_path: Path) -> Path:
    (tmp_path / "run.sh").write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    (tmp_path / "job.toml").write_text(
        """schema = 1
id = "example-job"
kind = "command"
cwd = "."
argv = ["bash", "run.sh"]
required_env = ["EXAMPLE_MESSAGE"]
required_files = ["run.sh"]
""",
        encoding="utf-8",
    )
    return tmp_path
