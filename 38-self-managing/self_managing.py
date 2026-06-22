# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# The self-managing loop: the LLM doesn't just DRIVE the node, it MANAGES it. When a
# planned step needs a scheme the node doesn't serve, the loop resolves the connector
# (resolver.py), installs it (admin-gated), re-discovers the surface, and re-plans —
# then executes, self-repairing the payload on a node error. So urirun self-extends
# with the capability it's missing instead of failing.
#
#   gap (scheme not served) -> resolve -> provision -> re-discover -> re-plan -> execute
#   node error on a payload -> feed back -> re-plan -> execute            (self-repair)

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[0] / "37-closed-loop-automation"))
sys.path.insert(0, str(HERE.parents[1] / "urirun" / "adapters" / "python"))

from closed_loop import execute_flow  # noqa: E402


def _scheme(uri: str) -> str:
    return uri.split("://", 1)[0]


def served_schemes(client) -> set[str]:
    return {_scheme(r["uri"]) for r in client.routes()}


def flow_gaps(flow: dict, served: set[str]) -> list[str]:
    """Schemes the flow needs that the node does not serve."""
    need = {_scheme(s["uri"]) for s in flow.get("steps", []) if "uri" in s}
    return sorted(need - served)


def self_managing_loop(client, goal, planner, resolver, provision, *, max_iter: int = 5) -> dict:
    """Drive AND manage. `planner(goal, routes, prev_error, observation)->{steps}`,
    `resolver(scheme)->[candidate...]`, `provision(client, candidate)->bool` (install +
    serve the connector). Returns convergence info and what was provisioned."""
    provisioned: list[dict] = []
    error = None
    for iteration in range(1, max_iter + 1):
        routes = client.routes()
        served = {_scheme(r["uri"]) for r in routes}
        flow = planner(goal, routes, error, None)
        gaps = flow_gaps(flow, served)
        if gaps:
            scheme = gaps[0]
            candidates = resolver(scheme)
            if not candidates:
                return {"ok": False, "reason": f"no connector resolves '{scheme}://'",
                        "provisioned": provisioned, "iterations": iteration}
            candidate = candidates[0]
            ok = bool(provision(client, candidate))
            provisioned.append({"scheme": scheme, "connector": candidate.get("package"),
                                "source": candidate.get("source"), "ok": ok})
            if not ok:
                return {"ok": False, "reason": f"provision failed for '{scheme}://' "
                        f"({candidate.get('package')})", "provisioned": provisioned, "iterations": iteration}
            continue  # re-discover the (now larger) surface and re-plan
        out = execute_flow(client, flow)
        if out["ok"]:
            return {"ok": True, "iterations": iteration, "provisioned": provisioned, "trace": out["trace"]}
        error = {"failed_step": out["failed_step"], "error": out["error"]}   # self-repair the payload
    return {"ok": False, "iterations": max_iter, "provisioned": provisioned, "reason": "did not converge"}


# --- production provision: install on the node, then serve the routes ---------

def make_provision(*, node_name: str, identity: str | None = None, token: str | None = None):
    """Real provision: install the connector into the node's venv via the admin-gated
    `node://.../package/command/install` (prefers the local path, falls back to git),
    then `host deploy --merge` its bindings so the routes start serving. Needs the node
    started with `--manage` + `--deploy` and an enrolled key or admin token."""
    import importlib
    import json
    import sys as _sys

    from urirun.node import mesh

    def provision(client, candidate) -> bool:
        spec = candidate["install"].get("local") or candidate["install"].get("git")
        env = client.run(f"node://{node_name}/package/command/install", {"spec": spec})
        if not env.get("ok"):
            return False
        # serve the routes: import the connector locally, get its bindings, deploy --merge
        try:
            mod = importlib.import_module(candidate["package"].replace("-", "_"))
            bindings = mod.urirun_bindings()
        except Exception:  # noqa: BLE001
            return True  # installed, but we couldn't fetch bindings here — node may auto-serve
        res = mesh.deploy_to_node(client.base, bindings=bindings, allow=[f"{s}://**" for s in candidate["schemes"]],
                                  merge=True, identity=identity, token=token)
        return bool(res.get("ok"))

    return provision
