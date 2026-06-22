#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Build the node's served registry: the tellmesh office/desktop routes (via
# tellmesh_bridge) PLUS a small base surface (env health, node log write/read,
# process list) so the host's both-sides logging keeps working. Writes
# generated/node-office.bindings.json and compiles generated/node-office.registry.json.
#
#   python3 build_node_registry.py --name lenovo

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / "urirun" / "adapters" / "python"))

import tellmesh_bridge  # noqa: E402
from urirun import v2  # noqa: E402


def base_bindings(name: str) -> dict:
    """Dependency-free argv-template routes every node should keep: health, logging,
    processes. The host writes to `log://<name>/session/command/write` on each step so
    the node's own log records what was delegated — visible on both sides."""
    py = "python3"  # resolved on the NODE's PATH (sys.executable would bake the host path)
    logp = f"/tmp/urirun-{name}.log"
    return {
        f"env://{name}/runtime/query/health": {
            "kind": "command", "adapter": "argv-template",
            "inputSchema": {"type": "object", "additionalProperties": False, "properties": {}},
            "argv": [py, "-c",
                     "import json,platform,socket,os;print(json.dumps({'host':socket.gethostname(),'platform':platform.platform(),'cwd':os.getcwd()}))"],
            "policy": {"allowExecute": True, "maxArgs": 8},
            "meta": {"label": "Node runtime health"},
        },
        f"log://{name}/session/command/write": {
            "kind": "command", "adapter": "argv-template",
            "inputSchema": {"type": "object", "additionalProperties": False,
                            "required": ["text"], "properties": {"text": {"type": "string", "minLength": 1}}},
            "argv": [py, "-c",
                     f"import json,pathlib,sys,time;p=pathlib.Path('{logp}');p.open('a').write(json.dumps({{'at':time.time(),'text':sys.argv[1]}})+chr(10));print(json.dumps({{'wrote':sys.argv[1]}}))",
                     "{text}"],
            "policy": {"allowExecute": True, "maxArgs": 8},
            "meta": {"label": "Write local node log entry"},
        },
        f"log://{name}/session/query/recent": {
            "kind": "command", "adapter": "argv-template",
            "inputSchema": {"type": "object", "additionalProperties": False,
                            "properties": {"limit": {"type": "integer", "default": 20, "minimum": 1, "maximum": 200}}},
            "argv": [py, "-c",
                     f"import json,pathlib,sys;p=pathlib.Path('{logp}');print(json.dumps({{'lines':p.read_text().splitlines()[-int(sys.argv[1]):] if p.exists() else []}}))",
                     "{limit}"],
            "policy": {"allowExecute": True, "maxArgs": 8},
            "meta": {"label": "Read local node log entries"},
        },
        f"proc://{name}/process/query/list": {
            "kind": "command", "adapter": "argv-template",
            "inputSchema": {"type": "object", "additionalProperties": False,
                            "properties": {"limit": {"type": "integer", "default": 12, "minimum": 1, "maximum": 50}}},
            "argv": [py, "-c",
                     "import json,subprocess,sys;out=subprocess.run(['ps','-eo','pid,comm,%cpu','--sort=-%cpu'],capture_output=True,text=True).stdout.splitlines()[:int(sys.argv[1])+1];print(json.dumps({'processes':out}))",
                     "{limit}"],
            "policy": {"allowExecute": True, "maxArgs": 8},
            "meta": {"label": "List top local processes"},
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", default="lenovo", help="node name (URI host segment)")
    ap.add_argument("--out-dir", default=str(HERE / "generated"))
    args = ap.parse_args()

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    office = tellmesh_bridge.build_bindings()
    bindings = {**base_bindings(args.name), **office}
    doc = {"version": "urirun.bindings.v2", "bindings": bindings}

    bpath = out / "node-office.bindings.json"
    rpath = out / "node-office.registry.json"
    bpath.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    registry = v2.compile_registry(doc)
    rpath.write_text(json.dumps(registry, indent=2), encoding="utf-8")

    schemes = sorted({u.split("://", 1)[0] for u in bindings})
    print(f"tellmesh dir : {tellmesh_bridge.TELLMESH_DIR}")
    print(f"office routes: {len(office)}  ({len(tellmesh_bridge.ROUTES)} adopted)")
    print(f"base routes  : {len(bindings) - len(office)}")
    print(f"total        : {len(bindings)} routes, schemes: {', '.join(schemes)}")
    print(f"bindings     : {bpath}")
    print(f"registry     : {rpath}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
