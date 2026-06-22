# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Connector RESOLVER prototype: map a NEEDED capability (a scheme, a route, or an NL
# phrase) to a connector that provides it AND an install spec — across three sources:
#   * local projects under ~/github/*/*           (install spec = the local path, pip -e)
#   * a git org (github.com/if-uri/...)           (install spec = git+https://...)
#   * the hub catalog (connect.ifuri.com)         (install spec = the catalog pip spec)
#
# This is the missing primitive for a SELF-MANAGING urirun: when the LLM plans a route
# no installed connector serves, the loop resolves it here and installs it (admin-gated)
# instead of failing. Local scan is offline; hub/git are best-effort.

from __future__ import annotations

import json
import re
from pathlib import Path


def _schemes_from_manifest(manifest: dict) -> list[str]:
    schemes = set(manifest.get("uriSchemes") or [])
    for route in manifest.get("routes") or []:
        uri = route if isinstance(route, str) else route.get("uri", "")
        if "://" in uri:
            schemes.add(uri.split("://", 1)[0])
    for ex in manifest.get("flowExample") or []:
        if "://" in ex:
            schemes.add(ex.split("://", 1)[0])
    return sorted(schemes)


def _schemes_from_code(pkg_dir: Path) -> list[str]:
    """Fallback: grep the package for scheme="..." in urirun.connector(...) calls."""
    schemes = set()
    for py in pkg_dir.rglob("*.py"):
        if "__pycache__" in py.parts:
            continue
        try:
            txt = py.read_text(encoding="utf-8")
        except OSError:
            continue
        schemes.update(re.findall(r'connector\([^)]*scheme=["\']([a-z0-9_-]+)["\']', txt))
        schemes.update(m.split("://", 1)[0] for m in re.findall(r'["\']([a-z0-9_-]+://[^"\']+)["\']', txt))
    return sorted(s for s in schemes if s and not s.startswith(("http", "git")))


def index_local(roots=("~/github",), git_org="if-uri") -> list[dict]:
    """Scan local projects for urirun connectors. Each entry: id, schemes, source path,
    and both a local (pip -e <path>) and a git install spec."""
    out = []
    seen = set()
    # bounded scan: <root>/urirun-connector-* and <root>/*/urirun-connector-* only
    # (no full recursion — skips node_modules/.git/venv and stays fast).
    for root in roots:
        base = Path(root).expanduser()
        if not base.exists():
            continue
        candidates = list(base.glob("urirun-connector-*")) + list(base.glob("*/urirun-connector-*"))
        for d in sorted(candidates):
            if not d.is_dir() or d.name in seen or "__pycache__" in d.parts or ".git" in d.parts:
                continue
            seen.add(d.name)
            cid = d.name.replace("urirun-connector-", "")
            manifests = list(d.rglob("connector.manifest.json"))
            manifest = {}
            if manifests:
                try:
                    manifest = json.loads(manifests[0].read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    manifest = {}
            schemes = _schemes_from_manifest(manifest) or _schemes_from_code(d)
            out.append({
                "id": cid,
                "package": f"urirun-connector-{cid}",
                "schemes": schemes or [cid.replace("-", "")],
                "source": str(d),
                "install": {
                    "local": str(d),                                   # pip install -e <path>
                    "git": f"git+https://github.com/{git_org}/urirun-connector-{cid}.git",
                    "pypi": f"urirun-connector-{cid}",
                },
                "summary": manifest.get("summary", ""),
            })
    return out


def resolve(capability: str, index: list[dict] | None = None) -> list[dict]:
    """Map a capability to connectors. `capability` may be a scheme ('browser'), a route
    ('browser://node/page/...'), or an NL phrase ('control a browser', 'send email')."""
    idx = index if index is not None else index_local()
    cap = capability.lower().strip()
    scheme = cap.split("://", 1)[0] if "://" in cap else cap
    hits = []
    for c in idx:
        score = 0
        if scheme in c["schemes"]:
            score += 100
        if scheme in c["id"] or c["id"] in cap:
            score += 50
        for word in re.findall(r"[a-z]+", cap):
            if word and (word in c["id"] or word in c["summary"].lower() or word in c["schemes"]):
                score += 5
        if score:
            hits.append({**c, "score": score})
    return sorted(hits, key=lambda c: -c["score"])


if __name__ == "__main__":
    import sys
    idx = index_local()
    if len(sys.argv) > 1:
        for c in resolve(sys.argv[1], idx)[:5]:
            print(f"  [{c['score']:3}] {c['package']:34} schemes={c['schemes']}")
            print(f"        install: -e {c['install']['local']}")
            print(f"             or: {c['install']['git']}")
    else:
        print(f"indexed {len(idx)} local connectors:")
        for c in idx:
            print(f"  {c['package']:36} schemes={c['schemes']}")
