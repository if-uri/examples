#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Bridge the REAL tellmesh handlers (`handler(payload, context)`) onto urirun's
# local-function adapter (`fn(**payload)`), so a urirun node can serve the whole
# office/desktop URI surface — him (mouse/keyboard), kvm, browser, urioffice,
# screen, shell — and execute it in-process.
#
# urirun's adopt-pack maps a manifest's `python://module:func` to a handler that is
# called as `func(**payload)`. tellmesh handlers instead take `(payload, context)`
# with a *persistent* context (holds mock state, config, and the `allow_real` flag).
# This module reads each manifest, imports the real handler, and exposes a wrapper
# named `h_<operation>` that forwards `(payload, CONTEXT)`. `build_bindings()` then
# emits a urirun.bindings.v2 document pointing every route at its wrapper.
#
# Set URISYS_ALLOW_REAL=1 on the node to drive the real machine (xdotool/ydotool,
# a real browser, LibreOffice); unset, every handler runs in safe mock mode.

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path
from typing import Any, Callable

import yaml

# --- where the tellmesh monorepo lives, and which packs to expose ----------------
TELLMESH_DIR = Path(
    os.environ.get("TELLMESH_DIR", Path(__file__).resolve().parents[3] / "tellmesh")
).resolve()

# manifest (relative to TELLMESH_DIR) -> the source dir to put on sys.path for it.
PACKS: list[str] = [
    "urihim/urihim/manifest.yaml",
    "urikvm/urikvm/manifest.yaml",
    "uribrowser/uribrowserdocker/manifest.yaml",
    "urioffice/urioffice/manifest.yaml",
    "uriscreen/uriscreen/manifest.yaml",
    "urishell/urishell/manifest.yaml",
]

# Persistent execution context shared across every dispatched route on this node.
# tellmesh handlers stash mock state here and read `allow_real` / `config` from it.
CONTEXT: dict[str, Any] = {
    "state": {},
    "config": {},
    "allow_real": os.environ.get("URISYS_ALLOW_REAL") == "1",
}

# Minimal input schemas per operation so the LLM planner on the host can fill
# parameters from the action space (urirun exposes inputSchema in /routes).
_SCHEMA: dict[str, dict] = {
    "him.mouse.move": {"x": {"type": "integer"}, "y": {"type": "integer"}},
    "him.mouse.click": {
        "x": {"type": "integer"}, "y": {"type": "integer"},
        "button": {"type": "string", "enum": ["left", "right", "middle"]},
        "clicks": {"type": "integer"},
    },
    "him.mouse.scroll": {"amount": {"type": "integer"}},
    "him.keyboard.type": {"text": {"type": "string"}},
    "him.keyboard.type_text": {"text": {"type": "string"}},
    "him.keyboard.hotkey": {"keys": {"type": "array", "items": {"type": "string"}}},
    "him.keyboard.key": {"key": {"type": "string"}},
    "kvm.task.click_text": {"text": {"type": "string"}},
    "kvm.task.type_text": {"text": {"type": "string"}},
    "browser.page.open": {"url": {"type": "string"}},
    "browser.form.submit": {
        "form_id": {"type": "string"},
        "fields": {"type": "object", "additionalProperties": {"type": "string"}},
    },
    "browser.social.publish_post": {
        "platform": {"type": "string"}, "text": {"type": "string"},
    },
    "office.document.open": {"path": {"type": "string"}, "title": {"type": "string"}},
    "office.document.save": {"path": {"type": "string"}, "content": {"type": "string"}},
    "office.document.export_pdf": {"path": {"type": "string"}},
    "office.writer.render": {
        "text": {"type": "string"}, "title": {"type": "string"},
        "format": {"type": "string", "enum": ["txt", "pdf", "html"]},
    },
    "shell.run": {
        "command": {"type": "string"},
        "args": {"type": "array", "items": {"type": "string"}},
    },
    "screen.frame": {"monitor": {"type": "integer"}, "backend": {"type": "string"}},
    "screen.capture": {"monitor": {"type": "integer"}, "output": {"type": "string"}},
}


def _ensure_paths() -> None:
    """Put each pack's source dir + the uri_control core on sys.path so the handlers
    import straight from a tellmesh checkout — no pip install needed on the node."""
    extra = [str(TELLMESH_DIR / "uricontrol" / "core" / "python")]  # provides uri_control
    extra += [str((TELLMESH_DIR / rel).parents[1]) for rel in PACKS]  # urihim, urikvm, …
    for p in extra:
        if p not in sys.path and Path(p).is_dir():
            sys.path.insert(0, p)


def _manifest_routes() -> list[dict]:
    """Parse every manifest into route descriptors — WITHOUT importing the handlers, so
    a host can build bindings even without the tellmesh runtime deps installed. The
    actual handler import is deferred to `__getattr__` on the node (see below)."""
    routes: list[dict] = []
    for rel in PACKS:
        manifest = TELLMESH_DIR / rel
        if not manifest.exists():
            continue
        doc = yaml.safe_load(manifest.read_text(encoding="utf-8"))
        scheme = doc.get("scheme", "")
        handlers = (doc.get("handlers", {}) or {}).get("python", {}) or {}
        for pat in doc.get("uri_patterns", []):
            op = pat["operation"]
            ref = handlers.get(op)
            if not ref:
                continue
            routes.append(
                {"uri": pat["pattern"], "kind": pat.get("kind", "command"),
                 "operation": op, "scheme": scheme,
                 "ref": ref.replace("python://", ""), "export": "h_" + op.replace(".", "_")}
            )
    return routes


ROUTES: list[dict] = _manifest_routes()
_BY_EXPORT: dict[str, dict] = {r["export"]: r for r in ROUTES}


def __getattr__(name: str) -> Callable:
    """PEP 562: resolve `h_<operation>` to a wrapper. The real tellmesh handler is
    imported INSIDE the wrapper (at call time), not here — so a missing dependency
    surfaces as a normal exception urirun can catch and report, instead of raising
    during attribute resolution (which would kill the request). Building bindings never
    triggers an import; only an actual call does."""
    route = _BY_EXPORT.get(name)
    if route is None:
        raise AttributeError(name)
    mod_name, _, func_name = route["ref"].partition(":")

    def handler(**payload: Any) -> Any:
        _ensure_paths()
        fn = getattr(importlib.import_module(mod_name), func_name)
        return fn(payload, CONTEXT)

    globals()[name] = handler  # cache so urirun's re-import path finds it directly
    return handler


def _input_schema(op: str) -> dict:
    props = _SCHEMA.get(op, {})
    return {"type": "object", "additionalProperties": True, "properties": props}


def build_bindings() -> dict:
    """Emit a urirun.bindings.v2 document for every adopted office/desktop route."""
    bindings: dict[str, dict] = {}
    for r in ROUTES:
        bindings[r["uri"]] = {
            "kind": r["kind"],
            "adapter": "local-function",
            "ref": f"tellmesh_bridge:{r['export']}",
            "python": {"type": "python", "module": "tellmesh_bridge", "export": r["export"]},
            "inputSchema": _input_schema(r["operation"]),
            "policy": {"allowExecute": True},
            "meta": {"label": f"{r['scheme']} · {r['operation']}",
                     "tellmesh": r["operation"]},
        }
    return bindings


if __name__ == "__main__":
    import json

    print(json.dumps({"tellmesh_dir": str(TELLMESH_DIR),
                      "routes": len(ROUTES),
                      "allow_real": CONTEXT["allow_real"],
                      "uris": [r["uri"] for r in ROUTES]}, indent=2))
