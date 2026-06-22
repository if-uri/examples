#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# THE thesis, in one example: urirun is the layer BETWEEN
#   the runtime (connectors — any language)   and   the transport (any wire).
#
# We take connectors written in Go / PHP / JS / Python and drive each one over
# several transports (in-process, queue ≈ MQTT/NATS, HTTP, MCP). Every cell runs
# the SAME `{uri, payload}` and returns the SAME envelope — because neither the
# connector's language nor the transport touch the contract (URI + schema + policy
# + v2.run). Deterministic connectors return byte-identical output across all
# transports; the rest return ok across all transports.

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "urirun" / "adapters" / "python"))
sys.path.insert(0, str(HERE.parent / "07-transports"))     # transport_lib
sys.path.insert(0, str(HERE.parent / "19-all-connectors"))  # polyglot bindings + shims

import transport_lib                      # inprocess / queue / serverless / http / grpc
import check_all                          # emit_bindings + setup_polyglot_bin
import urirun
from urirun.runtime import v2_mcp

ALLOW = {"execute": {"allow": ["*"]}}

# connector (its language) + how to emit bindings + a route to drive.
# `lang`/`emit`/`pkg` feed check_all.emit_bindings; `label` is the display language.
CONNECTORS = [
    {"n": "hash", "lang": "go", "label": "Go", "emit": ["go", "run", ".", "bindings"],
     "uri": "hash://host/text/query/sha256", "payload": {"text": "ifuri"}, "det": True},
    {"n": "base64", "lang": "php", "label": "PHP", "emit": ["php", "cli.php", "bindings"],
     "uri": "codec://host/text/query/base64", "payload": {"text": "ifuri", "mode": "encode"}, "det": True},
    {"n": "uuid", "lang": "js", "label": "JS", "emit": ["node", "cli.js", "bindings"],
     "uri": "uuid://host/id/query/v4", "payload": {"count": 1}, "det": False},
    {"n": "time-tools", "lang": "py", "label": "Python", "pkg": "urirun_connector_time_tools",
     "uri": "time://host/clock/query/now", "payload": {}, "det": False},
]


def via_mcp(uri, payload, registry):
    """MCP as a transport: project the registry to MCP tools, then call the tool
    (which dispatches to the same v2.run)."""
    name = v2_mcp.tool_name(uri)
    return v2_mcp.call_tool(name, payload, registry, mode="execute", policy=ALLOW)


TRANSPORTS = {
    "inprocess": lambda u, p, r: transport_lib.run_via("inprocess", u, p, r),
    "queue~MQTT": lambda u, p, r: transport_lib.run_via("queue", u, p, r),
    "http": lambda u, p, r: transport_lib.run_via("http", u, p, r),
    "mcp": via_mcp,
}


def connector_output(envelope):
    """Find the connector's emitted JSON anywhere in the (possibly forwarded) envelope."""
    def walk(obj):
        if isinstance(obj, dict):
            out = obj.get("stdout")
            if isinstance(out, str) and out.strip():
                try:
                    return json.loads(out)
                except json.JSONDecodeError:
                    pass
            for value in obj.values():
                found = walk(value)
                if found is not None:
                    return found
        return None
    return walk(envelope)


def main() -> int:
    check_all.setup_polyglot_bin()
    cols = list(TRANSPORTS)
    print(f"\n{'connector (runtime)':<22}" + "".join(f"{c:<13}" for c in cols) + "consistent")
    print("-" * 92)
    all_ok = True
    for c in CONNECTORS:
        registry = urirun.compile_registry(check_all.emit_bindings(c))
        cells, outputs = [], []
        for t in cols:
            try:
                env = TRANSPORTS[t](c["uri"], c["payload"], registry)
                ok = bool(env.get("ok")) or bool((connector_output(env) or {}).get("ok"))
                cells.append("✓" if ok else "✗")
                outputs.append(json.dumps(connector_output(env), sort_keys=True))
                all_ok = all_ok and ok
            except Exception as exc:  # noqa: BLE001
                cells.append(f"ERR:{type(exc).__name__}")
                outputs.append(None)
                all_ok = False
        if c["det"]:
            consistent = "identical out" if len(set(outputs)) == 1 else "DIFFERS!"
            all_ok = all_ok and (len(set(outputs)) == 1)
        else:
            consistent = "ok everywhere"
        label = f"{c['n']} ({c['label']})"
        print(f"{label:<22}" + "".join(f"{x:<13}" for x in cells) + consistent)
    print("-" * 92)
    print(f"transports: {', '.join(cols)}  (grpc available with grpcio; ws is the next adapter)")
    print("VERDICT:", "urirun sits between any-language runtime and any transport ✓" if all_ok else "FAILED")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
