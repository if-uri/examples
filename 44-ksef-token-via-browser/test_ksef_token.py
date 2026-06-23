"""Tests for the security-critical glue: token masking, JS builders, and the keyring/dotenv
store (which must return a reference + masked preview, never the raw token)."""
import os
import sys
import types

sys.path.insert(0, os.path.dirname(__file__))
import ksef_token as k


def test_mask_hides_the_middle():
    assert k.mask("ABCDEFGHIJ") == "ABC*****IJ"
    assert k.mask("short") == "*****"           # <=6 chars fully hidden
    assert k.mask("") == ""


def test_login_check_js_with_and_without_marker():
    assert "querySelector('#logout')" in k.build_login_check_js("#logout")
    assert "login" in k.build_login_check_js("")  # default: off the login page


def test_token_read_js_targets_selector():
    js = k.build_token_read_js("#token-value")
    assert "querySelector('#token-value')" in js and "trim()" in js


def test_store_token_uses_keyring_and_returns_reference(monkeypatch):
    saved = {}
    fake = types.SimpleNamespace(set_password=lambda s, a, t: saved.update({(s, a): t}))
    monkeypatch.setitem(sys.modules, "keyring", fake)
    r = k.store_token("SECRET-TOKEN-XYZ", service="ksef", account="test-token")
    assert r["ok"] and r["backend"] == "keyring"
    assert r["ref"] == "secret://keyring/ksef/test-token"
    assert saved[("ksef", "test-token")] == "SECRET-TOKEN-XYZ"   # value in store...
    # ...but never returned in the clear
    assert "SECRET-TOKEN-XYZ" not in str(r)
    assert r["masked"] == "SEC***********YZ"   # 16 chars → first 3 + 11 hidden + last 2


def test_store_token_dotenv_fallback_is_0600(monkeypatch, tmp_path):
    # force the keyring import to fail → dotenv fallback
    monkeypatch.setitem(sys.modules, "keyring", None)
    path = str(tmp_path / "ksef.env")
    r = k.store_token("TKN-123456", env="test", dotenv_path=path)
    assert r["ok"] and r["backend"] == "dotenv"
    assert r["ref"] == f"secret://dotenv/{path}#KSEF_TOKEN_TEST"
    assert oct(os.stat(path).st_mode)[-3:] == "600"
    assert "KSEF_TOKEN_TEST=TKN-123456" in open(path).read()
    assert "TKN-123456" not in str(r)            # raw token not in the result


def test_store_token_rejects_empty():
    assert k.store_token("   ")["ok"] is False
