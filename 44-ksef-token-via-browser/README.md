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
   ▼
store accessToken → secret://keyring/ksef/test-access   (ready for ksef:// API calls)
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

Then it runs the **token → accessToken handshake** — in plan/dry-run by default (prints the
steps, no secrets). For a real handshake set `KSEF_NIP` + `KSEF_PUBLIC_KEY` (the MF public key)
and add `--auth`; the accessToken is stored as `secret://keyring/ksef/test-access`:

```bash
export KSEF_NIP=7781422455
export KSEF_PUBLIC_KEY=/path/to/mf-public-key.pem   # GET .../security/public-key-certificates
python3 run_token_capture.py --auth
```

## Files

- `ksef_token.py` — token masking, the read/login JS builders, secure keyring/dotenv store.
- `ksef_auth.py` — token → accessToken handshake (plan by default), accessToken stored by reference.
- `run_token_capture.py` — the interactive orchestrator (run on the Lenovo).
- `ksef-token-via-browser.flow.yaml` — the declarative URI shape (set your real selectors/URLs).

## Security model (why it's safe)

- The token value goes into the **OS keyring** (`secret://keyring/...`); bindings/flows carry
  only the reference. Resolved **only** under `--execute` with `--secret-allow`, behind a
  deny-by-default policy, and shown as `****` on every serialized surface (see example 16).
- `secret://browser/...` is deliberately refused by the framework (infostealer pattern) — we
  capture from the **controlled** CDP tab you logged into and write to keyring, not by scraping
  some other browser's storage.
- No keyring? The helper falls back to a `chmod 600` dotenv and tells you to `pip install keyring`.

## Test

```bash
pytest -q     # masking, JS builders, keyring + 0600 dotenv store, plan-mode handshake
```

> The browser/gov-site steps cannot be unit-tested here (interactive, live portal). The
> security-critical helper is fully tested; confirm the URLs/selectors against the live
> Aplikacja Podatnika KSeF before the first real run, and start on the **TEST** environment.
