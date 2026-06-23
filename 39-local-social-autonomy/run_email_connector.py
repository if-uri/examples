#!/usr/bin/env python3
"""Run extract_local_invoices from urirun-connector-email and print summary."""
import json
from urirun_connector_email.core import extract_local_invoices

result = extract_local_invoices(
    start_date="2026-03-01",
    end_date="2026-06-01",
    downloads_dir="~/Downloads",
)

# Print summary without full details (too large for stdout)
summary = {k: v for k, v in result.items() if k != "details"}
summary["detail_count"] = len(result.get("details", []))
print(json.dumps(summary, indent=2))
