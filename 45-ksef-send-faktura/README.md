# 45 — send a KSeF FA(2) invoice (plan-ready)

The last leg of the office pipeline: take the **FA(2) XML** (built in example 43 from a
scanned receipt) and submit it to KSeF. **Plan/dry-run by default** — it validates, encrypts
and lays out the exact API sequence with **zero secrets**, so you can review everything before
the first real send. Flip to `--execute` once the accessToken is in the keyring (example 44).

```text
faktura-fa2.xml
   ▼
invoice://…/ksef/query/validate     ← HARD GATE: invalid → never sent
   ▼
encrypt locally (AES-256-CBC, key wrapped RSA-OAEP with the MF public key; SHA-256 hash)
   ▼
POST  /sessions/online              ← open session (Bearer {getv:KSEF_ACCESS_TOKEN})
PUT   /sessions/online/{ref}/invoices   ← send encryptedInvoiceContent + invoiceHash
POST  /sessions/{ref}/close
GET   /sessions/{ref}/upo            ← UPO = urzędowe potwierdzenie odbioru
   ▼
invoice://…/ksef/query/upo           ← parse UPO → assigned KSeF number + archive the raw UPO
```

## Run (plan)

```bash
# FA(2) from the receipt chain (example 43), or any FA(2) XML:
export FAKTURA_XML="$HOME/.urirun/camera-scans/receipt-invoice/faktura.xml"
python3 send_invoice.py
```

Prints the real `api-test` URLs, the SHA-256 `invoiceHash`, the encrypted size, and the
accessToken reference — nothing secret:

```
invoiceHash : EWw4hrRqY8bq…=  (1117 B → 1136 B encrypted)
auth        : Authorization: Bearer {getv:KSEF_ACCESS_TOKEN}   (secret://keyring/ksef/test-access)
  · POST https://api-test.ksef.mf.gov.pl/api/v2/sessions/online  …
  · PUT  …/sessions/online/{ref}/invoices  …
  · POST …/sessions/{ref}/close
  · GET  …/sessions/{ref}/upo
```

## Run (real, on the node)

```bash
# 1. capture the KSeF token + accessToken (example 44, on the Lenovo)
# 2. point at the MF public key and execute:
export KSEF_PUBLIC_KEY=/path/to/mf-public-key.pem
python3 send_invoice.py --execute
```

`--execute` refuses (cleanly) unless the accessToken is in the keyring and the MF public key is
given — it never half-sends. The live HTTP session dance runs through the `ksef://` connector
routes (see `ksef-send.flow.yaml`), with the token injected at the executor boundary.

## Files

- `send_invoice.py` — validate → encrypt → plan (real crypto, no secrets); guarded `--execute`;
  `parse_upo()` reads the confirmation into the assigned **KSeF number** and archives the raw UPO.
- `ksef-send.flow.yaml` — the declarative session→send→UPO→parse sequence (Bearer by reference).

## Test

```bash
pytest -q   # validation gate, encryption fields, plan ordering, execute-refused-without-token
```

> Validation uses the structural check unless you set `KSEF_FA2_XSD` to the official FA(2)
> schema (then it's a full XSD validation — example 43). Always start on the **TEST** environment.
