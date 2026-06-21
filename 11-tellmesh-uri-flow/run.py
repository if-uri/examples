#!/usr/bin/env python3
"""Adopt tellmesh capability packs as URI bindings, then run a uri2flow-style DAG
across them — entirely through urirun.

  1. each vendored manifest (packs/*.yaml) is adopted 1:1 to bindings.v2
     (`urirun.runtime.adopt_pack`) and merged into one registry;
  2. handlers are hydrated with stubs that return canned data, so the flow runs
     anywhere — install the real tellmesh packs to swap in live handlers;
  3. the flow (flow.yaml) is executed step by step, resolving `*_from` payload
     references from earlier step results, each step dispatched through urirun.

Run:  pip install urirun pyyaml  &&  python run.py
"""
from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent

try:
    import yaml
    from urirun.runtime import adopt_pack
    from urirun import v2, _registry as reg, _runtime as rt
except ImportError as exc:  # pragma: no cover
    sys.exit(f"missing dependency ({exc}); run: pip install urirun pyyaml")


# 1) adopt every vendored pack manifest into one registry --------------------
bindings: dict = {}
for manifest in sorted((HERE / "packs").glob("*.yaml")):
    bindings.update(adopt_pack.adopt_document(manifest)["bindings"])
registry = v2.compile_registry({"version": v2.VERSION, "bindings": bindings})
schemes = sorted({u.split("://", 1)[0] for u in bindings})
print(f"adopted {len(bindings)} routes across {len(schemes)} packs: {', '.join(schemes)}\n")


# 2) hydrate handlers with canned stubs (real packs replace these) -----------
def stub_for(ref: str):
    if "ocr" in ref:
        return lambda t, a, p, d: {"text": "Invoice #4471 — total 1 240.00 PLN, due 2026-07-01"}
    if "vql" in ref or "detect" in ref:
        return lambda t, a, p, d: {"elements": [{"label": "Pay now", "box": [880, 540, 120, 40]}]}
    if "analyze" in ref or "llm" in ref:
        return lambda t, a, p, d: {
            "summary": "An overdue invoice is on screen and a 'Pay now' button is visible.",
            "action": "notify",
        }
    return lambda t, a, p, d: {"sent": True, "to": (p or {}).get("to", "ops")}


refs = {b["ref"]: stub_for(b["ref"]) for b in bindings.values() if b.get("ref")}
hydrated = reg.hydrate_registry(registry, refs)
ALLOW = [f"{s}://*" for s in schemes]


# 3) execute the flow DAG ----------------------------------------------------
def resolve_payload(payload: dict, results: dict) -> dict:
    out: dict = {}
    for key, value in (payload or {}).items():
        if key.endswith("_from") and isinstance(value, str):
            step, _, path = value.partition(".")
            cursor = results.get(step)
            for segment in filter(None, path.split(".")):
                cursor = cursor.get(segment) if isinstance(cursor, dict) else None
            out[key[:-5]] = cursor
        else:
            out[key] = value
    return out


flow = yaml.safe_load((HERE / "flow.yaml").read_text(encoding="utf-8"))
print(f"flow: {flow['task']['id']} — {len(flow['steps'])} steps")
results: dict = {}
ok = True
for step in flow["steps"]:  # vendored in dependency order
    uri = step["uri"].replace("{host}", "host")
    payload = resolve_payload(step.get("payload"), results)
    env = rt.run(uri, hydrated, payload=payload, mode="execute", policy={"execute": {"allow": ALLOW}})
    value = (env.get("result") or {}).get("value", env.get("result"))
    results[step["id"]] = value
    ok = ok and bool(env.get("ok"))
    print(f"  [{step['id']:<11}] {uri}")
    print(f"        in : {json.dumps(payload) if payload else '-'}")
    print(f"        out: {json.dumps(value)}")

print(f"\nflow ok: {ok}")
sys.exit(0 if ok else 1)
