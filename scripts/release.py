#!/usr/bin/env python3
"""Validate release metadata and extract the notes for an exact release tag."""

import argparse
from datetime import date
import json
from pathlib import Path
import re


VERSION_PATTERN = r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)"


def release_metadata(root: Path, tag: str | None = None) -> tuple[str, str]:
    version = (root / "VERSION").read_text().strip()
    if not re.fullmatch(VERSION_PATTERN, version):
        raise ValueError("VERSION must contain MAJOR.MINOR.PATCH without leading zeroes")
    if tag is not None and tag != f"v{version}":
        raise ValueError(f"Tag must match VERSION: expected v{version}, got {tag}")

    metadata = json.loads((root / "foundation.json").read_text())
    if not isinstance(metadata, dict) or metadata.get("schema") != 1 or metadata.get("version") != version:
        raise ValueError("foundation.json must use schema 1 and its version must match VERSION")

    changelog = (root / "CHANGELOG.md").read_text()
    headings = list(re.finditer(r"^## \[([^\]]+)\](.*)$", changelog, re.MULTILINE))
    releases = [heading for heading in headings if heading[1] == version]
    if len(releases) != 1:
        raise ValueError(f"CHANGELOG.md must have exactly one section for [{version}]")
    heading = releases[0]
    release_date = re.fullmatch(r" - (\d{4}-\d{2}-\d{2})", heading[2])
    if release_date is None:
        raise ValueError("The release changelog section must have an ISO release date")
    date.fromisoformat(release_date[1])
    next_heading = next((item.start() for item in headings if item.start() > heading.start()), len(changelog))
    notes = changelog[heading.end():next_heading].strip()
    # Keep trailing reference links out of GitHub release notes.
    notes = re.split(r"^\[[^\]]+\]: ", notes, maxsplit=1, flags=re.MULTILINE)[0].strip()
    if not re.search(r"^- \S", notes, re.MULTILINE):
        raise ValueError("The release changelog section must contain release notes")
    return version, notes + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Validate the prepared release")
    parser.add_argument("--tag", help="Require the tag to match VERSION")
    parser.add_argument("--notes-file", type=Path, help="Write only this version's release notes")
    args = parser.parse_args()
    try:
        version, notes = release_metadata(Path(__file__).resolve().parents[1], args.tag)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Release metadata error: {error}\n")
    if args.notes_file is not None:
        args.notes_file.write_text(notes)
    print(f"Release metadata valid: v{version}")


if __name__ == "__main__":
    main()
