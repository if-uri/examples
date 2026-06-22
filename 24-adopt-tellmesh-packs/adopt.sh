#!/usr/bin/env bash
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Adopt a whole tree of tellmesh-style capability packs into one urirun registry,
# then verify every adopted pack: validate -> compile (merged) -> list -> dry-run.
#
# Each tellmesh library ships a `manifest.yaml` (scheme + uri_patterns + handlers).
# `urirun adopt-pack` maps that 1:1 onto urirun.bindings.v2 — no code change in the
# library. So N libraries become N URI connectors, and one merged registry is the
# single dispatch surface over all of them.
#
# Usage:
#   ./adopt.sh [TELLMESH_DIR]      # default: ../../../tellmesh, then ./manifests
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
TELLMESH="${1:-${TELLMESH_DIR:-${HERE}/../../../tellmesh}}"
OUT="${OUT_DIR:-${HERE}/generated}"
PYBIN="${PYTHON:-python3}"
# Prefer the in-repo urirun (current engine) when present, so the example never
# silently runs an older installed copy that lacks/handles adopt-pack differently.
REPO_URIRUN="${HERE}/../../urirun/adapters/python"
if [ -d "$REPO_URIRUN" ]; then
  export PYTHONPATH="${REPO_URIRUN}:${PYTHONPATH:-}"
fi
U() { "$PYBIN" -m urirun.runtime.v2 "$@"; }

rm -rf "$OUT"; mkdir -p "$OUT"

# Collect manifests: every tellmesh lib's manifest.yaml, else the bundled samples.
manifests=()
if [ -d "$TELLMESH" ]; then
  echo "== adopting tellmesh packs from ${TELLMESH} =="
  while IFS= read -r m; do manifests+=("$m"); done < <(
    for d in "$TELLMESH"/*/; do find "$d" -maxdepth 2 -name manifest.yaml 2>/dev/null | head -1; done)
else
  echo "== ${TELLMESH} not found; adopting bundled sample manifests =="
  while IFS= read -r m; do manifests+=("$m"); done < <(find "${HERE}/manifests" -name '*.yaml')
fi

ok=0; fail=0; skipped=0; total=0; bindings=()
printf "\n%-16s %-7s %-9s %s\n" "PACK" "ROUTES" "STATUS" "SCHEME"
printf -- "-------------------------------------------------------\n"
for m in "${manifests[@]}"; do
  [ -n "$m" ] || continue
  # name the pack by its manifest id (authoritative; layouts nest at different depths)
  pack="$(grep -m1 '^id:' "$m" 2>/dev/null | awk '{print $2}' | tr -d '\r')"
  [ -n "$pack" ] || pack="$(basename "$(dirname "$m")")"
  b="$OUT/${pack}.bindings.json"
  if ! U adopt-pack "$m" --out "$b" >/dev/null 2>&1 || [ ! -s "$b" ]; then
    printf "%-16s %-7s %-9s %s\n" "$pack" "-" "ADOPT-ERR" "-"; fail=$((fail+1)); continue
  fi
  n="$("$PYBIN" -c "import json;print(len(json.load(open('$b')).get('bindings',{})))" 2>/dev/null || echo 0)"
  if [ "$n" = 0 ]; then
    printf "%-16s %-7s %-9s %s\n" "$pack" "0" "skip" "(not a connector manifest)"; skipped=$((skipped+1)); continue
  fi
  sch="$("$PYBIN" -c "import json;b=json.load(open('$b'))['bindings'];print(sorted({k.split('://')[0] for k in b})[0])" 2>/dev/null)"
  if U validate "$b" >/dev/null 2>&1; then
    printf "%-16s %-7s %-9s %s\n" "$pack" "$n" "OK" "$sch"
    ok=$((ok+1)); total=$((total+n)); bindings+=("$b")
  else
    reason="$(U validate "$b" --json 2>/dev/null | "$PYBIN" -c "import json,sys;d=json.load(sys.stdin);print((d[0] if isinstance(d,list) and d else {}).get('error','invalid'))" 2>/dev/null || echo invalid)"
    printf "%-16s %-7s %-9s %s\n" "$pack" "$n" "INVALID" "$sch — $reason"; fail=$((fail+1))
  fi
done
printf -- "-------------------------------------------------------\n"
echo "adopted+valid: ${ok} · invalid/err: ${fail} · skipped(non-connector): ${skipped} · total routes: ${total}"

[ "${#bindings[@]}" -gt 0 ] || { echo "no valid packs to compile"; exit 1; }

echo "== compile all adopted packs into one registry =="
U compile "${bindings[@]}" --out "$OUT/tellmesh.registry.json" --on-conflict keep >/dev/null 2>&1 \
  || { echo "compile failed"; exit 1; }
routes="$("$PYBIN" -c "import json;d=json.load(open('$OUT/tellmesh.registry.json'));print(d.get('count') or len(d.get('index',{})))")"
echo "merged registry: $OUT/tellmesh.registry.json  (${routes} routes across ${ok} packs)"

echo "== verify dispatch: dry-run one query route per scheme =="
"$PYBIN" - "$OUT/tellmesh.registry.json" <<'PY'
import json, subprocess, sys
reg = sys.argv[1]
doc = json.load(open(reg))
uris = sorted({m.get("uri") for m in (doc.get("index") or {}).values() if m.get("uri")})
seen, checked, ok = set(), 0, 0
for uri in uris:
    scheme = uri.split("://", 1)[0]
    if scheme in seen or "/query/" not in uri:
        continue
    seen.add(scheme)
    concrete = uri.replace("{host}", "host1")
    if "{" in concrete:  # skip templated mid-path params for the smoke
        continue
    out = subprocess.run([sys.executable, "-m", "urirun.runtime.v2", "run", concrete, reg,
                          "--payload", "{}"], capture_output=True, text=True)
    checked += 1
    try:
        env = json.loads(out.stdout or "{}")
        good = env.get("ok") is True
    except Exception:
        good = False
    ok += 1 if good else 0
    print(f"  {'ok ' if good else 'BAD'} {concrete}")
print(f"dry-run dispatch: {ok}/{checked} schemes resolved")
sys.exit(0 if ok == checked else 1)
PY
echo "done"
