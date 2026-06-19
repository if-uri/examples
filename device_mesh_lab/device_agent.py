from __future__ import annotations

import json
import os
import platform
import shlex
import socket
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from mesh_env import check_auth, load_env, read_json, send_json


def object_schema(properties: dict, required: list[str] | None = None) -> dict:
    schema = {
        "type": "object",
        "properties": properties,
        "additionalProperties": False,
    }
    if required:
        schema["required"] = required
    return schema


DEFAULT_BROWSER_TARGETS = {
    "desktop": {"pc": "pc1", "apiUrl": "http://127.0.0.1:9001"},
    "laptop": {"pc": "pc2", "apiUrl": "http://127.0.0.1:9002"},
    "pc1": {"pc": "pc1", "apiUrl": "http://127.0.0.1:9001"},
    "pc2": {"pc": "pc2", "apiUrl": "http://127.0.0.1:9002"},
    "pc3": {"pc": "pc3", "apiUrl": "http://127.0.0.1:9003"},
    "pc4": {"pc": "pc4", "apiUrl": "http://127.0.0.1:9004"},
}


def default_browser_targets() -> dict[str, dict[str, str]]:
    return {name: dict(target) for name, target in DEFAULT_BROWSER_TARGETS.items()}


def browser_target_from_spec(name: str, spec: str) -> dict[str, str]:
    if "@" in spec:
        pc_name, api_url = spec.split("@", 1)
    else:
        pc_name, api_url = name, spec
    return {"pc": pc_name.strip() or name, "apiUrl": api_url.strip().rstrip("/")}


def parse_browser_targets(value: str | None = None) -> dict[str, dict[str, str]]:
    raw = (value if value is not None else os.getenv("URIRUN_MESH_BROWSER_TARGETS", "")).strip()
    targets = default_browser_targets()
    if not raw:
        return targets

    if raw.startswith("{"):
        parsed = json.loads(raw)
        for name, spec in parsed.items():
            key = str(name).strip()
            if not key:
                continue
            if isinstance(spec, str):
                targets[key] = browser_target_from_spec(key, spec)
            elif isinstance(spec, dict):
                pc_name = str(spec.get("pc") or spec.get("name") or key).strip()
                api_url = str(spec.get("apiUrl") or spec.get("api") or spec.get("url") or "").strip().rstrip("/")
                if api_url:
                    targets[key] = {"pc": pc_name or key, "apiUrl": api_url}
        return targets

    for item in raw.split(","):
        if not item.strip() or "=" not in item:
            continue
        name, spec = item.split("=", 1)
        key = name.strip()
        if key:
            targets[key] = browser_target_from_spec(key, spec)
    return targets


def build_novnc_browser_command(url: str) -> str:
    quoted_url = shlex.quote(url)
    return "\n".join(
        [
            f"URL={quoted_url}",
            'export DISPLAY="${DISPLAY:-:1}"',
            "for BROWSER in firefox-esr firefox chromium chromium-browser google-chrome x-www-browser; do",
            '  if command -v "$BROWSER" >/dev/null 2>&1; then',
            '    nohup "$BROWSER" "$URL" >/tmp/urirun-browser.log 2>&1 &',
            '    echo "started $BROWSER $URL"',
            "    exit 0",
            "  fi",
            "done",
            (
                "printf 'No browser installed in this noVNC PC.\\nURL: %s\\n"
                "Install firefox-esr or chromium in the noVNC image.\\n' "
                '"$URL" > /tmp/urirun-browser-request.txt'
            ),
            "if command -v xterm >/dev/null 2>&1; then",
            (
                "  nohup xterm -geometry 120x24+120+120 -title 'browser:// missing' "
                "-e bash -lc 'cat /tmp/urirun-browser-request.txt; echo; exec bash' "
                ">/tmp/urirun-browser-missing.log 2>&1 &"
            ),
            "  cat /tmp/urirun-browser-request.txt",
            "  exit 42",
            "fi",
            "cat /tmp/urirun-browser-request.txt >&2",
            "exit 43",
        ]
    )


