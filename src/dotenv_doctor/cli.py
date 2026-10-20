"""Command-line interface for dotenv-doctor."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from . import __version__
from .checks import check_env
from .parser import parse_env


def _load(path: Path) -> list:
    return parse_env(path.read_text(encoding="utf-8"))


def _candidate_files(path: Path, example_path: str | None) -> list[Path]:
    if not path.is_dir():
        return [path]
    resolved_example = Path(example_path).resolve() if example_path else None
    return sorted(
        item
        for item in path.iterdir()
        if item.is_file()
        and item.name.startswith(".env")
        and (resolved_example is None or item.resolve() != resolved_example)
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="dotenv-doctor",
        description="Lint .env files for common mistakes and drift from .env.example.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=[".env"],
        help="env files or directories to check",
    )
    parser.add_argument(
        "-e",
        "--example",
        default=".env.example",
        help="example env file to compare against",
    )
    parser.add_argument(
        "--no-example",
        action="store_true",
        help="disable comparison with an example file",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="treat warnings as errors",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print findings as JSON",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    args = parser.parse_args(argv)

    example_path = None if args.no_example else args.example
    example_entries = None
    if example_path and Path(example_path).is_file():
        example_entries = _load(Path(example_path))

    results = []
    total_errors = 0
    total_warnings = 0

    for raw_path in args.paths:
        path = Path(raw_path)
        if not path.exists():
            print(
                f"dotenv-doctor: {path}: no such file or directory",
                file=sys.stderr,
            )
            return 2

        for env_path in _candidate_files(path, example_path):
            if not env_path.is_file():
                print(
                    f"dotenv-doctor: {env_path}: no such file or directory",
                    file=sys.stderr,
                )
                return 2
            entries = _load(env_path)
            findings = check_env(entries, example_entries, strict=args.strict)
            for finding in findings:
                if finding.severity == "error":
                    total_errors += 1
                elif finding.severity == "warning":
                    total_warnings += 1
            results.append(
                {"path": str(env_path), "findings": [asdict(f) for f in findings]}
            )

    if args.json:
        print(
            json.dumps(
                {
                    "files": results,
                    "summary": {
                        "errors": total_errors,
                        "warnings": total_warnings,
                        "files": len(results),
                    },
                },
                indent=2,
            )
        )
    else:
        for result in results:
            if not result["findings"]:
                print(f"{result['path']}: OK")
                continue
            for finding in result["findings"]:
                location = (
                    f"{result['path']}:{finding['line']}"
                    if finding["line"] is not None
                    else result["path"]
                )
                print(
                    f"{location}: [{finding['severity']}] "
                    f"{finding['code']}: {finding['message']}"
                )
        print(f"\nSummary: {total_errors} error(s), {total_warnings} warning(s)")

    if total_errors or (args.strict and total_warnings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
