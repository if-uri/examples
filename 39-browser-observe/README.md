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
# 0) LLM config from .env (no manual `set -a; . .env`):
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
