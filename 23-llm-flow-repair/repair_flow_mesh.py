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


def make_mesh_runner(mode: str = "execute"):
    """A step runner that forwards to the remote node owning the target. In
    ``dry-run`` the node is never touched — ``v2_service.call`` still validates the
    payload against the node's published schema, so a bad LLM flow is caught (and
    repaired) before anything executes. The node's own --allow is the real gate."""
    def runner(uri, registry, payload, _allow):
        return v2_service.call(uri, payload, registry=registry, mode=mode)
    return runner


def _load_env_file(path: str) -> None:
    """Minimal .env loader (KEY=VALUE) so OPENROUTER_API_KEY / LLM_MODEL are set."""
    try:
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    except OSError:
        pass


def litellm_ask(_llm_registry, prompt: str, *, model: str, base_url: str) -> str:
    """Generate via litellm — works natively with OpenRouter/OpenAI/Anthropic/Ollama
    (model prefix + matching *_API_KEY), unlike the Ollama-only llm:// connector."""
    from litellm import completion
    resp = completion(model=model, messages=[{"role": "user", "content": prompt}], temperature=0)
    return resp["choices"][0]["message"]["content"]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="LLM-generated, self-repairing flow run on a remote mesh node")
    ap.add_argument("goal", nargs="?", default="report the node's runtime health")
    ap.add_argument("--config", help="mesh config (default: $URIRUN_MESH_CONFIG or ~/.urirun-host/mesh.json)")
    ap.add_argument("--node", action="append", help="restrict to node name(s); repeatable")
    ap.add_argument("--model", default=os.getenv("URIRUN_LLM_MODEL", "llama3"))
    ap.add_argument("--base-url", default=os.getenv("URIRUN_LLM_BASE_URL", "http://localhost:11434"))
    ap.add_argument("--max-attempts", type=int, default=3)
    ap.add_argument("--dry-run", action="store_true",
                    help="generate + validate the flow against the node's schemas, but do not execute on the node")
    ap.add_argument("--litellm", action="store_true",
                    help="generate with litellm (OpenRouter/OpenAI/…) instead of the Ollama llm:// connector")
    ap.add_argument("--env-file", help="load KEY=VALUE (e.g. OPENROUTER_API_KEY, LLM_MODEL) before generating")
    args = ap.parse_args(argv)

    if args.env_file:
        _load_env_file(args.env_file)
        args.model = os.getenv("LLM_MODEL", args.model)

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

    # 2) pick the LLM that writes the flow
    if args.litellm:
        ask, llm_registry = litellm_ask, {}
        print(f"llm: litellm model={args.model}")
    else:
        import urirun_connector_llm.core as llm
        ask, llm_registry = repair_flow.ask_llm, llm.conn.registry()
        print(f"llm: llm:// model={args.model} base_url={args.base_url}")

    # 3) generate → forward to node (or dry-run/validate) → repair on failure
    mode = "dry-run" if args.dry_run else "execute"
    print(f"mode: {mode}")
    report = repair_flow.generate_run_repair(
        args.goal, registry, llm_registry, model=args.model, base_url=args.base_url,
        allow=allow, max_attempts=args.max_attempts, ask=ask, runner=make_mesh_runner(mode),
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
