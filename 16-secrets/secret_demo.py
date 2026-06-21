#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# secret:// end-to-end: a URI carries a *reference* to a credential; the value is
# resolved only in --execute, behind a deny-by-default policy, injected into the
# request header at the executor boundary, and redacted (****) everywhere else.
#
# A tiny local server validates the Bearer token WITHOUT echoing it, so the demo
# proves both injection (auth works) and non-leak (the token never appears in the
# registry, plan or result). Runs anywhere, no network.

from __future__ import annotations

import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import urirun
from urirun.connectors import declarative
from urirun.runtime import _runtime

EXPECTED = "sk-SECRET-do-not-leak-1234"


def start_server() -> ThreadingHTTPServer:
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            auth = self.headers.get("Authorization", "")
            valid = auth == f"Bearer {EXPECTED}"
            self.rfile.read(int(self.headers.get("Content-Length") or 0))
            body = json.dumps({"ok": True, "authValid": valid}).encode()  # never echoes the token
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *a):
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def build(base_url: str):
    spec = {
        "connector": "secret-demo", "scheme": "sdemo",
        "environments": {"local": base_url},
        "routes": [{
            "uri": "sdemo://local/auth/command/call", "method": "POST", "path": "/auth",
            "headers": {"Authorization": "Bearer {getv:DEMO_TOKEN}"},
        }],
    }
    bindings = declarative.bindings_from_spec(spec)
    return bindings, urirun.compile_registry(bindings)


def run(registry, *, mode, secret_allow):
    policy = _runtime.build_policy(None, ["sdemo://*"], None, secret_allow)
    return urirun.run("sdemo://local/auth/command/call", registry, {}, mode=mode, policy=policy)


def scenarios():
    """Return the four scenario outcomes (used by both the CLI demo and the test)."""
    os.environ["DEMO_TOKEN"] = EXPECTED
    server = start_server()
    try:
        base = f"http://127.0.0.1:{server.server_address[1]}"
        bindings, registry = build(base)
        registry_text = json.dumps(bindings) + json.dumps(registry)

        dry = run(registry, mode="dry-run", secret_allow=["getv://DEMO_TOKEN"])
        denied = run(registry, mode="execute", secret_allow=None)            # no allow -> deny-by-default
        allowed = run(registry, mode="execute", secret_allow=["getv://DEMO_TOKEN"])

        return {
            "referenceOnly": EXPECTED not in registry_text,
            "dryRunNoExec": dry.get("mode") == "dry-run" and EXPECTED not in json.dumps(dry),
            "deniedWithoutAllow": not denied.get("ok"),
            "executedWithAllow": bool(allowed.get("ok")),
            "authValid": (allowed.get("result") or {}).get("body", "").find('"authValid": true') >= 0,
            "noLeakInResult": EXPECTED not in json.dumps(allowed),
        }
    finally:
        server.shutdown()


def main() -> int:
    r = scenarios()
    print("secret:// demo")
    print(f"  registry holds only the reference (no value)   : {r['referenceOnly']}")
    print(f"  dry-run does not resolve / leak the secret      : {r['dryRunNoExec']}")
    print(f"  execute WITHOUT --secret-allow is denied        : {r['deniedWithoutAllow']}")
    print(f"  execute WITH --secret-allow runs, auth valid    : {r['executedWithAllow']} / {r['authValid']}")
    print(f"  the token never appears in the result           : {r['noLeakInResult']}")
    ok = all(r.values())
    print(f"\n{'ALL INVARIANTS HOLD' if ok else 'FAILED'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
