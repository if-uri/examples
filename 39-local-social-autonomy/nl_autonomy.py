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
import unicodedata
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import autonomous_browser
import mock_linkedin


ROUTE = autonomous_browser.route_uri()


def binding_document(env_path: str | Path = autonomous_browser.DEFAULT_ENV) -> dict[str, Any]:
    import urllib.parse
    config = autonomous_browser.autonomy_config(env_path)
    route = autonomous_browser.route_uri(env_path)
    parsed = urllib.parse.urlparse(route)
    route_session = f"social://{parsed.netloc}/session/query/active"
    route_capture = f"social://{parsed.netloc}/scout/command/capture"
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
            route_session: {
                "kind": "query",
                "adapter": "local-function",
                "ref": "nl_autonomy:check_active_session",
                "python": {
                    "type": "python",
                    "module": "nl_autonomy",
                    "export": "check_active_session",
                },
                "inputSchema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "ports": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "List of debug ports to probe."
                        },
                        "env": {
                            "type": "string",
                            "default": str(env_path),
                            "description": "Path to .env with LI_DEBUG_PORT settings."
                        }
                    },
                },
                "policy": {"allowExecute": True},
                "meta": {
                    "label": "Check for active LinkedIn browser session",
                    "description": "Probes debugging ports to find a browser tab containing a logged-in LinkedIn session."
                }
            },
            route_capture: {
                "kind": "command",
                "adapter": "local-function",
                "ref": "nl_autonomy:scout_capture",
                "python": {
                    "type": "python",
                    "module": "nl_autonomy",
                    "export": "scout_capture",
                },
                "inputSchema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "index": {
                            "type": "integer",
                            "default": 1,
                            "description": "Index of the post to capture (1-based)."
                        },
                        "env": {
                            "type": "string",
                            "default": str(env_path),
                            "description": "Path to .env file."
                        }
                    },
                },
                "policy": {"allowExecute": True},
                "meta": {
                    "label": "Capture LinkedIn post by index",
                    "description": "Attaches to the active browser session, extracts the feed, and appends the post at the given index to the captures file."
                }
            }
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


def _nl_key(text: str) -> str:
    """Normalize Polish diacritics/typos enough for the tiny keyword planner."""
    plain = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return " ".join(plain.lower().split())


def planner(goal: str, action_space: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Planner contract used by `urirun agent run`: (goal, action_space) -> steps."""
    goal_lower = _nl_key(goal)
    if any(keyword in goal_lower for keyword in (
        "session", "sesja", "sejsja", "zalogowan", "przegladark", "check", "sprawdz", "query"
    )):
        route = next(
            (item["uri"] for item in action_space
             if str(item.get("uri", "")).startswith("social://")
             and str(item.get("uri", "")).endswith("/session/query/active")),
            None,
        )
        if route:
            return [{
                "uri": route,
                "payload": {},
                "why": "NL prompt asks to check the active LinkedIn session or browser",
            }]

    if any(keyword in goal_lower for keyword in ("scout", "capture", "zapisz", "feed")):
        route = next(
            (item["uri"] for item in action_space
             if str(item.get("uri", "")).startswith("social://")
             and str(item.get("uri", "")).endswith("/scout/command/capture")),
            None,
        )
        if route:
            count = 10
            match = re.search(r"(\d+)", goal_lower)
            if match:
                count = int(match.group(1))
            steps = []
            for i in range(count):
                steps.append({
                    "uri": route,
                    "payload": {"index": i + 1},
                    "why": f"Krokowo zapisujemy post nr {i + 1} z LinkedIn feed",
                })
            return steps

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


def check_active_session(
    ports: list[int] | None = None,
    env: str = "",
) -> dict[str, Any]:
    """Check if any running browser has an active logged-in LinkedIn session."""
    import scout
    import urllib.parse
    env_path = Path(env) if env else scout.DEFAULT_ENV
    env_dict = mock_linkedin.load_env(env_path) if env_path.exists() else {}

    if not ports:
        port_val = env_dict.get("LI_DEBUG_PORT")
        ports = [int(port_val)] if port_val else [9222]

    checked = []
    for port in ports:
        try:
            cdp = scout.AttachCDP(f"http://127.0.0.1:{port}")
            cdp.connect(prefer_url_contains="linkedin.com")
            try:
                href = cdp.eval("location.href") or ""
                title = cdp.eval("document.title") or ""

                # Check if we are on LinkedIn and logged in
                is_logged_in = cdp.eval("""(() => {
                  const path = location.pathname;
                  const hasFeed = path.includes('/feed') || path.includes('/in/') || path.includes('/my-items/');
                  const noLoginForm = !document.querySelector('form[action*="login"]');
                  return hasFeed && noLoginForm;
                })()""")

                if is_logged_in:
                    return {
                        "ok": True,
                        "found": True,
                        "port": port,
                        "url": href,
                        "title": title,
                    }
                checked.append({
                    "port": port,
                    "url": href,
                    "title": title,
                    "status": "No active logged-in session found on this port."
                })
            finally:
                cdp.close()
        except Exception as exc:
            checked.append({"port": port, "error": str(exc)})

    return {
        "ok": True,
        "found": False,
        "checked_ports": ports,
        "details": checked
    }


def scout_capture(index: int = 1, env: str = "") -> dict[str, Any]:
    """Capture a single post from the active LinkedIn feed browser without logging in."""
    import scout
    import time
    env_path = Path(env) if env else scout.DEFAULT_ENV
    config = scout.scout_config(env_path)
    cdp = scout.AttachCDP(config.base)
    cdp.connect(prefer_url_contains="linkedin.com")
    try:
        # Check if we are on feed, if not navigate
        href = cdp.eval("location.href") or ""
        if "linkedin.com/feed" not in href:
            cdp.command("Page.navigate", {"url": "https://www.linkedin.com/feed/"})
            time.sleep(3.0)

        # Scroll down slightly to trigger loading more posts or ensure we are positioned
        cdp.scroll_down(config.scroll_delay)

        posts = scout.extract_posts(cdp)
        if not posts or len(posts) < index:
            # Scroll more to find it
            for _ in range(3):
                cdp.scroll_down(config.scroll_delay)
                posts = scout.extract_posts(cdp)
                if len(posts) >= index:
                    break

        if not posts:
            return {"ok": False, "error": "No posts found on page"}

        # Target the post at index - 1 (clamped to available posts)
        target_idx = min(index - 1, len(posts) - 1)
        post = posts[target_idx]

        # Format and write to captures
        md = scout.to_markdown([post], {"feed": href})
        out_path = scout.CAPTURES
        scout.write_captures(out_path, md)

        return {
            "ok": True,
            "index": index,
            "captured_post": {
                "author": post.get("author"),
                "text": (post.get("text") or "")[:100] + "...",
                "url": post.get("url")
            },
            "out": str(out_path)
        }
    finally:
        cdp.close()


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
