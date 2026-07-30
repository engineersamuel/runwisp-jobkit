from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).parents[1] / ".claude" / "hooks" / "guard_bash.py"


def run_hook(command: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": command},
            }
        ),
        text=True,
        capture_output=True,
        check=False,
    )


def test_safe_command_keeps_normal_permission_flow():
    result = run_hook("uv run pytest")

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_destructive_command_is_denied():
    result = run_hook("git reset --hard HEAD~1")

    assert result.returncode == 0
    output = json.loads(result.stdout)
    decision = output["hookSpecificOutput"]
    assert decision["permissionDecision"] == "deny"
    assert "git reset --hard" in decision["permissionDecisionReason"]


def test_invalid_input_is_denied():
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input="{",
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
