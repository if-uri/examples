#!/usr/bin/env python3
"""Audit if-uri ecosystem coverage against the examples catalog."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request
from pathlib import Path
from typing import Any

EXAMPLE_RE = re.compile(r"^\d{2}-[A-Za-z0-9_.-]+$")
VALID_LEVELS = {"complete", "partial", "missing", "not-applicable", "deprecated"}
VALID_STATUSES = {
    "active", "experimental", "planned", "deprecated", "archived",
    "documentation", "website", "infrastructure", "test-only",
}


def numbered_examples(root: Path) -> list[str]:
    return sorted(p.name for p in root.iterdir() if p.is_dir() and EXAMPLE_RE.match(p.name))


def has_test(example_dir: Path) -> bool:
    return any(example_dir.glob("test_*.py")) or any(example_dir.glob("*_test.py"))


def load_coverage(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def repos_from_file(path: Path) -> list[str]:
    names: list[str] = []
    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-16")
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        names.append(line.split()[0])
    return sorted(set(names))


def fetch_org_repos(org: str) -> list[str]:
    repos: list[str] = []
    page = 1
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "if-uri-examples-audit"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    while True:
        url = f"https://api.github.com/orgs/{org}/repos?per_page=100&page={page}"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if not data:
            break
        repos.extend(item["full_name"] for item in data)
        page += 1
    return sorted(set(repos))


def audit(root: Path, coverage_path: Path, repos: list[str] | None = None) -> dict[str, Any]:
    coverage = load_coverage(coverage_path)
    repo_map: dict[str, dict[str, Any]] = coverage.get("repositories", {})
    examples = numbered_examples(root)
    example_set = set(examples)
    errors: list[str] = []
    warnings: list[str] = []

    for repo, entry in sorted(repo_map.items()):
        status = entry.get("status")
        level = entry.get("level")
        if status not in VALID_STATUSES:
            errors.append(f"{repo}: invalid status {status!r}")
        if level not in VALID_LEVELS:
            errors.append(f"{repo}: invalid level {level!r}")
        if level == "not-applicable" and not entry.get("reason"):
            errors.append(f"{repo}: not-applicable requires a concrete reason")
        for example in entry.get("examples", []):
            if example not in example_set:
                errors.append(f"{repo}: referenced example does not exist: {example}")

    if repos is not None:
        known = set(repo_map)
        for repo in sorted(set(repos) - known):
            errors.append(f"Unclassified if-uri repository: {repo}\nReview it and update ci/ecosystem-coverage.yml.")

    assigned = {example for entry in repo_map.values() for example in entry.get("examples", [])}
    unassigned = sorted(example_set - assigned)
    for example in unassigned:
        errors.append(f"Unassigned example: {example}\nMap it to a repository in ci/ecosystem-coverage.yml.")

    missing_readme = []
    missing_tests = []
    for example in examples:
        path = root / example
        if not (path / "README.md").exists():
            missing_readme.append(example)
            errors.append(f"Example without README: {example}")
        if not has_test(path):
            missing_tests.append(example)
            warnings.append(f"Example without pytest test: {example}")

    levels = {}
    statuses = {}
    for entry in repo_map.values():
        levels[entry.get("level", "unknown")] = levels.get(entry.get("level", "unknown"), 0) + 1
        statuses[entry.get("status", "unknown")] = statuses.get(entry.get("status", "unknown"), 0) + 1

    return {
        "coverage": str(coverage_path),
        "repositories": {
            "classified": len(repo_map),
            "observed": len(repos) if repos is not None else None,
            "levels": levels,
            "statuses": statuses,
        },
        "examples": {
            "count": len(examples),
            "assigned": len(assigned & example_set),
            "unassigned": unassigned,
            "missing_readme": missing_readme,
            "missing_tests": missing_tests,
        },
        "errors": errors,
        "warnings": warnings,
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Ecosystem Coverage Audit",
        "",
        f"- Classified repositories: {report['repositories']['classified']}",
        f"- Observed repositories: {report['repositories']['observed']}",
        f"- Examples: {report['examples']['count']}",
        f"- Assigned examples: {report['examples']['assigned']}",
        f"- Errors: {len(report['errors'])}",
        f"- Warnings: {len(report['warnings'])}",
        "",
        "## Errors",
    ]
    lines.extend(f"- {item}" for item in report["errors"]) if report["errors"] else lines.append("- none")
    lines.append("")
    lines.append("## Warnings")
    lines.extend(f"- {item}" for item in report["warnings"]) if report["warnings"] else lines.append("- none")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--coverage", default=None)
    parser.add_argument("--repos-file", default=None)
    parser.add_argument("--fetch-org", default=None)
    parser.add_argument("--json-out", default=None)
    parser.add_argument("--markdown-out", default=None)
    parser.add_argument("--allow-example-gaps", action="store_true",
                        help="Treat missing per-example tests/assignment as warnings for legacy examples.")
    ns = parser.parse_args(argv)

    root = Path(ns.root).resolve()
    coverage = Path(ns.coverage).resolve() if ns.coverage else root / "ci" / "ecosystem-coverage.yml"
    repos = None
    if ns.repos_file:
        repos = repos_from_file(Path(ns.repos_file))
    elif ns.fetch_org:
        repos = fetch_org_repos(ns.fetch_org)

    report = audit(root, coverage, repos)
    effective_errors = list(report["errors"])
    if ns.allow_example_gaps:
        effective_errors = [
            error for error in effective_errors
            if not error.startswith("Unassigned example: ")
            and not error.startswith("Example without README: ")
        ]
    if ns.json_out:
        Path(ns.json_out).write_text(json.dumps(report, indent=2), encoding="utf-8")
    else:
        print(json.dumps(report, indent=2))
    if ns.markdown_out:
        write_markdown(report, Path(ns.markdown_out))
    for error in effective_errors:
        print(error, file=sys.stderr)
    return 1 if effective_errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
