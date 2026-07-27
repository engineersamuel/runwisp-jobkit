from pathlib import Path
import re
import shutil
import subprocess
import sys
import tomllib

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _git(repo, *arguments):
    return subprocess.run(
        ["git", *arguments],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )


def _next_version(tmp_path, commit_message, released_version=None):
    repo = tmp_path / "repository"
    repo.mkdir()
    shutil.copy(ROOT / "pyproject.toml", repo / "pyproject.toml")
    (repo / "changes.txt").write_text("base\n")

    _git(repo, "init", "--initial-branch=main")
    _git(repo, "config", "user.name", "Release Test")
    _git(repo, "config", "user.email", "release-test@example.com")
    _git(repo, "remote", "add", "origin", "https://github.com/example/example.git")

    if released_version is None:
        _git(repo, "add", ".")
        _git(repo, "commit", "--message", commit_message)
    else:
        _git(repo, "add", ".")
        _git(repo, "commit", "--message", f"chore(release): {released_version}")
        _git(repo, "tag", f"v{released_version}")
        with (repo / "changes.txt").open("a") as changes:
            changes.write("change\n")
        _git(repo, "add", "changes.txt")
        _git(repo, "commit", "--message", commit_message)

    result = subprocess.run(
        [str(Path(sys.executable).with_name("semantic-release")), "version", "--print"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def test_semantic_release_configuration_matches_release_policy():
    config = tomllib.loads((ROOT / "pyproject.toml").read_text())
    semantic_release = config["tool"]["semantic_release"]
    parser = config["tool"]["semantic_release"]["commit_parser_options"]

    assert semantic_release["branches"]["main"]["match"] == "main"
    assert semantic_release["version_toml"] == ["pyproject.toml:project.version"]
    assert semantic_release["assets"] == ["uv.lock"]
    assert semantic_release["build_command"] == "uv lock"
    assert semantic_release["tag_format"] == "v{version}"
    assert semantic_release["major_on_zero"] is True
    assert semantic_release["allow_zero_version"] is True
    assert semantic_release["commit_parser"] == "conventional"
    assert (
        semantic_release["changelog"]["default_templates"]["changelog_file"]
        == "CHANGELOG.md"
    )
    assert parser["minor_tags"] == ["feat"]
    assert parser["patch_tags"] == ["fix", "perf"]
    assert parser["default_bump_level"] == 0
    assert {"docs", "test", "ci", "chore", "refactor"} <= set(
        parser["allowed_tags"]
    )


@pytest.mark.parametrize(
    ("commit_message", "released_version", "expected"),
    [
        ("feat: automate releases", None, "0.1.0"),
        ("fix: correct output", "0.1.0", "0.1.1"),
        ("perf: reduce startup time", "0.1.0", "0.1.1"),
        ("feat: add scheduling", "0.1.0", "0.2.0"),
        ("feat!: replace the manifest", "0.1.0", "1.0.0"),
        (
            "fix: replace the manifest\n\nBREAKING CHANGE: old manifests no longer load",
            "0.1.0",
            "1.0.0",
        ),
        ("docs: clarify usage", "0.1.0", "0.1.0"),
        ("test: cover manifest errors", "0.1.0", "0.1.0"),
        ("ci: use Python 3.14", "0.1.0", "0.1.0"),
        ("chore: refresh metadata", "0.1.0", "0.1.0"),
        ("refactor: simplify parsing", "0.1.0", "0.1.0"),
    ],
)
def test_semantic_release_version_cases(
    tmp_path, commit_message, released_version, expected
):
    assert _next_version(tmp_path, commit_message, released_version) == expected


def test_release_workflow_is_merge_only_and_least_privilege():
    workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text()

    assert "pull_request:" in workflow
    assert "\n  push:" not in workflow
    assert "types: [closed]" in workflow
    assert "branches: [main]" in workflow
    assert "github.event.pull_request.merged == true" in workflow
    assert "concurrency:" in workflow
    assert "cancel-in-progress: false" in workflow
    assert "needs: verify" in workflow
    assert "uv run pytest" in workflow
    assert "environment: pypi" in workflow
    assert workflow.count("id-token: write") == 1
    assert workflow.count("contents: write") == 1
    assert "pypa/gh-action-pypi-publish@" in workflow
    assert "actions/upload-artifact@" in workflow
    assert "actions/download-artifact@" in workflow
    assert "skip-existing: true" in workflow
    assert "password:" not in workflow

    action_references = re.findall(r"uses:\s+([^\s]+)", workflow)
    assert action_references
    assert all(re.search(r"@[0-9a-f]{40}$", ref) for ref in action_references)


def test_pull_requests_require_conventional_titles():
    workflow = (ROOT / ".github" / "workflows" / "test.yml").read_text()

    assert "amannn/action-semantic-pull-request@" in workflow
    assert re.search(
        r"amannn/action-semantic-pull-request@[0-9a-f]{40}", workflow
    )