class DeviceAgent:
    def __init__(
        self,
        name: str,
        role: str,
        root: Path,
        allow_browser: bool = True,
        browser_backend: str = "novnc",
        browser_targets: dict[str, dict[str, str]] | None = None,
    ):
        self.name = name
        self.role = role
        self.root = root
        self.allow_browser = allow_browser
        self.browser_backend = (browser_backend or "novnc").strip().lower()
        self.browser_targets = browser_targets or default_browser_targets()
        self.log_file = root / "logs" / f"{name}.jsonl"
        self.notes_file = root / "notes" / f"{name}.jsonl"

    def log(self, event: str, detail=None) -> dict:
        record = {
            "at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "device": self.name,
            "role": self.role,
            "event": event,
            "detail": detail or {},
        }
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        with self.log_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        print(json.dumps(record, ensure_ascii=False), flush=True)
        return record

    def recent_logs(self, limit: int = 30) -> list[dict]:
        if not self.log_file.exists():
            return []
        output = []
        for line in self.log_file.read_text(encoding="utf-8").splitlines()[-limit:]:
            try:
                output.append(json.loads(line))
            except json.JSONDecodeError:
                output.append({"raw": line})
        return output

    def append_note(self, text: str) -> dict:
        record = {
            "at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "device": self.name,
            "text": text,
        }
        self.notes_file.parent.mkdir(parents=True, exist_ok=True)
        with self.notes_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        self.log("note.written", {"text": text})
        return record

    def routes(self) -> list[dict]:
        target = self.name
        browser_target = self.browser_target()
        browser_adapter = "browser-host" if self.browser_backend == "host" else "browser-novnc"
        return [
            {
                "uri": f"device://{target}/capabilities/query/list",
                "kind": "query",
                "adapter": "device-agent",
                "safe": True,
                "title": "List URI capabilities on this device",
                "inputSchema": object_schema({}),
            },
            {
                "uri": f"device://{target}/installable/query/list",
                "kind": "query",
                "adapter": "device-agent",
                "safe": True,
                "title": "List capabilities that can be installed here",
                "inputSchema": object_schema({}),
            },
            {
                "uri": f"env://{target}/runtime/query/health",
                "kind": "query",
                "adapter": "device-agent",
                "safe": True,
                "title": "Read runtime health",
                "inputSchema": object_schema({}),
            },
            {
                "uri": f"proc://{target}/process/query/list",
                "kind": "query",
                "adapter": "ps",
                "safe": True,
                "title": "List running processes",
                "inputSchema": object_schema({"limit": {"type": "integer", "default": 12}}),
            },
            {
                "uri": f"proc://{target}/process/query/find",
                "kind": "query",
                "adapter": "ps",
                "safe": True,
                "title": "Find processes by command name",
                "inputSchema": object_schema({
                    "name": {"type": "string"},
                    "limit": {"type": "integer", "default": 12},
                }, ["name"]),
            },
            {
                "uri": f"shell://{target}/command/uname",
                "kind": "command",
                "adapter": "safe-argv",
                "safe": True,
                "title": "Run uname -a",
                "inputSchema": object_schema({}),
            },
            {
                "uri": f"shell://{target}/command/date",
                "kind": "command",
                "adapter": "safe-argv",
                "safe": True,
                "title": "Read device date",
                "inputSchema": object_schema({}),
            },
            {
                "uri": f"shell://{target}/command/which",
                "kind": "query",
                "adapter": "safe-argv",
                "safe": True,
                "title": "Check whether a binary exists",
                "inputSchema": object_schema({"binary": {"type": "string"}}, ["binary"]),
            },
            {
                "uri": f"browser://{target}/page/command/open",
                "kind": "command",
                "adapter": browser_adapter,
                "safe": True,
                "enabled": self.allow_browser,
                "policy": {
                    "allowBrowser": self.allow_browser,
                    "backend": self.browser_backend,
                    "target": browser_target,
                },
                "title": "Open a URL on the mapped noVNC device when browser execution is enabled",
                "inputSchema": object_schema({"url": {"type": "string"}}, ["url"]),
            },
            {
                "uri": f"note://{target}/operator/command/write",
                "kind": "command",
                "adapter": "jsonl",
                "safe": True,
                "title": "Write an operator note",
                "inputSchema": object_schema({"text": {"type": "string"}}, ["text"]),
            },
            {
                "uri": f"log://{target}/session/command/write",
                "kind": "command",
                "adapter": "jsonl",
                "safe": True,
                "title": "Write structured device log",
                "inputSchema": object_schema({
                    "event": {"type": "string"},
                    "detail": {"type": "object", "default": {}},
                }, ["event"]),
            },
            {
                "uri": f"log://{target}/session/query/recent",
                "kind": "query",
                "adapter": "jsonl",
                "safe": True,
                "title": "Read recent device logs",
                "inputSchema": object_schema({"limit": {"type": "integer", "default": 20}}),
            },
        ]

    def device_card(self) -> dict:
        return {
            "name": self.name,
            "role": self.role,
            "hostname": socket.gethostname(),
            "platform": platform.platform(),
            "python": platform.python_version(),
            "allowBrowser": self.allow_browser,
            "browserBackend": self.browser_backend,
            "browserTarget": self.browser_target(),
            "routeCount": len(self.routes()),
        }

    def browser_target(self) -> dict[str, str] | None:
        return self.browser_targets.get(self.name) or self.browser_targets.get(self.role)

    def installable(self) -> list[dict]:
        return [
            {
                "capability": "gui-kvm",
                "status": "not-installed",
                "routes": [
                    f"kvm://{self.name}/monitor/primary/query/screenshot",
                    f"him://{self.name}/keyboard/command/type-text",
                ],
                "installHint": "Install xdotool/gnome-screenshot or a noVNC desktop agent, then expose these URI routes.",
            },
            {
                "capability": "rdp-control",
                "status": "not-installed",
                "routes": [f"rdp://{self.name}/display/query/status"],
                "installHint": "Run an RDP/noVNC adapter and register rdp:// routes in this agent.",
            },
            {
                "capability": "ocr-vision",
                "status": "not-installed",
                "routes": [f"ocr://{self.name}/image/latest/query/text"],
                "installHint": "Add an OCR worker that reads latest screenshots and publishes ocr:// routes.",
            },
            {
                "capability": "stt-voice",
                "status": "not-installed",
                "routes": [f"stt://{self.name}/session/main/query/transcript"],
                "installHint": "Add an STT adapter or browser microphone capture service.",
            },
        ]

    def processes(self, limit: int = 12, name: str | None = None) -> list[dict]:
        command = ["ps", "-eo", "pid=,comm=,pcpu=,pmem=", "--sort=-pcpu"]
        proc = subprocess.run(command, text=True, capture_output=True, timeout=5)
        rows = []
        for line in proc.stdout.splitlines():
            parts = line.split(None, 3)
            if len(parts) < 4:
                continue
            pid, command_name, cpu, mem = parts
            if name and name.lower() not in command_name.lower():
                continue
            rows.append({"pid": int(pid), "command": command_name, "cpu": cpu, "mem": mem})
            if len(rows) >= limit:
                break
        return rows

    def safe_command(self, name: str, payload: dict) -> dict:
        commands = {
            "uname": ["uname", "-a"],
            "date": ["date", "-Is"],
            "which": ["which", str(payload.get("binary", ""))],
        }
        if name not in commands:
            return {"ok": False, "error": {"type": "route", "message": f"unknown safe command: {name}"}}
        if name == "which" and not payload.get("binary"):
            return {"ok": False, "error": {"type": "payload", "message": "binary is required"}}
        proc = subprocess.run(commands[name], text=True, capture_output=True, timeout=5)
        result = {"argv": commands[name], "returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}
        self.log("shell.safe", result)
        return {"ok": proc.returncode == 0, "result": result}

    def open_browser_on_host(self, url: str, detail: dict) -> dict:
        detail["executed"] = webbrowser.open(url, new=2)
        if not detail["executed"]:
            detail["reason"] = "webbrowser.open returned False"
            self.log("browser.open.failed", detail)
            return {
                "ok": False,
                "error": {"type": "runtime", "message": "Python webbrowser could not open the URL"},
                "result": detail,
            }
        self.log("browser.open", detail)
        return {"ok": True, "result": detail}

    def open_browser_in_novnc(self, url: str, detail: dict) -> dict:
        target = self.browser_target()
        if not target:
            detail["reason"] = f"no noVNC browser target mapped for {self.name}"
            self.log("browser.open.failed", detail)
            return {
                "ok": False,
                "error": {
                    "type": "browser-target",
                    "message": (
                        "No noVNC target is mapped for this device. Set "
                        "URIRUN_MESH_BROWSER_TARGETS, for example "
                        "desktop=pc1@http://127.0.0.1:9001."
                    ),
                },
                "result": detail,
            }

        pc_name = target["pc"]
        api_url = target["apiUrl"].rstrip("/")
        run_uri = f"pc://{pc_name}/terminal/command/run"
        command = build_novnc_browser_command(url)
        request_body = {"uri": run_uri, "payload": {"command": command}}
        detail.update({"target": target, "runUri": run_uri})

        try:
            request = urllib.request.Request(
                f"{api_url}/run",
                data=json.dumps(request_body).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=12) as response:
                response_body = json.loads(response.read().decode("utf-8") or "{}")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", "replace")
            try:
                response_body = json.loads(body)
            except json.JSONDecodeError:
                response_body = {"ok": False, "error": body}
            detail.update({"response": response_body, "status": exc.code})
            self.log("browser.open.failed", detail)
            return {
                "ok": False,
                "error": {"type": "novnc-api", "message": f"noVNC API returned HTTP {exc.code}"},
                "result": detail,
            }
        except urllib.error.URLError as exc:
            detail["reason"] = str(exc)
            self.log("browser.open.failed", detail)
            return {
                "ok": False,
                "error": {"type": "novnc-api", "message": f"Could not reach noVNC API at {api_url}: {exc}"},
                "result": detail,
            }

        terminal_result = response_body.get("result") or {}
        returncode = terminal_result.get("returncode")
        detail.update({"response": response_body, "returncode": returncode, "executed": returncode == 0})
        if returncode == 0:
            self.log("browser.open", detail)
            return {"ok": True, "result": detail}

        error_message = "Browser command was delegated to noVNC, but did not complete successfully."
        if returncode == 42:
            error_message = "The noVNC computer received the URI command, but no browser is installed there."
        self.log("browser.open.failed", detail)
        return {"ok": False, "error": {"type": "novnc-browser", "message": error_message}, "result": detail}

    def open_browser(self, url: str) -> dict:
        detail = {
            "url": url,
            "executed": False,
            "allowBrowser": self.allow_browser,
            "backend": self.browser_backend,
        }
        if not self.allow_browser:
            detail["reason"] = "browser execution is disabled by URIRUN_MESH_ALLOW_BROWSER"
            self.log("browser.blocked", detail)
            return {
                "ok": False,
                "error": {
                    "type": "policy",
                    "message": (
                        "browser:// execution is disabled. Set "
                        "URIRUN_MESH_ALLOW_BROWSER=1 on this device agent and restart it."
                    ),
                },
                "result": detail,
            }
        if self.browser_backend == "host":
            return self.open_browser_on_host(url, detail)
        return self.open_browser_in_novnc(url, detail)

    def dispatch(self, uri: str, payload: dict | None = None) -> dict:
        payload = payload or {}
        parsed = urllib.parse.urlparse(uri)
        target = parsed.netloc
        segments = [part for part in parsed.path.split("/") if part]
        if target != self.name:
            return {"ok": False, "error": {"type": "target", "message": f"{self.name} cannot own {target}"}}

        if parsed.scheme == "device" and segments == ["capabilities", "query", "list"]:
            return {"ok": True, "result": {"device": self.device_card(), "routes": self.routes()}}
        if parsed.scheme == "device" and segments == ["installable", "query", "list"]:
            return {"ok": True, "result": {"installable": self.installable()}}
        if parsed.scheme == "env" and segments == ["runtime", "query", "health"]:
            return {"ok": True, "result": self.device_card()}
        if parsed.scheme == "proc" and segments == ["process", "query", "list"]:
            return {"ok": True, "result": {"processes": self.processes(int(payload.get("limit", 12)))}}
        if parsed.scheme == "proc" and segments == ["process", "query", "find"]:
            return {"ok": True, "result": {"processes": self.processes(int(payload.get("limit", 12)), str(payload["name"]))}}
        if parsed.scheme == "shell" and segments[:1] == ["command"] and len(segments) == 2:
            return self.safe_command(segments[1], payload)
        if parsed.scheme == "browser" and segments == ["page", "command", "open"]:
            return self.open_browser(str(payload["url"]))
        if parsed.scheme == "note" and segments == ["operator", "command", "write"]:
            return {"ok": True, "result": self.append_note(str(payload["text"]))}
        if parsed.scheme == "log" and segments == ["session", "command", "write"]:
            return {"ok": True, "result": self.log(str(payload["event"]), payload.get("detail") or {})}
        if parsed.scheme == "log" and segments == ["session", "query", "recent"]:
            return {"ok": True, "result": {"logs": self.recent_logs(int(payload.get("limit", 20)))}}
        return {"ok": False, "error": {"type": "route", "message": f"unknown URI: {uri}"}}

    def handler(self):
        agent = self

        class Handler(BaseHTTPRequestHandler):
            def do_OPTIONS(self):
                send_json(self, 200, {"ok": True})

            def _authorized(self) -> bool:
                if check_auth(self.headers):
                    return True
                send_json(self, 401, {"ok": False, "error": "unauthorized"})
                return False

            def do_GET(self):
                if not self._authorized():
                    return
                if self.path == "/health":
                    send_json(self, 200, {"ok": True, "device": agent.device_card()})
                    return
                if self.path == "/device":
                    send_json(self, 200, {"ok": True, "device": agent.device_card(), "installable": agent.installable()})
                    return
                if self.path == "/routes":
                    send_json(self, 200, {"ok": True, "device": agent.device_card(), "routes": agent.routes()})
                    return
                if self.path == "/processes":
                    send_json(self, 200, {"ok": True, "device": agent.device_card(), "processes": agent.processes(18)})
                    return
                if self.path == "/logs":
                    send_json(self, 200, {"ok": True, "logs": agent.recent_logs(50)})
                    return
                send_json(self, 404, {"ok": False, "error": "not found"})

            def do_POST(self):
                if not self._authorized():
                    return
                if self.path != "/run":
                    send_json(self, 404, {"ok": False, "error": "not found"})
                    return
                try:
                    body = read_json(self)
                    result = agent.dispatch(str(body["uri"]), body.get("payload") or {})
                    result["service"] = agent.name
                    send_json(self, 200 if result.get("ok") else 400, result)
                except Exception as exc:  # noqa: BLE001 - device agent reports route errors as JSON.
                    agent.log("agent.error", {"message": str(exc)})
                    send_json(self, 500, {"ok": False, "error": {"type": type(exc).__name__, "message": str(exc)}})

            def log_message(self, fmt, *args):
                agent.log("http.request", {"message": fmt % args})

        return Handler

    def serve(self, host: str, port: int) -> ThreadingHTTPServer:
        server = ThreadingHTTPServer((host, port), self.handler())
        self.log("agent.started", {"host": host, "port": port, "routes": [route["uri"] for route in self.routes()]})
        return server


def make_agent_from_env() -> DeviceAgent:
    load_env()
    name = os.getenv("URIRUN_MESH_DEVICE_NAME", socket.gethostname()).strip() or socket.gethostname()
    role = os.getenv("URIRUN_MESH_DEVICE_ROLE", "workstation").strip() or "workstation"
    root = Path(os.getenv("URIRUN_MESH_STATE_DIR", ".run")).resolve()
    allow_browser = os.getenv("URIRUN_MESH_ALLOW_BROWSER", "1") == "1"
    browser_backend = os.getenv("URIRUN_MESH_BROWSER_BACKEND", "novnc")
    return DeviceAgent(
        name=name,
        role=role,
        root=root,
        allow_browser=allow_browser,
        browser_backend=browser_backend,
        browser_targets=parse_browser_targets(),
    )


def main() -> int:
    agent = make_agent_from_env()
    host = os.getenv("URIRUN_MESH_AGENT_HOST", "0.0.0.0")
    port = int(os.getenv("URIRUN_MESH_AGENT_PORT", "8765"))
    server = agent.serve(host, port)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
