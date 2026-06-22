#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Minimal flow runner: load a YAML/JSON flow and run its steps through the urirun
# runtime, chaining prior results (`<key>_from`) and gating with policy. A flow is
#   registry: <bindings-or-registry-path>
#   allow: [ "<glob>", ... ]            # optional
#   secretAllow: [ "<glob>", ... ]      # optional
#   steps:
#     - id: <name>
#       uri: <scheme://...>
#       payload: { ... }                # values ending in _from dig prior results
#       depends_on: [ <id>, ... ]       # optional

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import urirun
from urirun.node import mesh
from urirun.runtime import v2


def load(path: str) -> dict:
    text = Path(path).read_text(encoding="utf-8")
    if path.endswith((".yaml", ".yml")):
        import yaml
        return yaml.safe_load(text)
    return json.loads(text)


def run_flow(flow: dict, base_dir: Path, *, execute: bool, allow, secret_allow) -> dict:
    # #6: resolve the registry ONCE and share ONE warm worker pool across every
    # step, so a flow that hits the same connector N times pays the connector's
    # import once (not one `python -m urirun.exec` cold start per step).
    registry = v2.load_registry_arg(str(base_dir / flow["registry"]))
    policy = urirun.policy(allow=list(allow or flow.get("allow") or []),
                           secret_allow=list(secret_allow or flow.get("secretAllow") or []))
    from urirun.runtime.worker import ConnectorPools

    pools = ConnectorPools()
    executors = mesh._pool_executors(pools)
    results: dict = {}
    timeline = []
    try:
        for step in flow["steps"]:
            missing = [d for d in step.get("depends_on", []) if d not in results]
            if missing:
                raise SystemExit(f"{step['id']} missing dependencies: {missing}")
            payload = mesh.resolve_step_payload(step.get("payload") or {}, results)
            env = urirun.run(step["uri"], registry, payload,
                             mode="execute" if execute else "dry-run", policy=policy,
                             executors=executors)
            results[step["id"]] = env
            ok = bool(env.get("ok"))
            timeline.append({"id": step["id"], "uri": step["uri"], "ok": ok})
            mark = "✓" if ok else "✗"
            print(f"  {mark} {step['id']:<18} {step['uri']}")
            if not ok:
                reason = (env.get("decision") or {}).get("reason") or env.get("error") or "step failed"
                print(f"      stopped: {reason}")
                break
    finally:
        pools.close()
    return {"ok": all(t["ok"] for t in timeline), "timeline": timeline, "results": results}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Run a urirun flow (YAML/JSON)")
    ap.add_argument("flow")
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--allow", action="append", default=[])
    ap.add_argument("--secret-allow", action="append", default=[])
    args = ap.parse_args(argv)
    flow = load(args.flow)
    print(f"flow: {flow.get('task', {}).get('title') or Path(args.flow).stem}  (mode={'execute' if args.execute else 'dry-run'})")
    result = run_flow(flow, Path(args.flow).resolve().parent,
                      execute=args.execute, allow=args.allow, secret_allow=args.secret_allow)
    print(f"\n{'OK' if result['ok'] else 'FAILED'} — {sum(t['ok'] for t in result['timeline'])}/{len(result['timeline'])} steps")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
