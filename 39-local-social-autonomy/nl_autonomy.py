#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Natural-language planner + URI handler for the local fake LinkedIn example.
# This is intentionally small: it plugs into `urirun agent run` as
# `--planner nl_autonomy:planner` and exposes a typed local-function route.

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import autonomous_browser
import mock_linkedin


ROUTE = "social://linkedin.local/post/command/publish"


def extract_post(prompt: str, env_path: str | Path = autonomous_browser.DEFAULT_ENV) -> str:
    """Pull a fake post body from a short NL prompt.

    Supported forms:
    - `opublikuj "tekst posta"`
    - `post: tekst posta`
    - `opublikuj tekst posta`
    - fallback: FAKE_LINKEDIN_POST from .env
    """
    prompt = " ".join(str(prompt).split())
    quoted = re.search(r'"([^"]+)"|\'([^\']+)\'', prompt)
    if quoted:
        return (quoted.group(1) or quoted.group(2)).strip()
    marker = re.search(r"(?:post|treść|tresc|content)\s*:\s*(.+)$", prompt, flags=re.I)
    if marker:
        return marker.group(1).strip()
    verb = re.search(r"(?:opublikuj|publikuj|publish)\s+(.+)$", prompt, flags=re.I)
    if verb:
        text = verb.group(1).strip()
        text = re.sub(r"^(?:post|wpis)\s+", "", text, flags=re.I).strip()
        if text:
            return text
    env = mock_linkedin.load_env(env_path)
    return env.get("FAKE_LINKEDIN_POST", "Autonomiczna publikacja testowa na lokalnym mocku LinkedIn.")


def planner(goal: str, action_space: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Planner contract used by `urirun agent run`: (goal, action_space) -> steps."""
    route = next((item["uri"] for item in action_space if item.get("uri") == ROUTE), ROUTE)
    return [{
        "uri": route,
        "payload": {"post": extract_post(goal)},
        "why": "NL prompt asks for a local fake social publication",
    }]


def publish_local(
    post: str = "",
    hostname: str = "linkedin.local",
    host: str = "127.0.0.1",
    port: int = 0,
    env: str = "",
    keep_browser: bool = False,
) -> dict[str, Any]:
    """URI handler: start the local mock, log in, publish, verify."""
    env_path = autonomous_browser.ensure_env(Path(env) if env else autonomous_browser.DEFAULT_ENV)
    bind_port = int(port or autonomous_browser.free_port())
    server, _state = mock_linkedin.start_server(host, bind_port, env_path)
    try:
        return autonomous_browser.run_autonomy(
            hostname=hostname,
            port=bind_port,
            env_path=env_path,
            post=post or None,
            keep_browser=keep_browser,
        )
    finally:
        server.shutdown()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run local fake LinkedIn autonomy from an NL prompt.")
    parser.add_argument("prompt", nargs="+")
    args = parser.parse_args(argv)
    result = publish_local(post=extract_post(" ".join(args.prompt)))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
