#!/usr/bin/env bash
# Embedded URIRUN layer — the builtin URIs every runtime carries with zero config.
#
# These resolve with NO connector installed and NO registry file. The runtime
# answers them itself:
#
#   registry://  — the runtime describing its own routes and bindings
#   error://     — the runtime's addressable error store
#
# (log:// also exists for runtime logs, but it lives in the host layer and needs
#  host setup, so it is not part of this zero-config demo.)
#
# Requires urirun >= 0.4.4 (registry:// builtin + zero-config run). Override the
# binary with URIRUN=... e.g. URIRUN="python3 -m urirun.v2" ./demo.sh
set -euo pipefail
URIRUN="${URIRUN:-urirun}"

run() { $URIRUN run "$1" --execute --allow "$2" --payload "$3"; }

echo "== 1) registry:// — list every live route (no source, no compile) =="
run 'registry://local/routes/query/list' 'registry://*' '{}' \
  | python3 -c "import json,sys; d=json.load(sys.stdin)['result']; print(f\"   {d['count']} routes across the live runtime\")"

echo "== 2) registry:// — just the embedded builtin layer =="
run 'registry://local/routes/query/list' 'registry://*' '{}' \
  | python3 -c "import json,sys; [print('  ', r['uri'], '->', r['adapter']) for r in json.load(sys.stdin)['result']['routes'] if r['uri'].startswith(('registry://','error://'))]"

echo "== 3) registry:// — inspect one binding's contract =="
run 'registry://local/bindings/query/show' 'registry://*' '{"uri":"registry://local/routes/query/list"}' \
  | python3 -c "import json,sys; b=json.load(sys.stdin)['result']['binding']; print('  ', b['uri'], '| adapter', b['adapter'], '| connector', b['connector'])"

echo "== 4) error:// — query the runtime error store =="
run 'error://local/errors/query' 'error://*' '{}' \
  | python3 -c "import json,sys; d=json.load(sys.stdin)['result']; print('   recorded errors:', len(d.get('errors', [])))"

echo
echo "All four ran with zero configuration — no connector, no registry file."
