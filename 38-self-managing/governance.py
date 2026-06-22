# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Governance for autonomous connector install — so a self-managing loop is safe by
# default. Installing code on a node is RCE-class, so before any provision runs we:
#   1. check the install SOURCE against a trusted allowlist (else pause for approval),
#   2. VERIFY the connector (connectors verify — every handler resolves) before serving,
#   3. AUDIT the decision (source, spec, verdict) — for the log / SSE stream.
#
# `governed_provision(install_fn, ...)` wraps any provision (e.g. self_managing.make_
# provision) with these gates and returns a drop-in provision for self_managing_loop.

from __future__ import annotations

from pathlib import Path

# Trusted by default: the official hub, the if-uri GitHub org, and your local if-uri
# checkouts. Anything else is "untrusted" and needs explicit approval.
DEFAULT_ALLOWLIST = (
    "connect.ifuri.com",
    "github.com/if-uri/",
    str(Path.home() / "github" / "if-uri"),
)


def source_of(candidate: dict) -> str:
    """The concrete place a connector would be installed from."""
    inst = candidate.get("install", {}) or {}
    return inst.get("local") or inst.get("git") or inst.get("pypi") or candidate.get("source", "")


def is_trusted(candidate: dict, allowlist=DEFAULT_ALLOWLIST) -> bool:
    src = source_of(candidate)
    return bool(src) and any(t in src for t in allowlist)


def governed_provision(install_fn, *, allowlist=DEFAULT_ALLOWLIST, verify_fn=None, approve=None, audit=None):
    """Wrap a provision with governance. `install_fn(client, candidate)->bool` does the
    real install+serve; `verify_fn(candidate)->bool` is the pre-serve gate (e.g.
    `connectors verify`); `approve(candidate)->bool` is consulted for an untrusted
    source (default: deny); `audit(record)` receives each decision."""

    def _audit(candidate, decision, ok):
        if audit is not None:
            audit({"connector": candidate.get("package"), "source": source_of(candidate),
                   "schemes": candidate.get("schemes"), "decision": decision, "ok": bool(ok)})

    def provision(client, candidate):
        if not is_trusted(candidate, allowlist):
            if approve is None or not approve(candidate):
                _audit(candidate, "blocked: source not on allowlist (no approval)", False)
                return False
            _audit(candidate, "approved: untrusted source allowed by human", True)
        if verify_fn is not None and not verify_fn(candidate):
            _audit(candidate, "blocked: connectors verify failed", False)
            return False
        ok = bool(install_fn(client, candidate))
        _audit(candidate, "installed" if ok else "install failed", ok)
        return ok

    return provision


def make_verify_fn():
    """A pre-serve gate that runs `connectors verify` on a candidate's local source
    (when present). A connector that advertises a route it can't run never serves."""
    from urirun.connectors.connector_lint import verify_connector

    def verify_fn(candidate):
        local = (candidate.get("install") or {}).get("local")
        if not local or not Path(local).exists():
            return True   # no local source to check here; node-side verify still applies
        return bool(verify_connector(local).get("ok"))

    return verify_fn
