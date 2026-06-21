#!/usr/bin/env bash
# Scenario 3: drive httpbin from a declarative TOML spec, chained.
set -euo pipefail
cd "$(dirname "$0")"
urirun connectors from-spec ../15-declarative-http/httpbin.toml | urirun compile - --out httpbin.registry.json
urirun run 'httpbin://default/status/query/code' httpbin.registry.json \
  --payload '{"code":418}' --execute --allow 'httpbin://*'
urirun run 'httpbin://default/echo/command/post' httpbin.registry.json \
  --payload '{"name":"ifuri"}' --execute --allow 'httpbin://*'
