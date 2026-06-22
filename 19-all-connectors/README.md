# 19 — check every connector through one contract (4 languages)

Every `urirun-connector-*` — whatever language it's written in — exposes the same
contract: a `bindings` command emitting `urirun_bindings()`. This sweep drives all
17 connectors through it:

```
emit bindings ─▶ urirun validate ─▶ urirun compile ─▶ run a route (or mark config-gated)
```

```bash
python3 check_all.py        # builds the Go connector + PHP/JS shims, then sweeps
pytest test_all_connectors.py -q
```

Result (17 connectors, Python / PHP / Go / JS):

```
base64   php  RAN ✓     time-tools     py  RAN ✓     ksef          py  valid (config-gated)
hash     go   RAN ✓     mcp-filesystem py  RAN ✓     planfile      py  valid (config-gated)
uuid     js   RAN ✓     http-check     py  RAN ✓     namecheap-dns py  valid (config-gated)
                        domain-monitor py  RAN ✓     llm           py  valid (config-gated)
                        browser-control py RAN ✓     kvm           py  valid (config-gated)
                        get-node/email/sqlite-context/mqtt  py  RAN ✓
── 17/17 valid · 12 executed a route · 0 broken ──
```

## What it proves

- **One uniform contract.** Every connector compiles to a valid registry and is
  driven by the *same* `urirun run`, regardless of implementation language.
- **Polyglot.** The Python runtime spawns the PHP (`base64`), Go (`hash`) and JS
  (`uuid`) connectors via the URI argv — no language-specific glue.
- **12 execute end-to-end** (offline + network routes); the **5 "config-gated"**
  ones (`ksef` live MF API, `llm` API key, `namecheap-dns` creds, `kvm` device,
  `planfile` project) are valid and only need their runtime config to run — which
  is exactly the point: the *contract* is verified independently of the *backend*.

Pair this with [`18-connector-transport/`](../18-connector-transport/) (serve any
connector over HTTP) — together they show a connector is plugged into a runtime and
a transport, never bound to either.
