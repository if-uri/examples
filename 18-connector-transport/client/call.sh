#!/usr/bin/env bash
# The client side: has urirun but NOT the connector. Drives the connector purely
# over the URI + HTTP contract.
set -euo pipefail
rm -rf /tmp/urirun-contract /tmp/urirun
cp -r /src/urirun-contract /tmp/urirun-contract && cp -r /src/urirun /tmp/urirun
rm -rf /tmp/urirun-contract/{build,dist,*.egg-info} /tmp/urirun/{build,dist,*.egg-info}
pip install --quiet --force-reinstall /tmp/urirun-contract
pip install --quiet "jsonschema>=4.18" "pydantic>=2"
pip install --quiet --force-reinstall --no-deps /tmp/urirun
python - <<'PY'
import json, time, urllib.request
NODE = "http://node:8765"

def get(path):
    return json.load(urllib.request.urlopen(NODE + path, timeout=10))

def run(uri, payload):
    req = urllib.request.Request(NODE + "/run",
        data=json.dumps({"uri": uri, "payload": payload}).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        return json.load(urllib.request.urlopen(req, timeout=25))
    except urllib.error.HTTPError as exc:   # denied routes come back as 400 + envelope
        return json.load(exc)

for _ in range(40):                       # wait for the node to come up
    try:
        health = get("/health"); break
    except Exception:
        time.sleep(1)
else:
    raise SystemExit("node never became healthy")

print("== node /health   ==", health)
routes = get("/routes"); rs = routes.get("routes", routes)
print("== node /routes   ==", len(rs), "connector routes exposed over HTTP")
print("== node /mcp/tools==", len(get("/mcp/tools")["tools"]), "MCP tools (same registry)")

print("\n== drive monitor://host/http/query/status OVER HTTP (no connector on this client) ==")
res = run("monitor://host/http/query/status", {"domain": "target", "url": "http://target/"})
result = res.get("result") or {}
if res.get("ok") and isinstance(result.get("value"), dict):
    out = result["value"]
elif res.get("ok") and "stdout" in result:
    out = json.loads(result["stdout"])
else:
    out = res
print("  ok:", res.get("ok"), "| domain:", out.get("domain"), "| http status:", (out.get("http") or {}).get("status"), "| elapsedMs:", (out.get("http") or {}).get("elapsedMs"))

print("\n== a route outside the node's --allow is refused (transport security boundary) ==")
res2 = run("browser://host/page/command/screenshot", {"url": "http://target/"})
browser_allowed = res2.get("decision", {}).get("allowed")
print("  browser allowed:", browser_allowed, "(blocked: not in node --allow)")
if browser_allowed is not False:
    raise SystemExit(f"browser route should be denied by node --allow, got: {res2}")

print("\nCLIENT DONE — connector invoked across the network with zero local install")
PY
