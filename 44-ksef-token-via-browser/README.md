# 44 — assisted KSeF token capture via the browser (Lenovo)

Ease KSeF authorization: instead of hand-copying a token out of the **Aplikacja Podatnika
KSeF**, drive the browser on the Lenovo node, **you** log in with Profil Zaufany, and the
script reads the freshly generated token from the page and stores it as a **secret reference**
— the value never lands in a flow, a log or a screenshot.

```text
browser://cdp launch (visible Chrome on Lenovo)
   ▼
open KSeF web app (TEST)  ──►  YOU log in via Profil Zaufany (login.gov.pl)   ← human, interactive
   ▼
go to "Tokeny" ──► YOU click "Generuj token"
   ▼
browser://cdp eval  → read token from the DOM (shown once)
   ▼
store in OS keyring  →  secret://keyring/ksef/test-token   (value stays in the store)
   ▼
ksef://test/auth/...  → token → accessToken  (handshake; token never sent in plaintext)
```

## What is and isn't automated

- **Manual (by design):** the Profil Zaufany login and the "Generuj token" click. Government
  2FA / Trusted Profile is interactive — automation drives navigation and capture, you confirm.
- **Automated:** launching the browser, detecting the logged-in state, opening the tokens page,
  reading the token from the DOM, and storing it securely.

You do this **once** — the KSeF token is long-lived; later API calls use it (and a short-lived
accessToken). So the win is the one-time capture + safe storage.

## Run (on the Lenovo)

```bash
# confirm these against the LIVE page first (the gov DOM changes):
export KSEF_ENV=test
export KSEF_LOGIN_URL="https://ksef-test.mf.gov.pl/web/login"
export KSEF_TOKENS_URL="https://ksef-test.mf.gov.pl/web/tokens"
export KSEF_LOGIN_MARKER='[data-test="logout"]'   # a CSS selector only present once logged in
export KSEF_TOKEN_SELECTOR='#token-value'         # CSS selector of the generated token value

python3 run_token_capture.py
```

It prints only a **reference** + a masked preview, e.g.:

```
ref     : secret://keyring/ksef/test-token
podgląd : AbC***********yZ
--secret-allow 'secret://keyring/ksef/test-token'
```

## Security model (why it's safe)

- The token value goes into the **OS keyring** (`secret://keyring/...`); bindings/flows carry
  only the reference. Resolved **only** under `--execute` with `--secret-allow`, behind a
  deny-by-default policy, and shown as `****` on every serialized surface (see example 16).
- `secret://browser/...` is deliberately refused by the framework (infostealer pattern) — we
  capture from the **controlled** CDP tab you logged into and write to keyring, not by scraping
  some other browser's storage.
- No keyring? The helper falls back to a `chmod 600` dotenv and tells you to `pip install keyring`.

## Files

- `ksef_token.py` — testable glue: token masking, the read/login JS builders, secure store.
- `run_token_capture.py` — the interactive orchestrator (run on the Lenovo).
- `ksef-token-via-browser.flow.yaml` — the declarative URI shape (set your real selectors/URLs).

## Test

```bash
pytest test_ksef_token.py -q     # masking, JS builders, keyring + 0600 dotenv store
```

> The browser/gov-site steps cannot be unit-tested here (interactive, live portal). The
> security-critical helper is fully tested; confirm the URLs/selectors against the live
> Aplikacja Podatnika KSeF before the first real run, and start on the **TEST** environment.
