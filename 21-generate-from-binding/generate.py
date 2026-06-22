#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Generate transport/runtime artifacts FROM a URI scheme binding spec.
#
# The binding (uri + JSON-Schema inputSchema + kind + adapter) is the single
# source of truth. From it we generate, deterministically:
#   * protobuf + gRPC service   (one rpc per route, typed messages from the schema)
#   * an OpenAPI 3 document      (one path per route, requestBody from the schema)
#   * a typed Python client      (one function per route)
# Add a target = add a generator, never re-spec. This is the N×M → N+M move.

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "urirun" / "adapters" / "python"))

import urirun
from urirun import _registry as reglib

PROTO_TYPES = {"string": "string", "integer": "int64", "number": "double", "boolean": "bool"}
OPENAPI_TYPES = {"string", "integer", "number", "boolean", "array", "object"}


def pascal(uri: str) -> str:
    return "".join(p.capitalize() for p in re.split(r"[^a-zA-Z0-9]+", uri) if p)


def routes(registry: dict):
    for item in reglib.flatten_registry_document(registry):
        e = item["routeEntry"]
        schema = (e.get("config") or {}).get("inputSchema") or e.get("inputSchema") or {"type": "object"}
        yield {"uri": item["uri"], "name": pascal(item["uri"]), "kind": e.get("kind"),
               "props": schema.get("properties") or {}, "required": schema.get("required") or []}


# --- protobuf + gRPC -------------------------------------------------------
def gen_proto(rs, package="urirun") -> str:
    out = ['syntax = "proto3";', f"package {package};", "",
           "// One rpc per URI route; request fields are the route's inputSchema.",
           "message RunResult { bool ok = 1; string json = 2; }", ""]
    for r in rs:
        out.append(f"message {r['name']}Request {{")
        for i, (field, spec) in enumerate(r["props"].items(), start=1):
            ptype = PROTO_TYPES.get((spec or {}).get("type"), "string")
            if (spec or {}).get("type") == "array":
                ptype = "repeated string"
            out.append(f"  {ptype} {field} = {i};")
        out.append("}")
        out.append("")
    out.append("service UriService {")
    for r in rs:
        out.append(f"  // {r['uri']}")
        out.append(f"  rpc {r['name']}({r['name']}Request) returns (RunResult);")
    out.append("}")
    return "\n".join(out) + "\n"


# --- OpenAPI 3 -------------------------------------------------------------
def gen_openapi(rs, title="urirun routes") -> dict:
    paths = {}
    for r in rs:
        props = {f: {"type": (s or {}).get("type", "string")} for f, s in r["props"].items()}
        schema = {"type": "object", "properties": props}
        if r["required"]:
            schema["required"] = r["required"]
        paths["/run/" + r["uri"].replace("://", "/")] = {
            "post": {
                "summary": r["uri"], "operationId": r["name"][0].lower() + r["name"][1:],
                "x-uri": r["uri"], "x-kind": r["kind"],
                "requestBody": {"required": bool(r["required"]),
                                "content": {"application/json": {"schema": schema}}},
                "responses": {"200": {"description": "run envelope",
                                      "content": {"application/json": {"schema": {"type": "object"}}}}},
            }
        }
    return {"openapi": "3.0.3", "info": {"title": title, "version": "1.0.0"}, "paths": paths}


# --- typed Python client ---------------------------------------------------
def gen_client(rs) -> str:
    out = ['# generated from the binding spec — one function per route',
           "import urirun", "",
           "def _run(registry, uri, payload, allow):",
           "    policy = urirun.policy(allow=[allow])",
           "    return urirun.run(uri, registry, payload, mode='execute', policy=policy)", ""]
    for r in rs:
        args = ", ".join(f"{f}=None" for f in r["props"])
        body = "{" + ", ".join(f'"{f}": {f}' for f in r["props"]) + "}"
        scheme = r["uri"].split("://", 1)[0]
        fn = re.sub(r"[^a-z0-9]+", "_", r["uri"].lower()).strip("_")
        out += [f"def {fn}(registry, {args}):",
                f'    """{r["uri"]}"""',
                f'    return _run(registry, {r["uri"]!r}, {{k: v for k, v in {body}.items() if v is not None}}, {scheme + "://*"!r})',
                ""]
    return "\n".join(out)


def main() -> int:
    # build a registry from a connector (domain-monitor: 8 typed routes)
    sys.path.insert(0, str(ROOT / "urirun-connector-domain-monitor"))
    import urirun_connector_domain_monitor as conn
    registry = urirun.compile_registry(conn.urirun_bindings())
    rs = list(routes(registry))

    out_dir = HERE / "generated"
    out_dir.mkdir(exist_ok=True)
    (out_dir / "service.proto").write_text(gen_proto(rs))
    (out_dir / "openapi.json").write_text(json.dumps(gen_openapi(rs), indent=2) + "\n")
    (out_dir / "client.py").write_text(gen_client(rs))

    print(f"from 1 binding spec ({len(rs)} routes) generated:")
    print(f"  generated/service.proto   — protobuf + gRPC ({len(rs)} rpc, "
          f"{sum(len(r['props']) for r in rs)} typed fields)")
    print(f"  generated/openapi.json    — OpenAPI 3 ({len(rs)} paths)")
    print(f"  generated/client.py       — typed Python client ({len(rs)} functions)")
    print("\n--- service.proto (excerpt) ---")
    print("\n".join(gen_proto(rs).splitlines()[:16]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
