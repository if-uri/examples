# 39 — controlled social autonomy with a LinkedIn-shaped site

This example is the development version of "full autonomy on a social site":

- a controlled LinkedIn-like page,
- login credentials loaded from `.env`,
- a real local Chrome/Chromium session driven over CDP,
- autonomous login,
- autonomous publication into the controlled feed,
- verification that the post landed in the controlled feed.

Domain, host, port, feed path, and host-mapping values live in `.env`. The default
`.env.example` uses `SOCIAL_BROWSER_HOSTNAME=linkedin.com` and maps that hostname
to `SOCIAL_HOST_RESOLVER_TARGET=127.0.0.1` with Chrome's
`--host-resolver-rules`. That means the address bar shows
`http://linkedin.com:<port>/feed`, while the traffic goes to the controlled
development server started by the script. The write flow refuses unmapped public
hosts, including real `https://linkedin.com/feed`.

For the real public LinkedIn site, use the read-only/supervised browser path in
[`../36-remote-browser-cdp`](../36-remote-browser-cdp/): observe the page, inspect
OCR/CDP data, and prepare drafts. Autonomous external posting, messaging,
commenting, liking, following, password entry, and similar social actions stay out
of this unattended write example.

## Run

```bash
cd /home/tom/github/if-uri/examples/39-local-social-autonomy
cp .env.example .env
python3 autonomous_browser.py
```

Relevant `.env` keys:

```dotenv
SOCIAL_ROUTE_DOMAIN=linkedin.com
SOCIAL_BROWSER_SCHEME=http
SOCIAL_BROWSER_HOSTNAME=linkedin.com
SOCIAL_FEED_PATH=/feed
SOCIAL_MAP_BROWSER_HOST=true
SOCIAL_HOST_RESOLVER_TARGET=127.0.0.1
SOCIAL_LOCAL_SUFFIXES=localhost,127.0.0.1,::1,.local,.test,.internal,.lan
```

Expected result:

```json
{
  "ok": true,
  "url": "http://linkedin.com:/feed",
  "login": {"ok": true},
  "publish": {"ok": true},
  "apiPosts": [{"content": "..."}]
}
```

Custom post:

```bash
python3 autonomous_browser.py --post "Zaloguj sie"
python3 autonomous_browser.py --post "Testowa publikacja z pelnej lokalnej autonomii."
python3 autonomous_browser.py --post "publikacja postu na temat programowania"
```

## Read-only URI command runtime

`uri_runtime.py` exposes a small typed-URI command vocabulary that drives an
attach-only CDP Chrome session: navigate, search via the site's own search,
scroll, extract posts, extract comments, OCR low-text blocks, snapshot, and
append a markdown capture. It reacts to what it finds on the page (DOM via
`Runtime.evaluate` plus Tesseract OCR for image-heavy blocks) and writes only to
local files. There is no `publish`/`comment`/`like`/`message`/`follow`/`type`/
`click` command — by registry, not by convention. A test asserts that.

Start Chrome once with a debugging port:

```bash
google-chrome --remote-debugging-port=9222
```

Run the default program (feed → search the configured phrase → scroll → extract
posts/comments → OCR the main column → append to `.state/captures.md`):

```bash
python3 uri_runtime.py --query "system design"
python3 uri_runtime.py --hashtag python
```

Run a custom JSON program:

```bash
python3 uri_runtime.py --program my_program.json --query " distributed systems"
```

`my_program.json`:

```json
[
  {"uri": "chrome://scout/search?scope=posts&q=__QUERY__", "why": "search phrase"},
  {"uri": "chrome://scout/scroll?steps=6", "why": "load results"},
  {"uri": "chrome://scout/extract_posts", "why": "grab posts"},
  {"uri": "chrome://scout/extract_comments", "why": "grab visible comments"},
  {"uri": "chrome://scout/ocr?selector=main", "why": "OCR image-heavy blocks"},
  {"uri": "chrome://scout/append_markdown?path=.state/distributed.md"}
]
```

Ready-to-run scenarios live in [`SCENARIOS.md`](SCENARIOS.md) and
[`programs/`](programs/). They cover feed capture, search+filter+save, hashtag
watching, saved-post archiving, profile activity review, and comments/OCR/
snapshot capture:

