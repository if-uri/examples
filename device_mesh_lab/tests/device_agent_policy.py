#!/usr/bin/env python3
from __future__ import annotations

import pathlib
import tempfile

import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from device_agent import DeviceAgent, parse_browser_targets  # noqa: E402


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="urirun-agent-policy-") as tmp:
        default_agent = DeviceAgent(name="desktop", role="test", root=pathlib.Path(tmp))
        default_routes = {route["uri"]: route for route in default_agent.routes()}
        default_browser_route = default_routes["browser://desktop/page/command/open"]
        assert default_browser_route["enabled"] is True
        assert default_browser_route["policy"]["allowBrowser"] is True
        assert default_browser_route["policy"]["backend"] == "novnc"
        assert default_browser_route["policy"]["target"]["pc"] == "pc1"
        assert default_agent.device_card()["browserBackend"] == "novnc"

        parsed_targets = parse_browser_targets("desktop=pc9@http://127.0.0.1:9909")
        assert parsed_targets["desktop"] == {"pc": "pc9", "apiUrl": "http://127.0.0.1:9909"}

        agent = DeviceAgent(name="desktop", role="test", root=pathlib.Path(tmp), allow_browser=False)
        result = agent.dispatch("browser://desktop/page/command/open", {"url": "https://example.com/"})
        assert result["ok"] is False
        assert result["error"]["type"] == "policy"
        assert result["result"]["executed"] is False
        assert result["result"]["allowBrowser"] is False
        assert result["result"]["backend"] == "novnc"

        routes = {route["uri"]: route for route in agent.routes()}
        browser_route = routes["browser://desktop/page/command/open"]
        assert browser_route["enabled"] is False
        assert browser_route["policy"]["allowBrowser"] is False
        assert browser_route["policy"]["backend"] == "novnc"

    print("PASS device_agent_policy")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
