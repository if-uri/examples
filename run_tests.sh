#!/usr/bin/env bash
# Run the host-runnable checks for every NN-* example.
# Docker-only demos (08-multi_transport, 11-novnc_lan_flow, the full
# 09-docker_uri_flow compose flow and the full 12 E2E flow) are skipped with a
# note.
set -u
cd "$(dirname "$0")"

# Pick a Python that has `urirun` installed. Override with PYTHON=...
pick_python() {
  for p in "${PYTHON:-}" ../app/.venv/bin/python .venv/bin/python python3 python; do
    [ -n "$p" ] || continue
    if "$p" -c "import urirun" >/dev/null 2>&1; then echo "$p"; return 0; fi
  done
  return 1
}
PY="$(pick_python)" || { echo "ERROR: no Python with 'urirun' found. Install: pip install 'git+https://github.com/tellmesh/urirun.git@v0.3.13#subdirectory=adapters/python'"; exit 2; }
# Make a path-based interpreter absolute so it survives `cd` into example dirs.
case "$PY" in */*) PY="$(cd "$(dirname "$PY")" && pwd)/$(basename "$PY")";; esac
echo "Using Python: $PY ($("$PY" -c 'import urirun,sys;print("urirun",getattr(urirun,"__version__","?"))' 2>/dev/null))"
HAVE_NODE=0; command -v node >/dev/null 2>&1 && HAVE_NODE=1
HAVE_PHP=0;  command -v php  >/dev/null 2>&1 && HAVE_PHP=1
HAVE_TSC=0;  command -v tsc  >/dev/null 2>&1 && HAVE_TSC=1
HAVE_GO=0;   command -v go   >/dev/null 2>&1 && HAVE_GO=1
HAVE_GCC=0;  command -v gcc  >/dev/null 2>&1 && HAVE_GCC=1

PASS=0; FAIL=0; SKIP=0; FAILED=()
run() { # name, command
  printf '  %-40s ' "$1"
  if ( eval "$2" ) >/tmp/ex_$$.log 2>&1; then echo "PASS"; PASS=$((PASS+1));
  else echo "FAIL"; FAIL=$((FAIL+1)); FAILED+=("$1"); sed 's/^/      /' /tmp/ex_$$.log | tail -6; fi
}
skip() { printf '  %-40s SKIP (%s)\n' "$1" "$2"; SKIP=$((SKIP+1)); }

echo "== 01-json =="
run "01-json validate"            "$PY -m urirun.v2 validate 01-json/bindings.v2.example.json"
echo "== 02-decorators =="
run "02-decorators example.py"    "cd 02-decorators && $PY example.py"
echo "== 03-artifacts =="
run "03-artifacts scan"           "$PY -m urirun.v2 scan 03-artifacts --out /tmp/art_$$.json"
echo "== 04-python =="
run "04-python pytest"            "cd 04-python && $PY -m pytest -q ."
echo "== 05-generators =="
if [ "$HAVE_NODE" = 1 ]; then
  run "05-generators js"          "cd 05-generators && node js/example.mjs > /tmp/gen_js_$$.json && $PY -m urirun.v2 validate /tmp/gen_js_$$.json"
  run "05-generators nodejs"      "cd 05-generators && node nodejs/generate-bindings.mjs /tmp/gen_node_$$.json && $PY -m urirun.v2 validate /tmp/gen_node_$$.json"
else skip "05-generators js/nodejs" "no node"; fi
if [ "$HAVE_TSC" = 1 ] && [ "$HAVE_NODE" = 1 ]; then
  run "05-generators ts"          "cd 05-generators && rm -rf /tmp/gen_ts_$$ && tsc --target ES2022 --module ES2022 --outDir /tmp/gen_ts_$$ ts/decorators.ts && node /tmp/gen_ts_$$/decorators.js > /tmp/gen_ts_$$.json && $PY -m urirun.v2 validate /tmp/gen_ts_$$.json"
else skip "05-generators ts" "no tsc/node"; fi
if [ "$HAVE_PHP" = 1 ]; then
  run "05-generators php"         "cd 05-generators && php php/example.php > /tmp/gen_php_$$.json && $PY -m urirun.v2 validate /tmp/gen_php_$$.json"
else skip "05-generators php" "no php"; fi
if [ "$HAVE_GO" = 1 ]; then
  run "05-generators go"          "cd 05-generators && go run go/example.go > /tmp/gen_go_$$.json && $PY -m urirun.v2 validate /tmp/gen_go_$$.json"
else skip "05-generators go" "no go"; fi
if [ "$HAVE_GCC" = 1 ]; then
  run "05-generators c"           "cd 05-generators && gcc c/example.c -o /tmp/gen_c_$$ && /tmp/gen_c_$$ > /tmp/gen_c_$$.json && $PY -m urirun.v2 validate /tmp/gen_c_$$.json"
else skip "05-generators c" "no gcc"; fi
echo "== 06-html_uri_app =="
if [ "$HAVE_NODE" = 1 ]; then run "06-html_uri_app test.mjs" "cd 06-html_uri_app && node test.mjs"
else skip "06-html_uri_app test.mjs" "no node"; fi
echo "== 07-transports =="
run "07-transports test"          "cd 07-transports && $PY test_transports.py"
run "07-transports demo"          "cd 07-transports && $PY demo.py"
echo "== 08-multi_transport =="
skip "08-multi_transport" "needs Docker"
echo "== 09-docker_uri_flow (host) =="
run "09 service_adapter"          "cd 09-docker_uri_flow && $PY test_service_adapter.py"
run "09 flow_runner"              "cd 09-docker_uri_flow && $PY test_flow_runner.py"
skip "09 full compose flow" "needs Docker"
echo "== 10-device_mesh_lab (host) =="
run "10 device_agent_policy"      "cd 10-device_mesh_lab && PYTHONPATH=. $PY tests/device_agent_policy.py"
run "10 gui_smoke"                "cd 10-device_mesh_lab && PYTHONPATH=. $PY tests/gui_smoke.py"
echo "== 11-novnc_lan_flow =="
skip "11-novnc_lan_flow" "needs Docker + noVNC"
echo "== 12-full_e2e_connect_lab (public smoke) =="
run "12 public endpoints"        "cd 12-full_e2e_connect_lab && ./scripts/public_smoke.sh"
skip "12 full Docker E2E" "needs Docker; run cd 12-full_e2e_connect_lab && make test"
echo "== 13-simple_defaults =="
run "13 python connector defaults" "cd 13-simple_defaults && $PY python_connector.py > /tmp/defaults_py_$$.json && $PY -m urirun.v2 validate /tmp/defaults_py_$$.json"
if [ "$HAVE_NODE" = 1 ]; then
  run "13 js connector defaults"  "cd 13-simple_defaults && node js/example.mjs > /tmp/defaults_js_$$.json && $PY -m urirun.v2 validate /tmp/defaults_js_$$.json"
else skip "13 js connector defaults" "no node"; fi

rm -f /tmp/ex_$$.log
echo
echo "RESULT: $PASS passed, $FAIL failed, $SKIP skipped (Docker-only)"
[ "$FAIL" -eq 0 ] || { printf 'Failed: %s\n' "${FAILED[*]}"; exit 1; }
