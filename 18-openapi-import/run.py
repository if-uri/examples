#!/usr/bin/env python3
"""Import an OpenAPI spec into URI routes (`urirun add-openapi`) and call one — with
an auth header carried by reference (`secret://`/`getv://`), so the live request
uses the real token but no serialized surface ever prints it.

Run:  pip install urirun pyyaml  &&  PET_TOKEN=demo-key python run.py
"""
from __future__ import annotations

import http.server
import json
import os
import pathlib
import subprocess
import sys
import threading

HERE = pathlib.Path(__file__).resolve().parent

try:
    from urirun import v2, _runtime as rt
except ImportError as exc:  # pragma: no cover
    sys.exit(f"missing dependency ({exc}); run: pip install urirun")

os.environ.setdefault("PET_TOKEN", "demo-key")

# a tiny mock API on an auto-assigned port -----------------------------------
seen: dict = {}


class Mock(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        seen["authorization"] = self.headers.get("Authorization")
        body = json.dumps([{"id": "1", "name": "Rex"}]).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_):
        pass


server = http.server.HTTPServer(("127.0.0.1", 0), Mock)
port = server.server_address[1]
threading.Thread(target=server.serve_forever, daemon=True).start()

# 1) OpenAPI -> declarative fetch routes (base URL pointed at the mock) -------
generated = subprocess.run(
    ["urirun", "add-openapi", str(HERE / "petstore.json"),
     "--scheme", "pet", "--base-url", f"http://127.0.0.1:{port}"],
    capture_output=True, text=True,
)
doc = json.loads(generated.stdout)
print(f"add-openapi -> {len(doc['bindings'])} routes:")
for uri in doc["bindings"]:
    print(f"  {uri}")

# 2) secure GET /pets with a by-reference auth header ------------------------
doc["bindings"]["pet://api/pets/query/get"].setdefault("config", {})["headers"] = {
    "Authorization": "Bearer {getv:PET_TOKEN}",
}

registry = v2.compile_registry(doc)

# 3) run it — the token resolves only here, at the executor boundary ---------
env = rt.run(
    "pet://api/pets/query/get", registry, mode="execute",
    policy={"execute": {"allow": ["pet://*"]}, "secretAllow": ["getv://*"]},
)
result = env.get("result") or {}

print(f"\nrun ok: {env.get('ok')} | status: {result.get('status')}")
print(f"the mock received: {seen.get('authorization')}")
token = os.environ["PET_TOKEN"]
print(f"token in the run envelope:  {token in json.dumps(env)}")
print(f"token in the registry:      {token in json.dumps(registry)}")
print(f"registry keeps the {{getv:..}} reference: {'getv:PET_TOKEN' in json.dumps(registry)}")

server.shutdown()
ok = env.get("ok") and seen.get("authorization") == f"Bearer {token}" \
    and token not in json.dumps(env) and token not in json.dumps(registry)
print("\nimported an API as URI routes; called one with a referenced secret that never serialized"
      if ok else "\nFAILED")
sys.exit(0 if ok else 1)
