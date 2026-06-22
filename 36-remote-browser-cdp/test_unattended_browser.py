from __future__ import annotations

import unattended_browser as ub


def test_policy_blocks_social_write_actions():
    verdict = ub.policy_for_goal("znajdź linkedin i opublikuj post oraz wyślij wiadomości")
    assert verdict["ok"] is False
    assert verdict["blockedPatterns"]


def test_dev_override_allows_write_actions_on_localhost():
    verdict = ub.policy_for_goal(
        "opublikuj testowy post",
        "http://localhost:8080/fake-linkedin",
        dev_allow_write_actions=True,
    )
    assert verdict["ok"] is True
    assert verdict["mode"] == "dev-unattended-with-write-actions"
    assert verdict["detectedWritePatterns"]


def test_dev_override_does_not_allow_public_linkedin():
    verdict = ub.policy_for_goal(
        "opublikuj post",
        "https://www.linkedin.com/feed/",
        dev_allow_write_actions=True,
        dev_allowed_hosts=["www.linkedin.com"],
    )
    assert verdict["ok"] is False
    assert verdict["blockedPatterns"]


def test_policy_allows_read_only_observation():
    verdict = ub.policy_for_goal("sprawdź czy na ekranie jest LinkedIn i przeczytaj tytuł")
    assert verdict["ok"] is True


def test_infers_linkedin_feed_url():
    assert ub.infer_url("sprawdź linkedin", None) == "https://www.linkedin.com/feed/"


def test_summarize_page_detects_login():
    page = ub.summarize_page({"title": "LinkedIn Login", "href": "https://www.linkedin.com/login", "text": "Sign in"})
    assert page["hasLinkedIn"] is True
    assert page["hasLogin"] is True


def test_physical_screen_falls_back_to_screen_portal(monkeypatch):
    class FakeClient:
        def run(self, uri, payload=None, **kwargs):
            if uri.endswith("/kvm/screen/query/inspect"):
                return {"ok": True, "result": {"value": {"ok": False, "capture": {"ok": False}}}}
            if uri.endswith("/portal/query/capture"):
                return {"ok": True, "result": {"value": {"ok": True, "via": "portal", "base64": "ignored"}}}
            raise AssertionError(uri)

    monkeypatch.setattr(ub, "_save_portal_capture", lambda data: {"ok": True, "image": "/tmp/shot.png"})
    monkeypatch.setattr(ub, "_local_ocr", lambda image, contains: {"ok": True, "matched": True})

    routes = {
        "browser://laptop/kvm/screen/query/inspect",
        "screen://laptop/portal/query/capture",
    }
    observed = ub.observe_physical_screen(FakeClient(), "laptop", routes, "LinkedIn")
    assert observed["ok"] is True
    assert observed["method"] == "screen-portal-local-ocr"
    assert observed["attempts"][-1]["artifact"]["image"] == "/tmp/shot.png"