```bash
python3 uri_runtime.py --program programs/01-feed-save.json
python3 uri_runtime.py --program programs/02-search-filter-save.json --query "system design"
python3 uri_runtime.py --program programs/03-hashtag-watch.json --hashtag python
python3 uri_runtime.py --program programs/04-saved-posts-archive.json
python3 uri_runtime.py --program programs/05-profile-posts-review.json
python3 uri_runtime.py --program programs/06-comments-ocr-snapshot.json --query "agentic workflow"
```

### Command reference

| URI | params | effect |
| --- | --- | --- |
| `chrome://scout/navigate` | `url`, `settle` | go to an absolute http(s) URL |
| `chrome://scout/search` | `q`, `scope=content\|posts\|people`, `settle` | use the site's own search results URL |
| `chrome://scout/scroll` | `steps`, `delay` | scroll `steps` times by ~one viewport |
| `chrome://scout/filter` | `q` | set/clear a client-side text filter for the next extract |
| `chrome://scout/extract_posts` | `min_text_len` | pull posts (author/text/url) into the buffer |
| `chrome://scout/extract_comments` | `min_text_len` | pull visible comments into the buffer |
| `chrome://scout/ocr` | `selector` | OCR the bounding box of a CSS selector via Tesseract |
| `chrome://scout/snapshot` | `path` | save a PNG screenshot of the current page |
| `chrome://scout/append_markdown` | `path`, `heading` | flush buffer to markdown, then reset |

Result:

```json
{
  "ok": true,
  "results": [
    {"ok": true, "command": "navigate", "navigated": {"title": "Feed", "href": "https://www.linkedin.com/feed/"}},
    {"ok": true, "command": "search", "scope": "posts", "query": "system design", "url": "..."},
    {"ok": true, "command": "extract_posts", "count": 12},
    {"ok": true, "command": "append_markdown", "path": ".state/captures.md", "posts": 12, "comments": 0}
  ],
  "captured": 12
}
```

`scout.py` attaches to a Chrome session you already run with
`--remote-debugging-port` (logged in as you) and walks the read pages: home feed,
your recent activity, saved posts, and a hashtag/topic page. It scrolls, parses,
de-duplicates by URL+text, and appends interesting posts to
`.state/captures.md`. It never types, never clicks publish, and never navigates
away from these read pages — the publish step stays a human action.

Start Chrome once with a debugging port and your normal profile:

```bash
google-chrome --remote-debugging-port=9222
```

Then run the scout:

```bash
python3 scout.py
python3 scout.py --pages feed,saved
python3 scout.py --out .state/captures-python.md
```

Relevant `.env` keys:

```dotenv
LI_DEBUG_PORT=9222
LI_DEBUG_PORTS=9222,9223,9224
LI_CDP_ENDPOINTS=chrome=http://127.0.0.1:9222,brave=http://127.0.0.1:9223,chromium=http://127.0.0.1:9224
LI_PROFILE_PATH=/in/tom-developer/recent-activity/
LI_HASHTAG=programming
LI_SCROLL_STEPS=4
LI_SCROLL_DELAY=1.5
LI_MIN_TEXT_LEN=80
```

Expected result:

```json
{
  "ok": true,
  "pages": {
    "feed": {"url": "https://www.linkedin.com/feed/", "count": 12},
    "myposts": {"url": "https://www.linkedin.com/in/tom-developer/recent-activity/", "count": 3},
    "saved": {"url": "https://www.linkedin.com/my-items/saved-posts/", "count": 5},
    "hashtag": {"url": "https://www.linkedin.com/feed/hashtag/?keywords=programming", "count": 8}
  },
  "captured": 23,
  "out": ".state/captures.md"
}
```

## Find the Existing LinkedIn Session via URI

Before scouting, ask urirun which already-running browser/profile has the
LinkedIn session. This is read-only and does not launch a browser.

Start candidate browsers with separate CDP ports:

```bash
google-chrome --remote-debugging-port=9222
brave-browser --remote-debugging-port=9223
chromium --remote-debugging-port=9224
```

Set endpoints in `.env`:

