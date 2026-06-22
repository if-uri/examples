#!/usr/bin/env python3
"""Build the `uri_tree` YAML (scheme -> host -> path -> {uri}) for a selection of
connectors, straight from the connect.ifuri.com catalog — the same selection the
one-line installer takes:

  curl -fsSL 'https://connect.ifuri.com/install?connectors=planfile,sqlite-context,…' | bash

Usage:  python build_uri_tree.py planfile sqlite-context …   (default: the 8 below)
"""
import json, re, sys, urllib.request, pathlib

DEFAULT = ["planfile", "sqlite-context", "domain-monitor", "http-check",
           "time-tools", "namecheap-dns", "grpc-transport", "browser-control"]
CATALOG = "https://connect.ifuri.com/connectors.json"
LOCAL = pathlib.Path(__file__).resolve().parents[2] / "connect.ifuri.com/data/connectors.json"


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def catalog() -> list[dict]:
    try:
        data = json.loads(urllib.request.urlopen(CATALOG, timeout=8).read())
    except Exception:
        data = json.loads(LOCAL.read_text())  # offline fallback to the repo
    c = data.get("connectors", data)
    return c if isinstance(c, list) else list(c.values())


def schemes_tree(uris: list[str]) -> dict:
    """The scheme->host->path->{uri} tree. Dogfoods urirun's built-in
    `urirun.runtime.tree.uri_tree` when urirun is installed, with a local fallback
    so the example also runs standalone."""
    try:
        from urirun.runtime.tree import uri_tree
        return uri_tree(uris)
    except ImportError:
        tree: dict = {}
        for uri in sorted(set(uris)):
            scheme, rest = uri.split("://", 1)
            parts = rest.split("/")
            node = tree.setdefault(scheme, {})
            for seg in parts[:-1]:
                node = node.setdefault(seg, {})
            node[parts[-1]] = {"uri": uri}
        return tree


def build(ids: list[str]) -> dict:
    by_id = {c["id"]: c for c in catalog()}
    tree: dict = {}
    for cid in ids:
        c = by_id.get(cid)
        if not c:
            print(f"# skip unknown connector: {cid}", file=sys.stderr)
            continue
        entry = {
            "status": c.get("status"),
            "verified": c.get("provenance") == "verified",
            "category": c.get("category"),
            "description": c.get("summary") or c.get("description", "")[:120],
            "schemes": schemes_tree(c.get("routes", [])),
        }
        tree[slug(c.get("name", cid))] = entry
    return {"uri_tree": tree}


if __name__ == "__main__":
    import yaml
    ids = sys.argv[1:] or DEFAULT
    print(yaml.safe_dump(build(ids), sort_keys=False, allow_unicode=True, default_flow_style=False))
