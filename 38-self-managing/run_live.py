#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Fully autonomous self-management against a LIVE node: NL goal -> the LLM plans over
# the node's served routes PLUS the capabilities it could install -> the loop fills any
# gap (resolve -> governed provision -> re-discover) -> executes. The planner can ask
# for a capability the node doesn't serve yet; the loop installs it.
#
#   NODE_URL=http://192.168.188.201:8765 LLM_MODEL=... python3 run_live.py "<goal>"

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "urirun" / "adapters" / "python"))

from urirun.node import mesh
from urirun.node.client import NodeClient

import deployable_handlers as dh
import governance
import self_managing

NODE = os.environ.get("NODE_URL", "http://192.168.188.201:8765")
NODE_NAME = os.environ.get("NODE", "laptop")
MODEL = os.environ.get("LLM_MODEL") or os.environ.get("URIRUN_LLM_MODEL")
IDENTITY = os.path.expanduser(os.environ.get("IDENTITY", "~/.ssh/id_ed25519"))


def installable_routes() -> list[dict]:
    """The route shapes the loop can provision (self-contained stdlib handlers)."""
    out = []
    for scheme in dh.SELF_CONTAINED_SCHEMES:
        spec = dh.for_scheme(scheme, NODE_NAME)
        out += [{"uri": uri, "installable": True} for uri in spec["bindings"]["bindings"]]
    return out


def capability_aware_planner(goal, routes, prev_error, observation):
    """LLM plans over served routes UNION installable capabilities — so it may plan a
    capability the node doesn't have yet, which the loop then provisions."""
    from urirun.host.task_planner import quiet_completion
    served = [{"uri": r["uri"], "inputs": list((r.get("inputSchema", {}).get("properties") or {}).keys())} for r in routes]
    system = ("Build a urirun flow as strict JSON {\"steps\":[{\"id\":str,\"uri\":str,\"payload\":obj}]}. "
              "You may use the SERVED routes and also the INSTALLABLE routes (they will be installed "
              "on demand). Use exact field names; chain a prior output with '<field>_from':"
              "'<id>.result.value.<key>'. Minimal steps.")
    user = {"goal": goal, "served_routes": served, "installable_routes": installable_routes()}
    if prev_error:
        user["previous_attempt_failed"] = prev_error
    resp = quiet_completion(model=MODEL, temperature=0, response_format={"type": "json_object"},
                            messages=[{"role": "system", "content": system},
                                      {"role": "user", "content": json.dumps(user)}])
    return json.loads(resp["choices"][0]["message"]["content"])


def resolver(scheme: str) -> list[dict]:
    """Resolve a needed scheme to a self-contained deployable handler (this demo's source)."""
    spec = dh.for_scheme(scheme, NODE_NAME)
    if not spec:
        return []
    return [{"package": f"handler-{scheme}", "schemes": spec["schemes"], "_spec": spec,
             "install": {"local": str(HERE)}}]    # local if-uri path → trusted by governance


def make_install_fn():
    token = os.environ.get("URIRUN_NODE_TOKEN")          # token for a local test node
    def install_fn(client, candidate):
        spec = candidate["_spec"]
        res = mesh.deploy_to_node(client.base, bindings=spec["bindings"], code=spec["code"],
                                  allow=[f"{s}://**" for s in spec["schemes"]], merge=True,
                                  identity=None if token else IDENTITY, token=token)
        return bool(res.get("ok"))
    return install_fn


def main() -> int:
    if not MODEL:
        print("set LLM_MODEL (+ OPENROUTER_API_KEY)"); return 2
    client = NodeClient(NODE)
    goal = sys.argv[1] if len(sys.argv) > 1 else "Generate a unique id and write it to the session log."
    audit = []
    provision = governance.governed_provision(make_install_fn(), audit=audit.append)
    print(f"node {NODE_NAME} · goal: {goal}")
    print("before — schemes:", sorted(self_managing.served_schemes(client)))
    out = self_managing.self_managing_loop(client, goal, capability_aware_planner, resolver, provision, max_iter=6)
    print(f"\nloop ok={out['ok']} in {out.get('iterations')} iteration(s)")
    print("provisioned:", [p["scheme"] for p in out.get("provisioned", [])])
    print("audit:", [f"{a['connector']}:{a['decision']}" for a in audit])
    print("after  — schemes:", sorted(self_managing.served_schemes(client)))
    for t in out.get("trace", []):
        print(f"  {'✓' if t['ok'] else '✗'} {t['uri']}  ->  {json.dumps(t.get('data'))[:90]}")
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
