from __future__ import annotations

import unattended_browser as ub


def test_policy_blocks_social_write_actions():
    verdict = ub.policy_for_goal("znajdź linkedin i opublikuj post oraz wyślij wiadomości")
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
