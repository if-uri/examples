# 39 — local social autonomy on a fake LinkedIn

This example is the safe development version of "full autonomy on a social site":

- a local LinkedIn-like page,
- login credentials loaded from `.env`,
- a real local Chrome/Chromium session driven over CDP,
- autonomous login,
- autonomous fake publication,
- verification that the post landed in the local mock feed.

It never talks to linkedin.com and refuses the autonomous write flow for non-local
hosts. The default browser hostname is `linkedin.com`, mapped inside Chrome to
`127.0.0.1` with `--host-resolver-rules`, so the demo works without editing
`/etc/hosts`.

## Run

```bash
cd /home/tom/github/if-uri/examples/39-local-social-autonomy
cp .env.example .env
python3 autonomous_browser.py
```

Expected result:

```json
{
  "ok": true,
  "url": "http://linkedin.com:<port>/feed",
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
PYTHONPATH=/home/tom/github/if-uri/urirun/adapters/python \
  python3 -m urirun.runtime.v2 compile bindings.json --out .state/local-social.registry.json

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
agent runner validates and executes the command under policy.

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

- `mock_linkedin.py` — local LinkedIn-like server with `/login`, `/feed`, `/post`, `/api/posts`.
- `autonomous_browser.py` — launches Chrome, maps `linkedin.com`, logs in from `.env`, publishes, verifies.
- `nl_autonomy.py` — NL planner + URI handler for `urirun agent run`.
- `bindings.json` — typed `social://linkedin.com/post/command/publish` route.
- `run_prompt.sh` — one-command prompt runner around `urirun compile` + `urirun agent run`.
- `.env.example` — sample local-only credentials and post text.
- `test_local_social.py` — offline tests for the server, `.env` loading, and local-host scope.

## Boundary

This is intentionally full autonomy only for local/staging/mock hosts such as
`localhost`, `127.0.0.1`, `.local`, `.test`, `.internal`, `.lan`. It is the fixture to
develop selectors, OCR, closed-loop repair, and URI flow generation before any real
human-approved workflow.
