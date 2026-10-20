"""Checks for .env files."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from .parser import EnvEntry, KEY_RE


@dataclass
class Finding:
    severity: str
    code: str
    message: str
    key: str | None = None
    line: int | None = None


PLACEHOLDER_VALUES = {
    "changeme",
    "replace-me",
    "replace_me",
    "your_value",
    "your-value",
    "xxx",
    "todo",
}
PLACEHOLDER_TOKENS = ("changeme", "replace", "your_", "xxx", "todo")


def _is_placeholder(value: str) -> bool:
    lowered = value.strip().lower().strip('"\'')
    if lowered in PLACEHOLDER_VALUES:
        return True
    if len(lowered) >= 2 and lowered.startswith("<") and lowered.endswith(">"):
        return True
    return any(token in lowered for token in PLACEHOLDER_TOKENS)


def check_env(
    entries: list[EnvEntry],
    example_entries: list[EnvEntry] | None = None,
    *,
    strict: bool = False,
) -> list[Finding]:
    findings: list[Finding] = []
    keys_seen: dict[str, list[EnvEntry]] = defaultdict(list)
    for entry in entries:
        keys_seen[entry.key].append(entry)

    for entry in entries:
        if not KEY_RE.fullmatch(entry.key):
            findings.append(
                Finding(
                    "error",
                    "invalid-key",
                    f"invalid environment key {entry.key!r}",
                    entry.key,
                    entry.line_number,
                )
            )

    for key, items in keys_seen.items():
        for entry in items[1:]:
            findings.append(
                Finding(
                    "error",
                    "duplicate-key",
                    f"duplicate key {key!r}",
                    key,
                    entry.line_number,
                )
            )

    for entry in entries:
        if entry.value == "":
            findings.append(
                Finding(
                    "warning",
                    "empty-value",
                    f"{entry.key} has an empty value",
                    entry.key,
                    entry.line_number,
                )
            )
        elif _is_placeholder(entry.value):
            findings.append(
                Finding(
                    "warning",
                    "placeholder-value",
                    f"{entry.key} uses a placeholder value",
                    entry.key,
                    entry.line_number,
                )
            )

    if example_entries is not None:
        example_keys = {entry.key for entry in example_entries}
        env_keys = {entry.key for entry in entries}

        for key in sorted(example_keys - env_keys):
            findings.append(
                Finding(
                    "error",
                    "missing-key",
                    f"required key {key!r} is missing",
                    key,
                    None,
                )
            )

        undocumented_severity = "warning" if strict else "info"
        for key in sorted(env_keys - example_keys):
            findings.append(
                Finding(
                    undocumented_severity,
                    "undocumented-key",
                    f"{key!r} is not documented in the example file",
                    key,
                    None,
                )
            )

    return findings
