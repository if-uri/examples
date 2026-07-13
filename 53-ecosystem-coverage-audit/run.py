from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports" / "ecosystem-audit"


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        str(ROOT / "scripts" / "audit_ecosystem_coverage.py"),
        "--allow-example-gaps",
        "--json-out",
        str(REPORT_DIR / "audit.json"),
        "--markdown-out",
        str(REPORT_DIR / "audit.md"),
    ]
    return subprocess.run(command, cwd=ROOT).returncode


if __name__ == "__main__":
    raise SystemExit(main())
