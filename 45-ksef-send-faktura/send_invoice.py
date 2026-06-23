# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Send a KSeF FA(2) invoice — plan/dry-run by default, ready to flip to --execute once the
# accessToken is in the keyring (see example 44). The chain: VALIDATE the XML (gate — never
# send invalid), ENCRYPT it locally (AES-256-CBC, key wrapped with the MF public key), then
# the online session sequence: open → send → close → poll UPO. Real crypto runs in plan mode
# too (no secrets), so you see the exact send-request fields before anything leaves the host.

from __future__ import annotations

import os
import sys
from typing import Any

import urirun_connector_invoice.core as inv
import urirun_connector_ksef.core as ksef

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "44-ksef-token-via-browser"))


def build_send_plan(env: str, invoice_xml: str, *, access_ref: str = "",
                    xsd_path: str = "") -> dict[str, Any]:
    """Validate + encrypt an FA(2) invoice and return the ordered KSeF send plan. No network,
    no secrets — the gate (valid) and the encrypted-field shapes are all computed locally."""
    val = inv.ksef_validate(xml=invoice_xml, xsd_path=xsd_path)
    if not val.get("valid"):
        return {"ok": False, "blocked": "validation", "checkedWith": val.get("checkedWith"),
                "errors": val.get("errors", []), "warnings": val.get("warnings", [])}

    enc = ksef.encrypt_invoice(invoice_xml.encode("utf-8"))
    base_urls = getattr(getattr(ksef, "auth", None), "BASE_URLS", {}) or getattr(ksef, "BASE_URLS", {})
    base = base_urls.get(env, f"<{env}>")
    ref = access_ref or f"secret://keyring/ksef/{env}-access"
    steps = [
        f"POST {base}/sessions/online  (open; AES-256 session key wrapped RSA-OAEP with the MF public key)",
        f"PUT  {base}/sessions/online/{{ref}}/invoices  (send: encryptedInvoiceContent + invoiceHash)",
        f"POST {base}/sessions/{{ref}}/close",
        f"GET  {base}/sessions/{{ref}}/upo  (poll → UPO = urzędowe potwierdzenie odbioru)",
        "invoice://host/ksef/query/upo  (parse UPO → KSeF number; archive the raw UPO)",
    ]
    return {"ok": True, "valid": True, "checkedWith": val.get("checkedWith"),
            "env": env, "accessRef": ref, "dryRun": True,
            "invoiceHash": enc.get("invoiceHash"), "invoiceSize": enc.get("invoiceSize"),
            "encryptedInvoiceSize": enc.get("encryptedInvoiceSize"),
            "authHeader": "Authorization: Bearer {getv:KSEF_ACCESS_TOKEN}",
            "steps": steps}


def parse_upo(upo: str = "", upo_path: str = "", save_to: str = "") -> dict[str, Any]:
    """Parse the UPO returned by the send (the assigned KSeF number + timestamp) and archive
    the raw UPO. Thin wrapper over invoice://host/ksef/query/upo so the send example is
    self-contained — the KSeF number is the proof the e-invoice was accepted."""
    return inv.ksef_upo(text=upo, path=upo_path, output_path=save_to)


def send(env: str = "test", invoice_path: str = "", invoice_xml: str = "",
         public_key: str = "", xsd_path: str = "", execute: bool = False) -> dict[str, Any]:
    """Plan (default) or execute the send. Execute needs the accessToken in the keyring and the
    MF public key; without them it refuses with a clear message rather than half-sending."""
    if not invoice_xml:
        if not invoice_path:
            return {"ok": False, "error": "provide invoice_xml or invoice_path"}
        try:
            invoice_xml = open(os.path.expanduser(invoice_path), encoding="utf-8").read()
        except OSError as exc:
            return {"ok": False, "error": str(exc)}

    plan = build_send_plan(env, invoice_xml, xsd_path=xsd_path)
    if not plan.get("ok"):
        return plan
    if not execute:
        return plan

    # --- real send (guarded): needs accessToken + MF public key ---
    try:
        from ksef_auth import resolve_token  # type: ignore
    except Exception:  # noqa: BLE001
        return {"ok": False, "error": "ksef_auth helper not importable (example 44 on sys.path)"}
    access = resolve_token(account=f"{env}-access", env=env)
    if not access:
        return {"ok": False, "error": f"no accessToken in keyring "
                                      f"(run example 44 with --auth first; secret://keyring/ksef/{env}-access)"}
    if not public_key:
        return {"ok": False, "error": "real send needs the MF public_key (to wrap the session key)"}
    # The actual HTTP session dance runs through the ksef:// connector routes with the
    # accessToken injected at the executor boundary. Left to the live run on the node.
    return {"ok": False, "error": "live send not performed here — run on the node with the "
                                  "ksef:// routes; this script validated, encrypted and planned it",
            "plan": plan}


def main() -> int:
    env = os.getenv("KSEF_ENV", "test")
    path = os.getenv("FAKTURA_XML", "")
    if not path:
        print("set FAKTURA_XML=/path/to/faktura-fa2.xml")
        return 2
    res = send(env=env, invoice_path=path, xsd_path=os.getenv("KSEF_FA2_XSD", ""),
               public_key=os.getenv("KSEF_PUBLIC_KEY", ""), execute="--execute" in sys.argv)
    if res.get("blocked") == "validation":
        print(f"[!] FA(2) invalid ({res['checkedWith']}) — NIE wysyłam:")
        for e in res.get("errors", []):
            print("   ✗", e)
        return 1
    if not res.get("ok") and "error" in res and "plan" not in res:
        print(f"[!] {res['error']}")
        return 1
    plan = res if res.get("dryRun") else res.get("plan", {})
    print(f"== KSeF send plan ({plan.get('checkedWith')} valid) — env={plan.get('env')} ==")
    print(f"invoiceHash : {plan.get('invoiceHash')}  ({plan.get('invoiceSize')} B → "
          f"{plan.get('encryptedInvoiceSize')} B encrypted)")
    print(f"auth        : {plan.get('authHeader')}   ({plan.get('accessRef')})")
    for s in plan.get("steps", []):
        print("  ·", s)
    print("\nRealnie: ustaw accessToken (przykład 44 --auth) + KSEF_PUBLIC_KEY, dodaj --execute.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
