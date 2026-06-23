#!/usr/bin/env python3
"""Compatibility wrapper for the email connector invoice extractor."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
for path in (ROOT / "urirun-connector-email", ROOT / "urirun" / "adapters" / "python"):
    value = str(path)
    if value not in sys.path:
        sys.path.insert(0, value)

from urirun_connector_email import extract_local_invoices  # noqa: E402


def run_extraction() -> dict:
    return extract_local_invoices(
        start_date="2026-03-01",
        end_date="2026-06-01",
        months="2026.03,2026.04,2026.05",
        downloads_dir="~/Downloads",
        dry_run=False,
        group_by_account=False,
        json_out="~/Downloads/invoice_export_2026.03-2026.05_report.json",
    )


if __name__ == "__main__":
    print(json.dumps(run_extraction(), ensure_ascii=False, indent=2))
