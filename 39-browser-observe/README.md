# 39 — autonomous READ-ONLY browser observation (gillm + LLM vision over URIs)

Capture a node's **real screen** and let an LLM tell you what's on it — fully
autonomous, but **observation-only**. It uses three local projects as URIs:

- **gillm** (`semcod/gillm`) → `screen://<node>/portal/query/capture` — Wayland screen
  capture via the XDG Desktop Portal (the path that works on GNOME/Wayland where
  `gnome-screenshot`/`x11grab`/`pipewire` return a black frame or hang).
- a **vision LLM** (`LLM_MODEL`, e.g. a `*image*`/`*vision*` model) → describes the
  capture.
- **imgl/vql** (`semcod/imgl`, `oqlos/vql`) can be added as `imgl://…/screen/query/layout`
  for structured OCR (text + element bounding boxes) instead of a prose description.

Verified live on a node ("laptop"): captured 884 KB, and the model reported *"the
LinkedIn website, where user Tom Sapletta is logged in … a messaging pane on the right
…"* — all read-only.

## The read-only gate

`observe.py` refuses every write/social/login/payment URI before it runs, so an
autonomous loop can **never** turn observation into a post, a message, a like, a login
or a purchase — regardless of the goal it's given:

```python
REFUSED = ("/command/", "publish", "form/command/submit", "message", "/send", "dm",
           "comment", "like", "follow", "login", "password", "input/command", "click",
           "type", "pay", "buy", "checkout")
```

`assert_read_only(uri)` runs on every call. Reads (`screen://…/query/capture`,
`browser://…/page/query/dom`) pass; writes (`…/form/command/submit`,
`linkedin://post/command/publish`) are refused.

## Example commands — the autonomous loop

```bash
# 0) LLM config from ../.env or ./.env (no manual `set -a; . .env`):
#    LLM_MODEL=openrouter/google/gemini-3.1-flash-image-preview   (a VISION model)
#    OPENROUTER_API_KEY=sk-or-...

# 1) read-only observe: capture the screen + describe it (self-deploys gillm capture if missing)
NODE_URL=http://192.168.188.201:8766 NODE=laptop \
  python3 observe.py

# 2) the LLM "host ask" path, with auto-loaded .env (new --env-file):
urirun host ask laptop "what is on the screen right now" --env-file ../.env --execute

# 3) auto-load ./.env without a flag:
URIRUN_DOTENV=1 urirun host ask laptop "is LinkedIn open and logged in" --execute

# 4) self-managing variant: if the node lacks the capability, it installs it first
NODE_URL=http://192.168.188.201:8766 NODE=laptop \
  python3 ../38-self-managing/run_live.py "capture the screen and tell me what app is open"
```

## Live node smoke test

Current `laptop` state can be checked without guessing:

```bash
curl -fsS --max-time 6 http://192.168.188.201:8766/health
curl -fsS --max-time 6 http://192.168.188.201:8766/routes
```

On 2026-06-23 the node was up as `laptop`, running urirun `0.4.56`. Before
`observe.py` provisioned screen capture it served five CDP routes:

```text
browser://laptop/cdp/session/command/launch
browser://laptop/cdp/page/command/navigate
browser://laptop/cdp/page/query/eval
browser://laptop/cdp/page/query/screenshot
browser://laptop/cdp/page/query/tabs
```

After `observe.py` ran, it merged the portal-capture route too:

```text
screen://laptop/portal/query/capture
```

That surface is enough to test real browser control over URI:

```bash
cd /home/tom/github/if-uri/examples
NODE_URL=http://192.168.188.201:8766 NODE=laptop \
  /home/tom/github/if-uri/urirun/venv/bin/python3 \
  36-remote-browser-cdp/drive_cdp.py https://www.linkedin.com/feed/
```

Observed result on `laptop`:

```text
6/6 CDP browser steps ok on laptop
title: LinkedIn Login, Sign in | LinkedIn
links: 24
screenshot: 27879-byte PNG
tabs: LinkedIn Login, Sign in | LinkedIn
```

This confirms that urirun controls the node browser through `browser://.../cdp/*`.
It also shows that this route launches/uses the CDP profile, not necessarily the
physical browser profile where a human is already logged in.

The real monitor capture path was also tested:

```bash
cd /home/tom/github/if-uri/examples/39-browser-observe
NODE_URL=http://192.168.188.201:8766 NODE=laptop \
  /home/tom/github/if-uri/urirun/venv/bin/python3 observe.py
```

Observed result without a configured vision model in the shell:

```json
{
  "ok": true,
  "captured_bytes": 538550,
  "note": "set LLM_MODEL (vision) to analyse the image"
}
```

Observed result with `LLM_MODEL`/`OPENROUTER_API_KEY` loaded from `../.env`:

```text
captured_bytes: 538328
observation: terminal application open on a Linux desktop; urirun startup output
             visible, including port 8766 and security warnings.
```

For full monitor-based autonomy (`real desktop screenshot -> OCR/vision -> decision`)
the node needs one screen/KVM route such as:

```text
screen://laptop/portal/query/capture
browser://laptop/kvm/screen/query/inspect
```

Without one of those, `observe.py` self-provisions the `screen://` capture handler
when `/deploy` is enabled and the node desktop has `python3-dbus` and
`python3-gobject`. The CDP smoke test above remains the fallback proof that URI
browser control itself works.

## What it will and won't do

| action | autonomous? |
|--------|-------------|
| capture the screen, read the feed/DOM, OCR, summarise, **draft** a post/reply for you | ✅ yes |
| publish a post, send a DM, comment, like, follow, log in, pay | ⛔ no — these reach real people on a live platform; they need you to do them (or confirm a single specific item) |

A "local node" only means the browser runs on your LAN — **LinkedIn is still the live
public site**, so a post/message there is real. This example stays observation-only by
design; for a single post you've written, fill the composer and stop before *Publish*
so a human clicks it.

## Files

- `gillm_capture.py` — gillm's portal screen capture as a deployable URI handler.
- `observe.py` — capture → vision-LLM description, with the read-only gate.
