#!/usr/bin/env bash
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

set -euo pipefail

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

python3 - <<'PY'
import json
import urllib.request

checks = [
    ("https://ifuri.com/", "text/html"),
    ("https://get.ifuri.com/node.sh", "text/"),
    ("https://connect.ifuri.com/connectors.json", "application/json"),
    ("https://connect.ifuri.com/registry.json", "application/json"),
]
for url, expected in checks:
    with urllib.request.urlopen(url, timeout=25) as response:
        body = response.read().decode("utf-8", errors="replace")
        content_type = response.headers.get("content-type", "")
    assert response.status == 200, (url, response.status)
    assert expected in content_type, (url, content_type)
    if url.endswith(".json"):
        json.loads(body)
    if url == "https://ifuri.com/":
        assert "ifuri" in body.lower(), "ifuri.com page does not contain ifuri"
print("public endpoint smoke OK")
PY

curl -fsSL https://get.ifuri.com/node.sh -o "$tmp/node.sh"
bash -n "$tmp/node.sh"

curl -fsSL 'https://connect.ifuri.com/install?connectors=planfile' -o "$tmp/connect-install.sh"
bash -n "$tmp/connect-install.sh"
# The hub installs the planfile connector (pip version pin or git pip-spec —
# accept either so a connector version bump on the live hub doesn't break smoke).
grep -qE "urirun-connector-planfile|planfile>=" "$tmp/connect-install.sh"

echo "public smoke OK"
