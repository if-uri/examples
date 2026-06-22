#!/usr/bin/env bash
# Local proof (no docker): the SAME shop:// URIs reach existing Python, Node and
# shell code, and the SAME registry projects to CLI / HTTP / MCP / A2A.
#
# Requires urirun >= 0.4.4, python3, node, bash. Override: URIRUN="python3 -m urirun.v2"
set -euo pipefail
cd "$(dirname "$0")"
URIRUN="${URIRUN:-urirun}"
MCP="${MCP:-urirun-v2-mcp}"

echo "== adopt: validate + compile existing code into a registry =="
$URIRUN validate shop.bindings.json
$URIRUN compile shop.bindings.json --out shop.registry.json >/dev/null
$URIRUN list shop.registry.json

run() { $URIRUN run "$1" shop.registry.json --execute --allow 'shop://*' --payload "$2"; }
field() { python3 -c "import json,sys; print(json.loads(json.load(sys.stdin)['result']['stdout']))"; }

echo; echo "== same URI surface, three runtimes =="
echo -n "  python  "; run 'shop://inventory/stock/query/check'    '{"sku":"sku-1"}'            | field
echo -n "  python  "; run 'shop://inventory/stock/command/reserve' '{"sku":"sku-1","qty":3}'  | field
echo -n "  nodejs  "; run 'shop://notify/email/command/send'      '{"to":"a@b.com","msg":"hi"}' | field
echo -n "  shell   "; run 'shop://report/sales/query/daily'       '{"date":"2026-06-22"}'      | field

echo; echo "== same registry, agent layers =="
echo -n "  MCP tools: "; $MCP tools shop.registry.json | python3 -c "import json,sys;print([t['name'] for t in json.load(sys.stdin)['tools']])"
echo -n "  A2A skills: "; $MCP card shop.registry.json --name shop --url http://gateway:8080/ | python3 -c "import json,sys;print(len(json.load(sys.stdin)['skills']))"

rm -f shop.registry.json
echo; echo "OK — existing code adopted; one URI surface across runtimes and layers."
