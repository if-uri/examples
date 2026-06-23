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
```

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
- `nl_autonomy.py` — NL planner + URI handler for `urirun agent run`.
- `bindings.json` — default snapshot; `run_prompt.sh` renders `.state/local-social.bindings.json` from `.env`.
- `run_prompt.sh` — one-command prompt runner around env-resolved binding generation, `urirun compile`, and `urirun agent run`.
- `.env.example` — sample development credentials, post text, domains, hosts, ports, and mapping policy.
- `test_local_social.py` — offline tests for the server, `.env` loading, and mapped-host scope.

## Boundary

This is intentionally full autonomy only for controlled hosts such as `localhost`,
`127.0.0.1`, `.local`, `.test`, `.internal`, `.lan`, or an explicitly mapped
browser hostname like `linkedin.com:<port>` in this example. It is the place to
develop selectors, OCR, closed-loop repair, and URI flow generation before any
real human-approved workflow.
