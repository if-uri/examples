#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Mesh variant of repair_flow: the LLM runs locally (brain), but the generated
# YAML flow is executed on a REMOTE node (hands) over HTTP, and failures are fed
# back for a correction.
#
#   urirun host mesh (officepc, …)
#       │ GET /routes  → action space (what the node can do)
#       ▼
#   llm://host/chat/command/complete  → YAML flow
#       │ per step: POST {node}/run {uri, payload}   (urirun.runtime.v2_service)
#       ▼
#   node runs it under ITS OWN --allow; failure → error fed back to the LLM → fix
#
# The node enforces its own allow-policy, so the host can only run what the node
# already exposes — the LLM cannot widen that surface.

from __future__ import annotations

import argparse
import json
import os

import urirun
from urirun.node import mesh as meshlib
from urirun.runtime import v2_service

import repair_flow

DEFAULT_CONFIG = os.path.expanduser("~/.urirun-host/mesh.json")


def load_mesh_config(path: str | None) -> tuple[dict, str]:
    path = path or os.environ.get("URIRUN_MESH_CONFIG") or DEFAULT_CONFIG
    with open(path, encoding="utf-8") as handle:
        return json.load(handle), path


def mesh_runner(uri, registry, payload, _allow):
    """Forward one step to the remote node that owns its target (the node's own
    --allow is the gate; the host-side allow is unused for forwarded routes)."""
    return v2_service.call(uri, payload, registry=registry, mode="execute")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="LLM-generated, self-repairing flow run on a remote mesh node")
    ap.add_argument("goal", nargs="?", default="report the node's runtime health")
    ap.add_argument("--config", help="mesh config (default: $URIRUN_MESH_CONFIG or ~/.urirun-host/mesh.json)")
    ap.add_argument("--node", action="append", help="restrict to node name(s); repeatable")
    ap.add_argument("--model", default=os.getenv("URIRUN_LLM_MODEL", "llama3"))
    ap.add_argument("--base-url", default=os.getenv("URIRUN_LLM_BASE_URL", "http://localhost:11434"))
    ap.add_argument("--max-attempts", type=int, default=3)
    args = ap.parse_args(argv)

    config, path = load_mesh_config(args.config)
    print(f"mesh: {path}")

    # 1) discover what the node(s) expose → action space + serviceMap for forwarding
    discovered = meshlib.discover_mesh(config)
    routes = discovered["routes"]
    if args.node:
        routes = [r for r in routes if r.get("node") in set(args.node)]
    if not routes:
        print("no reachable routes — check `urirun host nodes` / `urirun host routes`")
        return 1
    registry = meshlib.registry_from_routes(routes)
    os.environ["URI_SERVICE_MAP"] = json.dumps(discovered["serviceMap"])  # enable HTTP forward

    schemes = sorted({r["uri"].split("://", 1)[0] for r in routes})
    allow = [f"{s}://*" for s in schemes]
    print(f"nodes: {sorted({r.get('node') for r in routes})} · routes: {len(routes)} · schemes: {schemes}")

    # 2) the LLM that writes the flow runs locally (the host's own llm:// connector)
    import urirun_connector_llm.core as llm
    llm_registry = llm.conn.registry()

    # 3) generate → forward to node → repair on failure
    report = repair_flow.generate_run_repair(
        args.goal, registry, llm_registry, model=args.model, base_url=args.base_url,
        allow=allow, max_attempts=args.max_attempts, runner=mesh_runner,
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
