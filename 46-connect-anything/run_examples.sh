#!/usr/bin/env bash
set -euo pipefail

ROOT="${ROOT:-/home/tom/github}"
IFURI="${IFURI:-/home/tom/github/if-uri}"
VPY="${VPY:-$IFURI/urirun/venv/bin/python}"
URIRUN="${URIRUN:-$IFURI/urirun/venv/bin/urirun}"
ADOPT="${ADOPT:-$IFURI/urirun/venv/bin/urirun-adopt}"

section() {
  printf '\n== %s ==\n' "$1"
}

summarize_project() {
  "$VPY" -c 'import json,sys
d=json.load(sys.stdin)
value=d.get("result",{}).get("value",d)
project=value.get("project",{})
print("name:", project.get("name"))
print("primary:", project.get("primaryGroup"))
print("groups:", ", ".join(g.get("id","") for g in project.get("groups",[])))
print("routes:")
for r in project.get("uriSurface",[])[:12]:
    print(" -", r.get("uri"))'
}

section "1. Inspect tellmesh URI capability pack"
"$ADOPT" inspect --path "$ROOT/tellmesh/uriimg2nl" | summarize_project

section "2. Plan wronai OCR as Docker/CLI/service/API"
"$ADOPT" plan --path "$ROOT/wronai/ocr" | "$VPY" -c 'import json,sys
d=json.load(sys.stdin)
value=d.get("result",{}).get("value",d)
project=value.get("project",{})
plan=value.get("plan",{})
print("name:", project.get("name"))
print("primary:", project.get("primaryGroup"))
print("connector:", plan.get("connector",{}))
print("contracts:")
for c in plan.get("contracts",[]):
    print(" -", c.get("group"), "=>", c.get("contract"))
print("next steps:")
for s in plan.get("nextSteps",[]):
    print(" -", s)'

section "3. Inspect semcod imgl desktop/OCR library"
"$ADOPT" inspect --path "$ROOT/semcod/imgl" | summarize_project

section "4. Scan selected workspaces"
(cd /tmp && "$VPY" - <<'PY'
from urirun_connector_adopt.core import scan_projects

result = scan_projects(
    [
        "/home/tom/github/tellmesh",
        "/home/tom/github/wronai",
        "/home/tom/github/semcod",
    ],
    maxDepth=1,
    limit=25,
)
print("count:", result["count"])
for project in result["projects"]:
    print(f"- {project['path']} => {project['primaryGroup']} ({', '.join(project['groups'][:5])})")
PY
)

section "5. Run through a bindings file"
TMP_BINDINGS="${TMP_BINDINGS:-/tmp/adopt.bindings.json}"
"$ADOPT" bindings > "$TMP_BINDINGS"
"$URIRUN" run adopt://host/project/query/inspect "$TMP_BINDINGS" \
  --execute \
  --payload "{\"path\":\"$ROOT/tellmesh/uriimg2nl\"}" | summarize_project

section "6. Run through installed entry points"
"$URIRUN" run adopt://host/project/query/inspect \
  --entry-points \
  --execute \
  --payload "{\"path\":\"$ROOT/semcod/imgl\"}" | summarize_project
