#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Check every urirun-connector-* through the same contract, regardless of the
# language it is written in (Python / PHP / Go / JS):
#   emit urirun_bindings()  ->  urirun validate  ->  urirun compile
#   ->  run a representative route (offline/network) or mark it config-gated.
#
# This is the "one contract, many connectors, many languages" proof.

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import urirun

ROOT = Path(__file__).resolve().parents[2]            # if-uri/
UP = str(ROOT / "urirun" / "adapters" / "python")

# How to emit bindings per connector, and a representative route to run.
# run=None  -> validate-only (needs runtime config: creds / broker / device).
CONNECTORS = [
    # polyglot (CLI `bindings`)
    {"n": "base64", "lang": "php", "emit": ["php", "cli.php", "bindings"],
     "run": ("codec://host/text/query/base64", {"text": "ifuri", "mode": "encode"})},
    {"n": "hash", "lang": "go", "emit": ["go", "run", ".", "bindings"],
     "run": ("hash://host/text/query/sha256", {"text": "ifuri"})},
    {"n": "uuid", "lang": "js", "emit": ["node", "cli.js", "bindings"],
     "run": ("uuid://host/id/query/v4", {"count": 1})},
    # python (import the package)
    {"n": "time-tools", "lang": "py", "pkg": "urirun_connector_time_tools",
     "run": ("time://host/clock/query/now", {})},
    {"n": "uuid", "lang": "js"},  # placeholder removed below
    {"n": "mcp-filesystem", "lang": "py", "pkg": "urirun_connector_mcp_filesystem",
     "run": ("fs://host/dir/query/list", {"path": "."})},
    {"n": "http-check", "lang": "py", "pkg": "urirun_connector_http_check",
     "run": ("httpcheck://host/http/query/status", {"url": "https://example.com"})},
    {"n": "domain-monitor", "lang": "py", "pkg": "urirun_connector_domain_monitor",
     "run": ("monitor://host/dns/query/current",
             {"domain": "example.com", "current_records": '[{"Name":"@","Type":"A","Address":"203.0.113.10"}]'})},
    {"n": "browser-control", "lang": "py", "pkg": "urirun_connector_browser_control",
     "run": ("browser://chrome/page/query/text", {"url": "https://example.com", "max": 80})},
    {"n": "get-node", "lang": "py", "pkg": "urirun_connector_get_node",
     "run": ("node://get/installer/query/script", {})},
    {"n": "email", "lang": "py", "pkg": "urirun_connector_email",
     "run": ("email://host/inbox/query/list", {})},          # safe: "not configured" without creds
    {"n": "sqlite-context", "lang": "py", "pkg": "urirun_connector_sqlite_context",
     "run": ("log://host/logs/query/recent", {"limit": 5})},
    {"n": "mqtt", "lang": "py", "pkg": "urirun_connector_mqtt",
     "run": ("device://device-01/led/command/set", {"state": "on"})},  # reports topic, no broker bound
    {"n": "ksef", "lang": "py", "pkg": "urirun_connector_ksef"},          # live MF API
    {"n": "planfile", "lang": "py", "pkg": "urirun_connector_planfile"},  # needs a planfile project
    {"n": "namecheap-dns", "lang": "py", "pkg": "urirun_connector_namecheap_dns"},  # API creds
    {"n": "llm", "lang": "py", "pkg": "urirun_connector_llm"},            # API key
    {"n": "kvm", "lang": "py", "pkg": "urirun_connector_kvm"},            # KVM device
]
CONNECTORS = [c for c in CONNECTORS if "pkg" in c or "emit" in c]  # drop the placeholder


def setup_polyglot_bin() -> None:
    """Put `urirun-connector-{base64,hash,uuid}` on PATH as shims so the Python
    runtime can spawn the PHP / Go / JS connectors their argv references."""
    binroot = Path(__file__).resolve().parent / ".bin"
    binroot.mkdir(exist_ok=True)
    go_dir = ROOT / "urirun-connector-hash"
    go_bin = go_dir / "urirun-connector-hash"
    if not go_bin.exists():
        subprocess.run(["go", "build", "-o", "urirun-connector-hash", "."], cwd=go_dir, check=True, timeout=180)
    shims = {
        "urirun-connector-base64": f'exec php "{ROOT}/urirun-connector-base64/cli.php" "$@"',
        "urirun-connector-hash": f'exec "{go_bin}" "$@"',
        "urirun-connector-uuid": f'exec node "{ROOT}/urirun-connector-uuid/cli.js" "$@"',
    }
    for name, body in shims.items():
        path = binroot / name
        path.write_text(f"#!/bin/sh\n{body}\n")
        path.chmod(0o755)
    os.environ["PATH"] = f"{binroot}{os.pathsep}{os.environ['PATH']}"


def emit_bindings(c) -> dict:
    cdir = ROOT / f"urirun-connector-{c['n']}"
    if c["lang"] == "py":
        env = dict(os.environ, PYTHONPATH=f"{UP}{os.pathsep}{cdir}")
        code = f"import json,{c['pkg']} as m;print(json.dumps(m.urirun_bindings()))"
        out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, timeout=60)
    else:
        out = subprocess.run(c["emit"], capture_output=True, text=True, cwd=cdir, timeout=120)
    if out.returncode != 0:
        raise RuntimeError((out.stderr or out.stdout)[:120])
    return json.loads(out.stdout)


def check(c) -> dict:
    row = {"connector": c["n"], "lang": c["lang"]}
    try:
        doc = emit_bindings(c)
        row["routes"] = len(doc["bindings"])
        rep = urirun.validate_binding_document(doc)
        row["valid"] = rep["ok"]
        if not rep["ok"]:
            row["status"] = "INVALID"
            return row
        registry = urirun.compile_registry(doc)
        row["compiled"] = True
        if not c.get("run"):
            row["status"] = "valid (config-gated)"
            return row
        uri, payload = c["run"]
        scheme = uri.split("://", 1)[0]
        policy = urirun.policy(allow=[f"{scheme}://*"])
        result = urirun.run(uri, registry, payload, mode="execute", policy=policy)
        ok = bool(result.get("ok"))
        row["ran"] = uri
        row["status"] = "RAN ✓" if ok else f"run-failed: {(result.get('decision') or {}).get('reason') or result.get('error')}"
        row["ok"] = ok
    except Exception as exc:  # noqa: BLE001
        row["status"] = f"ERROR: {type(exc).__name__}: {exc}"
        row["valid"] = False
    return row


def main() -> int:
    setup_polyglot_bin()
    rows = [check(c) for c in CONNECTORS]
    print(f"\n{'connector':<20}{'lang':<6}{'routes':<8}{'valid':<7}status")
    print("-" * 88)
    for r in rows:
        print(f"{r['connector']:<20}{r['lang']:<6}{str(r.get('routes','-')):<8}"
              f"{('✓' if r.get('valid') else '✗'):<7}{r['status']}")
    valid = sum(1 for r in rows if r.get("valid"))
    ran = sum(1 for r in rows if r.get("ok"))
    print("-" * 88)
    print(f"{valid}/{len(rows)} valid · {ran} executed a route · "
          f"{len(rows) - valid} broken")
    return 0 if valid == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
