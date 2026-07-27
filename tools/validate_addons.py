#!/usr/bin/env python3
"""Validate the current Fabulor Python and Tcl add-on layout."""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_SUFFIXES = {".py", ".tcl"}
METADATA_FIELDS = ("Name", "Version", "Description")


def fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)


def add_on_directories() -> list[Path]:
    return sorted(
        path
        for path in ROOT.iterdir()
        if path.is_dir() and not path.name.startswith(".") and path.name != "tools"
    )


def metadata_value(text: str, field: str) -> str | None:
    pattern = re.compile(
        rf"^\s*#\s*Fabulor-{re.escape(field)}:\s*(.+?)\s*$",
        re.MULTILINE,
    )
    match = pattern.search(text)
    return match.group(1) if match else None


def validate_source(path: Path, names: dict[str, Path]) -> int:
    errors = 0
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        fail(f"{path.relative_to(ROOT)} is not valid UTF-8: {exc}")
        return 1

    values: dict[str, str] = {}
    for field in METADATA_FIELDS:
        value = metadata_value(text, field)
        if value is None:
            fail(f"{path.relative_to(ROOT)} lacks Fabulor-{field} metadata")
            errors += 1
        else:
            values[field] = value

    name = values.get("Name")
    if name:
        key = name.casefold()
        previous = names.get(key)
        if previous is not None:
            fail(
                f"duplicate add-on name {name!r} in "
                f"{previous.relative_to(ROOT)} and {path.relative_to(ROOT)}"
            )
            errors += 1
        else:
            names[key] = path

    if path.suffix == ".py":
        try:
            ast.parse(text, filename=str(path))
        except SyntaxError as exc:
            fail(f"{path.relative_to(ROOT)} has invalid Python syntax: {exc}")
            errors += 1

    return errors


def main() -> int:
    errors = 0
    names: dict[str, Path] = {}
    directories = add_on_directories()

    if not directories:
        fail("no add-on directories found")
        return 1

    for directory in directories:
        relative = directory.relative_to(ROOT)
        if not (directory / "README.md").is_file():
            fail(f"{relative} lacks README.md")
            errors += 1

        sources = sorted(
            path
            for path in directory.iterdir()
            if path.is_file() and path.suffix.lower() in SOURCE_SUFFIXES
        )
        if not sources:
            fail(f"{relative} has no Python or Tcl source file")
            errors += 1
            continue

        for source in sources:
            errors += validate_source(source, names)

    if errors:
        print(f"Validation failed with {errors} error(s).", file=sys.stderr)
        return 1

    print(f"Validated {len(directories)} add-ons and {len(names)} source files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
