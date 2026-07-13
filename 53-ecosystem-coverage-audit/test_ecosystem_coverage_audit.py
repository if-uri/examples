from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_ecosystem_coverage_map_is_auditable(tmp_path):
    json_out = tmp_path / "audit.json"
    md_out = tmp_path / "audit.md"

    cp = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "audit_ecosystem_coverage.py"),
            "--allow-example-gaps",
            "--json-out",
            str(json_out),
            "--markdown-out",
            str(md_out),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )

    assert cp.returncode == 0, cp.stderr + cp.stdout
    report = json.loads(json_out.read_text(encoding="utf-8"))
    assert report["repositories"]["classified"] >= 100
    assert "if-uri/urirun" in (ROOT / "ci" / "ecosystem-coverage.yml").read_text(encoding="utf-8")
    assert md_out.exists()


def test_unclassified_repository_fails(tmp_path):
    repos = tmp_path / "repos.txt"
    repos.write_text("if-uri/urirun\nif-uri/new-unclassified-repo\n", encoding="utf-8")

    cp = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "audit_ecosystem_coverage.py"),
            "--repos-file",
            str(repos),
            "--allow-example-gaps",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )

    assert cp.returncode == 1
    assert "Unclassified if-uri repository: if-uri/new-unclassified-repo" in cp.stderr
