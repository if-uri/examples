# 24 — adopt tellmesh libraries into URI (reuse, don't rewrite)

The sibling `../tellmesh` monorepo is ~50 Python libraries that already speak URI
internally (`urikvm`, `uriocr`, `urillm`, `urivql`, …). Each ships a **capability
manifest** — `manifest.yaml` with `scheme` + `uri_patterns` + `handlers`. This
example shows how to **adopt all of them into one urirun registry with zero code
change**, and verify they work.

`urirun adopt-pack` maps a manifest **1:1** onto `urirun.bindings.v2`: each
`uri_pattern` becomes a route, each `handler` (`python://pkg.module:func`) becomes
the route's `local-function` adapter. The library doesn't import urirun and isn't
modified — urirun just *reads* its manifest. N libraries → N URI connectors → one
merged dispatch surface.

```txt
tellmesh/urikvm/.../manifest.yaml ─┐
tellmesh/uriocr/.../manifest.yaml ─┤  urirun adopt-pack  ─► *.bindings.v2.json
tellmesh/urillm/.../manifest.yaml ─┘                              │
                                        urirun compile  ◄─────────┘
                                              │
                                     one registry: 110 routes / 23 packs
```

## Adopt one pack

```bash
urirun adopt-pack ../../../tellmesh/uriocr/uriocr/manifest.yaml --out ocr.bindings.json
urirun validate  ocr.bindings.json          # OK
urirun compile   ocr.bindings.json --out ocr.registry.json
urirun list      ocr.registry.json          # ocr://… routes, adapter local-function
urirun run 'ocr://host1/image/latest/query/text' ocr.registry.json --payload '{}'  # dry-run plan
```

## Adopt the whole tree at once

`urirun adopt-pack <dir>` walks every `manifest.yaml` under a tree and merges them, so
adopting the whole monorepo is **one command** (no per-pack loop):

```bash
urirun adopt-pack ../../../tellmesh --out tellmesh.bindings.json \
  --registry-out tellmesh.registry.json --on-conflict keep
```

`./adopt.sh [TELLMESH_DIR]` wraps that and validates the merged document. Current run
over `../tellmesh`:

```
== adopt every pack under ../tellmesh ==
merged document is valid
merged: 110 routes across 23 packs -> 110 compiled
schemes: app, browser, chat, env, him, img2nl, kv, kvm, llm, log, message, node,
         ocr, process, rdp, screen, shell, stepper, stt, urimail, urioffice, vql, webrtc
```

The whole tellmesh URI surface — **110 routes across 23 schemes** — becomes one merged
dispatch surface, reused as-is. (`test_adopt.py` additionally dry-run-dispatches an
adopted route to prove it resolves; example 25 executes a multi-step flow over the
adopted packs.)

## Nuances the adoption surfaces (it validates, it doesn't lie)

Adoption is a real contract check, not a rubber stamp:

- **flat URIs are rejected** — a flat `demo://{thing}` (one path segment) fails
  validation because urirun requires `scheme://target/resource/.../operation`:
  `invalid uri: URI must include resource and operation segments`. The fix belongs in
  the manifest, not in urirun. `urishell` originally shipped a flat `shell://{command}`
  and now ships `shell://{host}/process/command/run` (command moved to the payload) —
  so it adopts cleanly. `manifests/flat-uri-bad.manifest.yaml` keeps the rejected shape
  so the grammar check stays demonstrated.
- **non-connector manifests are skipped** — `tellmesh/manifest.yaml` is a
  monorepo-dropin descriptor (`package`/`layout`/`adds`), not a capability pack, so it
  yields 0 routes and is reported as `skip (not a connector manifest)`.
- **handlers stay declarative** — a route's `python://pkg:func` handler is recorded as
  the `local-function` adapter; **dry-run** resolves and validates the route without
  importing the tellmesh package, so the whole tree verifies even if not every pack is
  installed. `--execute` is what actually imports and calls the handler.

## Files

- `adopt.sh` — adopt every tellmesh manifest, validate, merge-compile, dispatch-smoke.
- `manifests/` — bundled so the example/test run without tellmesh: `uriocr.manifest.yaml`
  (a real pack, adopts cleanly) and `flat-uri-bad.manifest.yaml` (synthetic, the
  rejected flat-URI shape).
- `test_adopt.py` — offline CI: manifest → bindings → validate → compile → dry-run,
  plus the flat-URI rejection.
- `generated/` — output of `adopt.sh` (regenerated; not checked in).

## Adopting more, in other languages

The same `adopt-pack` reads a `[tool.urirun]` table in `pyproject.toml` (Python source
adoption) and a `"urirun"` key in `package.json` (Node), and can resolve an **installed**
package's manifest via the `urirun.packs` entry point — so a published library is
adopted by name without a path. Point urirun at the manifest, the pyproject, or the
package; the URI surface comes along for free.
