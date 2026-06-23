"""Tests for the auth handshake glue: plan mode needs no secrets; a real run stores the
accessToken by reference (never in the clear); token resolution from keyring/dotenv."""
import os
import sys
import types

sys.path.insert(0, os.path.dirname(__file__))
import ksef_auth as a
import pytest

HAS_KSEF = __import__("importlib.util", fromlist=["util"]).find_spec("urirun_connector_ksef") is not None


@pytest.mark.skipif(not HAS_KSEF, reason="urirun-connector-ksef not installed")
def test_plan_mode_needs_no_secrets():
    r = a.authenticate_and_store("test", "7781422455")
    assert r["ok"] and r["dryRun"] is True
    assert any("auth/challenge" in s for s in r["steps"])


@pytest.mark.skipif(not HAS_KSEF, reason="urirun-connector-ksef not installed")
def test_real_execute_requires_token_and_public_key(monkeypatch):
    # no stored token → clear error, nothing attempted
    monkeypatch.setattr(a, "resolve_token", lambda **kw: "")
    r = a.authenticate_and_store("test", "7781422455", public_key="PUB", execute=True)
    assert r["ok"] is False and "no stored token" in r["error"]
    # token present but no public key → refused
    monkeypatch.setattr(a, "resolve_token", lambda **kw: "TKN")
    r2 = a.authenticate_and_store("test", "7781422455", execute=True)
    assert r2["ok"] is False and "public_key" in r2["error"]


def test_execute_stores_access_token_by_reference(monkeypatch):
    fake_ksef = types.SimpleNamespace(
        authenticate=lambda *args, **kw: {"ok": True, "accessToken": "ACCESS-SECRET-123"})
    monkeypatch.setitem(sys.modules, "urirun_connector_ksef.core", fake_ksef)
    monkeypatch.setitem(sys.modules, "urirun_connector_ksef",
                        types.SimpleNamespace(core=fake_ksef))
    monkeypatch.setattr(a, "resolve_token", lambda **kw: "TKN")
    saved = {}
    monkeypatch.setitem(sys.modules, "keyring",
                        types.SimpleNamespace(set_password=lambda s, ac, t: saved.update({(s, ac): t}),
                                              get_password=lambda s, ac: None))
    r = a.authenticate_and_store("test", "7781422455", public_key="PUB", execute=True)
    assert r["ok"] and r["authenticated"] is True
    assert r["accessRef"] == "secret://keyring/ksef/test-access"
    assert saved[("ksef", "test-access")] == "ACCESS-SECRET-123"   # value in store
    assert "ACCESS-SECRET-123" not in str(r)                        # never in the result


def test_resolve_token_from_dotenv(monkeypatch, tmp_path):
    monkeypatch.setitem(sys.modules, "keyring", None)
    p = tmp_path / "test.env"
    p.write_text("KSEF_TOKEN_TEST=FROM-DOTENV-9\n", encoding="utf-8")
    assert a.resolve_token(env="test", dotenv_path=str(p)) == "FROM-DOTENV-9"
    assert a.resolve_token(env="test", dotenv_path=str(tmp_path / "missing.env")) == ""
