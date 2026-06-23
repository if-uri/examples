#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Natural-language planner + URI handler for the controlled LinkedIn-shaped example.
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


ROUTE = autonomous_browser.route_uri()


def binding_document(env_path: str | Path = autonomous_browser.DEFAULT_ENV) -> dict[str, Any]:
    config = autonomous_browser.autonomy_config(env_path)
    route = autonomous_browser.route_uri(env_path)
    return {
        "version": "urirun.bindings.v2",
        "bindings": {
            route: {
                "kind": "command",
                "adapter": "local-function",
                "ref": "nl_autonomy:publish_local",
                "python": {
                    "type": "python",
                    "module": "nl_autonomy",
                    "export": "publish_local",
                },
                "inputSchema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "post": {
                            "type": "string",
                            "description": "Text to publish on the LinkedIn feed.",
                        },
                        "port": {"type": "integer", "default": config.bind_port},
                        "env": {"type": "string", "default": str(env_path)},
                        "keep_browser": {"type": "boolean", "default": False},
                    },
                },
                "policy": {"allowExecute": True},
                "meta": {
                    "label": "Publish a LinkedIn post",
                    "description": "Loads host/domain settings from .env, starts the site, publishes, and verifies the feed.",
                },
            },
        },
    }


def write_bindings(path: str | Path, env_path: str | Path = autonomous_browser.DEFAULT_ENV) -> None:
    Path(path).write_text(json.dumps(binding_document(env_path), indent=2, ensure_ascii=False), encoding="utf-8")


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
    return env.get("REAL_LINKEDIN_POST") or env.get("LINKEDIN_POST") or env.get("FAKE_LINKEDIN_POST", "Autonomiczna publikacja testowa na portalu LinkedIn.")


def planner(goal: str, action_space: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Planner contract used by `urirun agent run`: (goal, action_space) -> steps."""
    default_route = autonomous_browser.route_uri()
    route = next(
        (item["uri"] for item in action_space
         if str(item.get("uri", "")).startswith("social://")
         and str(item.get("uri", "")).endswith("/post/command/publish")),
        default_route,
    )
    return [{
        "uri": route,
        "payload": {"post": extract_post(goal)},
        "why": "NL prompt asks for a controlled social publication",
    }]


def publish_local(
    post: str = "",
    hostname: str = "",
    host: str = "",
    port: int = 0,
    env: str = "",
    keep_browser: bool = False,
) -> dict[str, Any]:
    """URI handler: start the controlled site, log in, publish, verify."""
    env_path = autonomous_browser.ensure_env(Path(env) if env else autonomous_browser.DEFAULT_ENV)
    config = autonomous_browser.autonomy_config(
        env_path,
        host=host or None,
        hostname=hostname or None,
        port=int(port) if port else None,
    )
    bind_port = config.bind_port or autonomous_browser.free_port()
    server, _state = mock_linkedin.start_server(config.bind_host, bind_port, env_path)
    try:
        return autonomous_browser.run_autonomy(
            hostname=config.browser_hostname,
            port=bind_port,
            env_path=env_path,
            post=post or None,
            keep_browser=keep_browser,
            config=config,
        )
    finally:
        server.shutdown()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run controlled LinkedIn-shaped autonomy from an NL prompt.")
    parser.add_argument("--env", default=str(autonomous_browser.DEFAULT_ENV))
    parser.add_argument("--write-bindings", help="write an env-resolved binding document and exit")
    parser.add_argument("prompt", nargs="*")
    args = parser.parse_args(argv)
    if args.write_bindings:
        write_bindings(args.write_bindings, args.env)
        return 0
    if not args.prompt:
        parser.error("prompt is required unless --write-bindings is used")
    result = publish_local(post=extract_post(" ".join(args.prompt), args.env), env=args.env)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
