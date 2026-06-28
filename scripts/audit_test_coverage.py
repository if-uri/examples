#!/usr/bin/env python3
# Part of the ifURI solution.
"""Report how much of examples/ is covered by the smoke runner.

The main run_tests.sh script is intentionally a fast host smoke. This audit keeps
that honest by showing which example directories have pytest tests but are not in
the smoke script.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Iterable

EXAMPLE_RE = re.compile(r"^\d{2}-[A-Za-z0-9_.-]+$")
MENTION_RE = re.compile(r"\b(\d{2}-[A-Za-z0-9_.-]+)\b")


def _numbered_dirs(root: Path) -> list[str]:
    return sorted(p.name for p in root.iterdir() if p.is_dir() and EXAMPLE_RE.match(p.name))


def _test_dirs(root: Path) -> list[str]:
    found: set[str] = set()
    for pattern in ("test_*.py", "*_test.py"):
        for test in root.glob(f"*/{pattern}"):
            if test.parent.is_dir() and EXAMPLE_RE.match(test.parent.name):
                found.add(test.parent.name)
    return sorted(found)


def _mentioned_dirs(root: Path, script: Path) -> list[str]:
    try:
        text = script.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    dirs = set(_numbered_dirs(root))
    return sorted(name for name in set(MENTION_RE.findall(text)) if name in dirs)


def audit(root: Path, script: Path) -> dict[str, object]:
    numbered = _numbered_dirs(root)
    pytest_dirs = _test_dirs(root)
    smoke_dirs = _mentioned_dirs(root, script)
    smoke = set(smoke_dirs)
    tested = set(pytest_dirs)
    return {
        "root": str(root),
        "smokeScript": str(script),
        "exampleDirs": numbered,
        "pytestDirs": pytest_dirs,
        "smokeDirs": smoke_dirs,
        "pytestDirsNotInSmoke": sorted(tested - smoke),
        "smokeDirsWithoutPytest": sorted(smoke - tested),
        "dirsWithoutPytestAndNotInSmoke": sorted(set(numbered) - tested - smoke),
        "counts": {
            "examples": len(numbered),
            "pytestDirs": len(pytest_dirs),
            "smokeDirs": len(smoke_dirs),
            "pytestDirsNotInSmoke": len(tested - smoke),
            "smokeDirsWithoutPytest": len(smoke - tested),
            "dirsWithoutPytestAndNotInSmoke": len(set(numbered) - tested - smoke),
        },
    }


def _wrap(items: Iterable[str], width: int = 6) -> list[str]:
    out: list[str] = []
    row: list[str] = []
    for item in items:
        row.append(item)
        if len(row) >= width:
            out.append(", ".join(row))
            row = []
    if row:
        out.append(", ".join(row))
    return out


def _print_report(rep: dict[str, object], verbose: bool) -> None:
    counts = rep["counts"]
    assert isinstance(counts, dict)
    print(
        "examples coverage: "
        f"{counts['examples']} dirs, "
        f"{counts['pytestDirs']} dirs with pytest, "
        f"{counts['smokeDirs']} dirs mentioned by run_tests.sh"
    )
    print(
        "smoke gap: "
        f"{counts['pytestDirsNotInSmoke']} pytest dirs are not in the smoke runner; "
        "run `make test-all` for the full host pytest suite"
    )
    if verbose:
        for key, title in (
            ("pytestDirsNotInSmoke", "pytest dirs not in smoke"),
            ("smokeDirsWithoutPytest", "smoke dirs without pytest"),
            ("dirsWithoutPytestAndNotInSmoke", "dirs without pytest and not in smoke"),
        ):
            items = rep[key]
            assert isinstance(items, list)
            print(f"{title}:")
            if not items:
                print("  (none)")
                continue
            for line in _wrap(items):
                print(f"  {line}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--script", default=None)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--fail-on-uncovered-pytest", action="store_true")
    ns = parser.parse_args(argv)

    root = Path(ns.root).resolve()
    script = Path(ns.script).resolve() if ns.script else root / "run_tests.sh"
    rep = audit(root, script)
    if ns.json:
        print(json.dumps(rep, indent=2, sort_keys=True))
    else:
        _print_report(rep, ns.verbose)
    if ns.fail_on_uncovered_pytest and rep["pytestDirsNotInSmoke"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
