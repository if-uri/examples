# 39 — local social autonomy on a fake LinkedIn

This example is the safe development version of "full autonomy on a social site":

- a local LinkedIn-like page,
- login credentials loaded from `.env`,
- a real local Chrome/Chromium session driven over CDP,
- autonomous login,
- autonomous fake publication,
- verification that the post landed in the local mock feed.

It never talks to linkedin.com and refuses the autonomous write flow for non-local
hosts. The default browser hostname is `linkedin.local`, mapped inside Chrome to
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
  "url": "http://linkedin.local:<port>/feed",
  "login": {"ok": true},
  "publish": {"ok": true},
  "apiPosts": [{"content": "..."}]
}
```

Custom post:

```bash
python3 autonomous_browser.py --post "Testowa publikacja z pelnej lokalnej autonomii."
```

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
- `autonomous_browser.py` — launches Chrome, maps `linkedin.local`, logs in from `.env`, publishes, verifies.
- `.env.example` — sample local-only credentials and post text.
- `test_local_social.py` — offline tests for the server, `.env` loading, and local-host scope.

## Boundary

This is intentionally full autonomy only for local/staging/mock hosts such as
`localhost`, `127.0.0.1`, `.local`, `.test`, `.internal`, `.lan`. It is the fixture to
develop selectors, OCR, closed-loop repair, and URI flow generation before any real
human-approved workflow.