```dotenv
LI_CDP_ENDPOINTS=chrome=http://127.0.0.1:9222,brave=http://127.0.0.1:9223,chromium=http://127.0.0.1:9224
```

Run the URI query:

```bash
./run_session_probe.sh
```

The script compiles and runs:

```text
browser://local/linkedin/session/query/find
```

The result reports the browser label, CDP endpoint, browser version, LinkedIn
tabs, and whether the `li_at` session cookie exists. Cookie values are never
printed.

## Natural Language Via urirun

The shortest prompt-driven command is:

```bash
./run_prompt.sh 'opublikuj "publikacja z promptu NL przez urirun agent run"'
```

That script uses built-in urirun pieces:

```bash
PYTHONPATH=/home/tom/github/if-uri/urirun/adapters/python:$PWD \
  python3 nl_autonomy.py --env .env --write-bindings .state/local-social.bindings.json

PYTHONPATH=/home/tom/github/if-uri/urirun/adapters/python \
  python3 -m urirun.runtime.v2 compile .state/local-social.bindings.json \
    --out .state/local-social.registry.json

PYTHONPATH=/home/tom/github/if-uri/urirun/adapters/python:$PWD \
  python3 -m urirun.runtime.v2 agent run .state/local-social.registry.json \
    --planner nl_autonomy:planner \
    --allow 'social://**' \
    --allow-commands \
    --goal 'opublikuj "Testowa publikacja z promptu NL przez urirun agent run"'
```

The registry exposes one command:

```text
social://linkedin.com/post/command/publish
```

`nl_autonomy:planner` maps the NL prompt to that typed URI payload, and urirun's
agent runner validates and executes the command under policy. The URI deliberately
uses `SOCIAL_ROUTE_DOMAIN` as the social domain in the action space; the handler
still starts the controlled development server and maps the browser hostname when
`SOCIAL_MAP_BROWSER_HOST=true`.

Run only the fake site:

```bash
python3 mock_linkedin.py --port 8080
```

Then open:

```text
http://127.0.0.1:8080/feed
```

The credentials are the values in `.env`.

## Files

- `mock_linkedin.py` — controlled LinkedIn-like server with `/login`, `/feed`, `/post`, `/api/posts`.
- `autonomous_browser.py` — launches Chrome, reads domain/host settings from `.env`, logs in, publishes, verifies.
- `scout.py` — read-only scout that attaches to your logged-in Chrome (CDP) and captures interesting posts to `.state/captures.md`.
- `uri_runtime.py` — read-only URI command runtime: navigate/search/scroll/extract/ocr/snapshot/append-markdown over attach-CDP. Registry-only, no write commands.
- `session_probe.py` — read-only URI handler that finds which existing CDP browser has a LinkedIn session.
- `SCENARIOS.md` — ready-to-run search/filter/save/OCR/snapshot scenarios.
- `programs/*.json` — URI programs used by `uri_runtime.py`.
- `nl_autonomy.py` — NL planner + URI handler for `urirun agent run`.
- `session-probe.bindings.json` — static snapshot for `browser://local/linkedin/session/query/find`.
- `bindings.json` — default snapshot; `run_prompt.sh` renders `.state/local-social.bindings.json` from `.env`.
- `run_prompt.sh` — one-command prompt runner around env-resolved binding generation, `urirun compile`, and `urirun agent run`.
- `run_session_probe.sh` — compiles and runs the LinkedIn session probe URI.
- `.env.example` — sample development credentials, post text, domains, hosts, ports, and mapping policy.
- `test_local_social.py` — offline tests for the server, `.env` loading, and mapped-host scope.
- `test_scout.py` — offline tests for the scout's dedupe, markdown rendering, and `.env` config parsing.
- `test_uri_runtime.py` — offline tests for URI parsing, program execution, markdown rendering, and the read-only registry invariant.
- `test_session_probe.py` — offline tests for CDP endpoint parsing and session-cookie detection.

## Boundary

This is intentionally full autonomy only for controlled hosts such as `localhost`,
`127.0.0.1`, `.local`, `.test`, `.internal`, `.lan`, or an explicitly mapped
browser hostname like `linkedin.com:<port>` in this example. It is the place to
develop selectors, OCR, closed-loop repair, and URI flow generation before any
real human-approved workflow.
