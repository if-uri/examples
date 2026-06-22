# 40 — create a WordPress article over a URI (REST API, Application Password)

Create an article on **your own** WordPress blog as a URI route — the proper
automation path, not by typing your password into the `wp-login.php` form.

- Auth: a WordPress **Application Password** (WP admin → Users → Profile → *Application
  Passwords*), read **by reference** from `WP_APP_PASSWORD` — this connector never asks
  for or stores it; on a urirun node back it with `secret://`.
- Endpoint: the WordPress **REST API** (`/wp-json/wp/v2/posts`), Basic-auth with the app
  password. No browser, no login form.
- Default `status="draft"` — **nothing is published.** The article lands in your WP
  admin to review; publishing is a deliberate `status="publish"` you choose.

| URI | does |
|-----|------|
| `wordpress://blog/post/command/create` | create a post (`title`, `content`, `status=draft`, `excerpt`, `categories`) |
| `wordpress://blog/post/query/list` | list recent posts/drafts (read-only) |

## Setup (once)

```bash
# In WP admin: Users → Profile → Application Passwords → add one ("urirun"), copy it.
export WP_URL=https://your-blog.example.com
export WP_USER=your-wp-login
export WP_APP_PASSWORD='xxxx xxxx xxxx xxxx xxxx xxxx'   # the Application Password, NOT your login password
```

You set these yourself — they are never typed into a form by the assistant, and the
password value is never shown to it.

## Create an article (draft)

```bash
# direct (the connector function):
python3 -c "import wp_connector, json; print(json.dumps(wp_connector.create_post(
  title='Sterowanie nodem przez URI', status='draft',
  content='<p>Jak ifURI/urirun pozwala sterować maszyną przez adresowalne URI…</p>'), indent=2))"

# as a URI route on a node (deploy the connector, then run it):
urirun host deploy laptop --bindings wp.bindings.json --code wp_connector.py --merge --identity ~/.ssh/id_ed25519
urirun run 'wordpress://blog/post/command/create' \
  --payload '{"title":"Nowy wpis","content":"<p>Treść…</p>","status":"draft"}' --execute

# NL path (the LLM drafts the article, the connector creates it as a DRAFT):
urirun host ask laptop "draft a blog post titled 'URI-driven automation' about ifURI" --env-file ../.env --execute
```

```bash
# generate the bindings file:
python3 -c "import wp_connector,json;open('wp.bindings.json','w').write(json.dumps(wp_connector.urirun_bindings()))"
```

## Boundary

| action | allowed |
|--------|---------|
| log in by typing your WordPress password into `wp-login.php` | ⛔ never — use an Application Password + the REST API |
| create a **draft** (`status=draft`) — private until you publish | ✅ yes (default) |
| **publish** (`status=publish`) — makes it public | only as a deliberate, explicit choice — review the draft first |

The credential stays a reference you control (`WP_APP_PASSWORD` / `secret://`); the
assistant never sees it. Drafts are safe to create autonomously; publishing public
content is your call.

## Files

- `wp_connector.py` — the `wordpress://` routes (REST API, app-password by reference, draft default).
- `test_wp.py` — offline test against a fake WordPress endpoint (no real blog/credentials), 3 cases.
