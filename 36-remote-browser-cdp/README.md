# 36 — control a remote browser over CDP (no xdotool/ydotool, Wayland-safe)

Drive a node's **real browser** from the host over the URI contract, using the
browser-control connector's **Chrome DevTools Protocol** surface
(`browser://<node>/cdp/...`). CDP runs headed under Wayland and needs no
`xdotool`/`ydotool` — the practical way to control Chrome on a Linux desktop node.

```
host                                node (Chrome + a urirun node)
 browser://NODE/cdp/session/command/launch {headless}   ── launch Chrome w/ debug port
 browser://NODE/cdp/page/command/navigate  {url}        ── go to a page
 browser://NODE/cdp/page/query/eval        {expr}       ── run JS in the page, get the value
 browser://NODE/cdp/page/query/screenshot              ── PNG over CDP
 browser://NODE/cdp/page/query/tabs                    ── list tabs
```

The surface is **stateful**: launch first, then navigate / eval / screenshot
against the live page.

## Run

Against any node that serves the CDP surface (e.g. a remote box):

```bash
NODE_URL=http://192.168.188.201:8765 NODE=laptop python3 drive_cdp.py https://example.com
```

Read-only unattended browser observation, with physical-screen KVM/OCR detection first,
`screen://.../portal/query/capture` + local OCR fallback second, and CDP fallback third:

```bash
NODE_URL=http://192.168.188.201:8766 NODE=laptop \
  python3 unattended_browser.py --unattended "sprawdź czy na ekranie jest LinkedIn"
```

The unattended runner is intentionally **read-only**. It refuses social writes and
login/payment actions such as publishing posts, sending messages, commenting, liking,
following, entering passwords, or buying. Use it to inspect the screen/page, capture
evidence, and prepare drafts for a human to approve.

When the node can capture the desktop through `screen://<node>/portal/query/capture`,
the runner saves the PNG under `~/.urirun/artifacts/screenshots/` and OCRs it locally
with `tesseract` when available. This is the practical GNOME/Wayland path when
`grim` is missing and `gnome-screenshot` hangs inside the node process.

For local development and fake/staging surfaces, the runner has a dev override:

```bash
python3 unattended_browser.py --unattended --dev-allow-write-actions \
  --url http://localhost:8080/fake-linkedin \
  "opublikuj testowy post w lokalnym fake LinkedIn"
```

The override only applies to allowlisted non-public hosts (`localhost`, `.test`,
`.local`, `.internal`, `.lan`, plus repeated `--dev-allow-host`). It intentionally
does not override public social sites such as `linkedin.com`.

Self-contained local proof (spins a local node, deploys the CDP handler, drives a
local Chrome) — needs a Chrome/Chromium on this machine:

```bash
./e2e.sh
```

```
== deploy the CDP surface ==
  deploy ok= True routeCount= 5
== drive the local browser over CDP ==
  ✓ launch        {"ok":true,"browser":"Chrome/149.0.7827.155","debugPort":9222,...}
  ✓ navigate      https://example.com
  ✓ eval title    'Example Domain'
  ✓ eval links    1 <a> on the page
  ✓ screenshot    17149-byte PNG
  ✓ tabs          ['Example Domain', 'about:blank']
  6/6 CDP browser steps ok
```

Verified live the same way against a remote Fedora node ("lenovo", 192.168.188.201).

## Why CDP (and not the GUI/KVM path)

The browser-control connector also has a browser-agnostic `browser://<node>/kvm/*`
path (launch + navigate + type + click-text + capture by GUI automation). On a
**GNOME/Wayland** node that path needs `ydotool`+`grim` and the node running inside
the graphical user session. **CDP sidesteps all of that** for Chrome-family
browsers: the debug protocol drives the page directly, headed or headless, no input
tools, no portal. For Chrome on Linux desktops, prefer `browser://.../cdp/*`.

## Files

- `drive_cdp.py` — host-side driver: launch → navigate → eval → screenshot → tabs (`NODE_URL`, `NODE`).
- `unattended_browser.py` — KVM/OCR-first, screen-portal/OCR fallback, then CDP read-only
  unattended observation with policy gates for social-write/login/payment actions.
- `cdp-bindings.json` — the 5 CDP routes (templated on `NODE`), mapping to the connector's `cdp-flat-handler.py`.
- `e2e.sh` — local node + signed `/deploy` of the CDP handler + `drive_cdp.py` (self-contained; skips if no Chrome).

The handler is [`urirun-connector-browser-control/examples/cdp-flat-handler.py`](../../urirun-connector-browser-control/examples/cdp-flat-handler.py)
(stdlib-only CDP WebSocket client; deployable as a single file).
