"""Parse .env files into structured entries."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class EnvEntry:
    key: str
    value: str
    line_number: int
    raw: str


def _strip_inline_comment(value: str) -> str:
    for index, char in enumerate(value):
        if char == "#" and index > 0 and value[index - 1].isspace():
            return value[:index].rstrip()
    return value


def parse_env(text: str) -> list[EnvEntry]:
    entries: list[EnvEntry] = []

    for line_number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            continue

        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()

        quoted = (
            len(value) >= 2
            and value[0] == value[-1]
            and value[0] in {'"', "'"}
        )
        if not quoted:
            value = _strip_inline_comment(value)
        else:
            value = value[1:-1]

        entries.append(
            EnvEntry(key=key, value=value, line_number=line_number, raw=raw)
        )

    return entries


def read_env_file(path: str | Path) -> list[EnvEntry]:
    return parse_env(Path(path).read_text(encoding="utf-8"))
