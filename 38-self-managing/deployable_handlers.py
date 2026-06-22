# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# A small catalog of SELF-CONTAINED (stdlib-only) capability handlers that a provision
# step can push onto a node as `--code` + bindings — so a node with no connectors
# installed can still gain a capability over the URI contract. Each entry maps a scheme
# to (module source, bindings-for-a-node). Real connectors (browser-control, email, …)
# install via pip; these cover the pure-stdlib capabilities an autonomous loop reaches
# for most often.

from __future__ import annotations

# module source pushed as <scheme>_handler.py on the node
_UUID = '''
def gen(**p):
    import uuid
    n = max(1, min(int(p.get("count", 1)), 50))
    return {"ok": True, "ids": [str(uuid.uuid4()) for _ in range(n)]}
'''

_HASH = '''
def sha256(**p):
    import hashlib
    return {"ok": True, "sha256": hashlib.sha256(str(p.get("text", "")).encode()).hexdigest()}
'''

_CODEC = '''
def b64(**p):
    import base64
    text, mode = str(p.get("text", "")), p.get("mode", "encode")
    if mode == "decode":
        return {"ok": True, "result": base64.b64decode(text).decode("utf-8", "replace")}
    return {"ok": True, "result": base64.b64encode(text.encode()).decode()}
'''


def _binding(uri, module, export, props):
    return {uri: {"kind": "query", "adapter": "local-function", "ref": f"{module}:{export}",
                  "python": {"type": "python", "module": module, "export": export},
                  "inputSchema": {"type": "object", "properties": props}, "uri": uri}}


def for_scheme(scheme: str, node: str = "host") -> dict | None:
    """Return {code:{file:src}, bindings:{...}, schemes:[...]} for a stdlib capability,
    templated on the node name, or None if there's no self-contained handler for it."""
    if scheme == "uuid":
        mod = "uuid_handler"
        return {"code": {f"{mod}.py": _UUID}, "schemes": ["uuid"],
                "bindings": {"version": "urirun.bindings.v2",
                             "bindings": _binding(f"uuid://{node}/id/query/v4", mod, "gen",
                                                  {"count": {"type": "integer"}})}}
    if scheme == "hash":
        mod = "hash_handler"
        return {"code": {f"{mod}.py": _HASH}, "schemes": ["hash"],
                "bindings": {"version": "urirun.bindings.v2",
                             "bindings": _binding(f"hash://{node}/text/query/sha256", mod, "sha256",
                                                  {"text": {"type": "string"}})}}
    if scheme == "codec":
        mod = "codec_handler"
        return {"code": {f"{mod}.py": _CODEC}, "schemes": ["codec"],
                "bindings": {"version": "urirun.bindings.v2",
                             "bindings": _binding(f"codec://{node}/text/query/base64", mod, "b64",
                                                  {"text": {"type": "string"}, "mode": {"type": "string"}})}}
    return None


SELF_CONTAINED_SCHEMES = ("uuid", "hash", "codec")
