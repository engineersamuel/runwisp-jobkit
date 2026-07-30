from __future__ import annotations

import json
import re
import sys
from collections.abc import Mapping
from typing import Any

BLOCKED_COMMANDS = (
    (re.compile(r"\bgit\s+reset\s+--hard\b", re.IGNORECASE), "git reset --hard"),
    (re.compile(r"\bgit\s+clean\s+-[a-z]*f[a-z]*\b", re.IGNORECASE), "git clean"),
    (
        re.compile(r"\bgit\s+push\b[^\n]*(?:--force(?:-with-lease)?|-f)\b", re.IGNORECASE),
        "force push",
    ),
    (
        re.compile(
            r"\brm\s+-[a-z]*r[a-z]*f[a-z]*\s+(?:/|~|\$HOME|\${HOME}|\.{1,2})(?:\s|$)",
            re.IGNORECASE,
        ),
        "recursive deletion of a broad path",
    ),
    (
        re.compile(r"\b(?:drop\s+(?:database|schema|table)|truncate\s+table)\b", re.IGNORECASE),
        "destructive database statement",
    ),
    (
        re.compile(r"\b(?:curl|wget)\b[^\n|]*\|\s*(?:ba)?sh\b", re.IGNORECASE),
        "remote script piped to a shell",
    ),
)


def _deny(reason: str) -> int:
    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        },
        sys.stdout,
    )
    sys.stdout.write("\n")
    return 0


def _command(payload: Mapping[str, Any]) -> str | None:
    if payload.get("tool_name") != "Bash":
        return None
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, Mapping):
        return None
    command = tool_input.get("command")
    return command if isinstance(command, str) else None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return _deny("Blocked because the Bash governance hook received invalid input.")
    if not isinstance(payload, Mapping):
        return _deny("Blocked because the Bash governance hook received invalid input.")

    command = _command(payload)
    if command is None:
        return _deny("Blocked because the Bash governance hook could not inspect the command.")

    for pattern, description in BLOCKED_COMMANDS:
        if pattern.search(command):
            return _deny(f"Blocked dangerous operation: {description}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
