#!/usr/bin/env python3
"""Test that every vendored capability pack adopts, validates and dispatches
through urirun. Mirrors the ecosystem-wide adopt-pack matrix on the 4 packs that
this example bundles, so it runs self-contained in CI.

Run:  pip install urirun pyyaml  &&  python test_packs.py
"""
from __future__ import annotations

import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent

from urirun.runtime import adopt_pack
from urirun import v2, _registry as reg, _runtime as rt

failures = []
for manifest in sorted((HERE / "packs").glob("*.yaml")):
    man = adopt_pack._load(manifest)
    scheme = man.get("scheme")
    doc = adopt_pack.adopt_document(manifest)          # 1. adopt manifest -> bindings.v2
    registry = v2.compile_registry(doc)                # 2. compile + validate structure
    refs = {b["ref"]: (lambda t, a, p, d: {"ok": True})
            for b in doc["bindings"].values() if b.get("ref")}
    hydrated = reg.hydrate_registry(registry, refs)
    for uri in doc["bindings"]:                        # 3. dispatch every route
        concrete = uri.replace("{host}", "host")       # authority only; mid-path {param} stays literal
        env = rt.run(concrete, hydrated, mode="execute", policy={"execute": {"allow": [f"{scheme}://*"]}})
        if not env.get("ok"):
            failures.append(f"{manifest.name} {uri}: {(env.get('error') or {}).get('message')}")
    print(f"ok  {manifest.stem:<10} {scheme}://  {len(doc['bindings'])} routes adopted, validated, dispatched")

if failures:
    print("\nFAILURES:")
    for f in failures:
        print(" ", f)
    sys.exit(1)
print("\nall vendored packs adopt + validate + dispatch through urirun")
