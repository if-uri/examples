"""Tests for the send plan: validation is a hard gate, encryption produces the send fields,
the plan is correctly ordered, and execute refuses without an accessToken — all offline."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import pytest

import urirun_connector_invoice.core as inv
import send_invoice as si


def _valid_fa2() -> str:
    rj = '{"items": [{"name": "Kawa", "price": 29.90}], "total": 38.39, "nip": "7781422455"}'
    draft = inv.receipt_draft(receipt_json=rj, vat_rate=23, seller="SKLEP IFURI")["draft"]
    return inv.ksef_build(draft_json=json.dumps(draft), number="FV/7/2026")["xml"]


def test_plan_on_valid_invoice_has_ordered_steps():
    r = si.build_send_plan("test", _valid_fa2())
    assert r["ok"] and r["valid"] and r["dryRun"] is True
    assert r["invoiceHash"] and r["encryptedInvoiceSize"] > r["invoiceSize"]
    joined = " | ".join(r["steps"])
    assert joined.index("sessions/online") < joined.index("/invoices") < joined.index("/close") < joined.index("/upo")
    assert r["accessRef"] == "secret://keyring/ksef/test-access"


def test_validation_is_a_hard_gate():
    bad = '<Faktura xmlns="http://crd.gov.pl/wzor/2023/06/29/12648/"><Fa><P_15>1.00</P_15></Fa></Faktura>'
    r = si.send(invoice_xml=bad)
    assert r["ok"] is False and r["blocked"] == "validation"
    assert r["errors"]                                  # missing Podmiot/Adnotacje etc.


def test_execute_refused_without_access_token(monkeypatch):
    # valid invoice, but no accessToken in the keyring → must refuse, not half-send
    monkeypatch.syspath_prepend(os.path.join(os.path.dirname(__file__), "..", "44-ksef-token-via-browser"))
    import ksef_auth
    monkeypatch.setattr(ksef_auth, "resolve_token", lambda **kw: "")
    r = si.send(invoice_xml=_valid_fa2(), public_key="PUB", execute=True)
    assert r["ok"] is False and "accessToken" in r["error"]


def test_plan_default_does_not_require_secrets():
    # plain plan path must work with zero credentials
    r = si.send(invoice_xml=_valid_fa2())
    assert r["ok"] and r["dryRun"] is True


def test_parse_upo_returns_ksef_number(tmp_path):
    upo = '{"ksefReferenceNumber": "7781422455-20260623-XYZ-9", "acquisitionTimestamp": "2026-06-23T10:00:00Z"}'
    out = str(tmp_path / "upo.json")
    r = si.parse_upo(upo=upo, save_to=out)
    assert r["ok"] and r["ksefNumber"] == "7781422455-20260623-XYZ-9" and r["savedTo"] == out
