# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Self-contained CI for adopting tellmesh-style capability packs into urirun.
# Uses the bundled manifests/ (no tellmesh checkout needed), so it proves the
# manifest -> bindings -> validate -> compile -> dispatch path offline.
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "urirun" / "adapters" / "python"))

from urirun import v2  # noqa: E402
from urirun.runtime import adopt_pack  # noqa: E402

MANIFESTS = HERE / "manifests"


def test_adopt_maps_manifest_1to1_to_bindings():
    doc = adopt_pack.adopt(str(MANIFESTS / "uriocr.manifest.yaml"))
    uris = list(doc["bindings"])
    assert len(uris) == 2                                   # two uri_patterns -> two routes
    assert all(u.startswith("ocr://") for u in uris)
    assert any(u.endswith("/query/text") for u in uris)
    res = v2.validate_binding_document(doc)
    assert res["ok"], res                                   # adopted bindings are valid


def test_adopted_route_dispatches_dry_run():
    doc = adopt_pack.adopt(str(MANIFESTS / "uriocr.manifest.yaml"))
    registry = v2.compile_registry(doc)
    env = v2.run("ocr://host1/image/latest/query/text", registry, payload={}, mode="dry-run")
    assert env["ok"] is True                                # the registry resolves the route
    assert env["adapter"] == "local-function"               # manifest handler -> local-function


def test_flat_uri_pattern_is_rejected_nuance():
    # A flat URI (`demo://{thing}`) lacks resource+operation segments; urirun rejects
    # it. Adoption surfaces this as a validation error rather than silently shipping a
    # broken route — the fix belongs in the manifest. (This is the shape urishell used
    # to ship; it is now shell://{host}/process/command/run upstream.)
    doc = adopt_pack.adopt(str(MANIFESTS / "flat-uri-bad.manifest.yaml"))
    res = v2.validate_binding_document(doc)
    assert res["ok"] is False
    assert any("resource and operation" in e["error"] for e in res["errors"])
