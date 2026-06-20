from __future__ import annotations

import base64
import json
import os
import re
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


NODE_NAME = os.environ.get("NODE_NAME", "pc1")
HOST = os.environ.get("URI_NODE_HOST", "0.0.0.0")
PORT = int(os.environ.get("URI_NODE_PORT", "9001"))
SELENIUM_URL = os.environ.get("SELENIUM_URL", "http://pc1-browser:4444").rstrip("/")
ARTIFACT_DIR = Path(os.environ.get("ARTIFACT_DIR", "/data"))
SCREENSHOT_DIR = ARTIFACT_DIR / "screenshots"

ROUTES = [
    f"browser://{NODE_NAME}/page/command/open",
    f"browser://{NODE_NAME}/page/command/screenshot",
    f"log://{NODE_NAME}/session/command/write",
    f"log://{NODE_NAME}/session/query/recent",
]

NODE_SERVICE_ROUTES = {
    "pc1": [
        f"app://{NODE_NAME}/notes/command/add",
        f"app://{NODE_NAME}/notes/query/list",
    ],
    "pc2": [
        f"app://{NODE_NAME}/orders/command/create",
        f"app://{NODE_NAME}/orders/query/list",
    ],
    "pc3": [
        f"app://{NODE_NAME}/reports/command/render",
        f"app://{NODE_NAME}/reports/query/latest",
    ],
    "pc4": [
        f"app://{NODE_NAME}/monitor/command/check",
        f"app://{NODE_NAME}/monitor/query/status",
    ],
}

ROUTES.extend(NODE_SERVICE_ROUTES.get(NODE_NAME, []))

LOGS: list[dict[str, Any]] = []
STATE: dict[str, Any] = {"notes": [], "orders": [], "reports": [], "monitor": None}
SESSION_ID: str | None = None


def log(event: str, detail: dict[str, Any] | None = None) -> None:
    LOGS.append({"ts": time.time(), "node": NODE_NAME, "event": event, "detail": detail or {}})
    del LOGS[:-100]


def json_response(handler: BaseHTTPRequestHandler, status: int, payload: dict[str, Any]) -> None:
    body = json.dumps(payload, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Headers", "content-type")
    handler.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
    handler.end_headers()
    handler.wfile.write(body)


def route_kind(uri: str) -> str:
    return "query" if "/query/" in uri else "command"


def webdriver(method: str, path: str, payload: dict[str, Any] | None = None, timeout: float = 20.0) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"{SELENIUM_URL}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8") or "{}"
            return json.loads(raw)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8") if exc.fp else "{}"
        try:
            body = json.loads(raw or "{}")
        except json.JSONDecodeError:
            body = {"raw": raw}
        raise RuntimeError(f"webdriver {method} {path} failed: {exc.code} {body}") from exc


def wait_for_webdriver(timeout: float = 45.0) -> None:
    deadline = time.time() + timeout
    last: Exception | None = None
    while time.time() < deadline:
        try:
            webdriver("GET", "/status", timeout=3)
            return
        except Exception as exc:  # noqa: BLE001 - retry until Selenium is ready
            last = exc
            time.sleep(1)
    raise RuntimeError(f"Selenium not ready at {SELENIUM_URL}: {last}")


def ensure_session() -> str:
    global SESSION_ID
    if SESSION_ID:
        try:
            webdriver("GET", f"/session/{SESSION_ID}/url", timeout=5)
            return SESSION_ID
        except Exception:
            SESSION_ID = None

    wait_for_webdriver()
    created = webdriver(
        "POST",
        "/session",
        {
            "capabilities": {
                "alwaysMatch": {
                    "browserName": "chrome",
                    "goog:chromeOptions": {
                        "args": [
                            "--no-sandbox",
                            "--disable-dev-shm-usage",
                            "--window-size=1280,900",
                        ]
                    },
                }
            }
        },
    )
    value = created.get("value") or created
    SESSION_ID = value.get("sessionId") or created.get("sessionId")
    if not SESSION_ID:
        raise RuntimeError(f"WebDriver did not return a session id: {created}")
    return SESSION_ID


def current_url(session_id: str) -> str:
    data = webdriver("GET", f"/session/{session_id}/url")
    return str((data.get("value") if isinstance(data, dict) else "") or "")


def open_page(payload: dict[str, Any]) -> dict[str, Any]:
    url = str(payload.get("url") or "").strip()
    if not url:
        return {"ok": False, "error": "payload.url is required"}
    session_id = ensure_session()
    webdriver("POST", f"/session/{session_id}/url", {"url": url})
    log("browser.open", {"url": url})
    return {
        "ok": True,
        "node": NODE_NAME,
        "url": url,
        "currentUrl": current_url(session_id),
        "executed": True,
        "backend": "selenium-chromium-novnc",
    }


def safe_name(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9._-]+", "-", value).strip("-")
    return value or "screenshot"


def screenshot_page(payload: dict[str, Any]) -> dict[str, Any]:
    url = str(payload.get("url") or "").strip()
    output = str(payload.get("output") or "").strip()
    session_id = ensure_session()
    if url:
        webdriver("POST", f"/session/{session_id}/url", {"url": url})
    data = webdriver("GET", f"/session/{session_id}/screenshot", timeout=20)
    encoded = str(data.get("value") or "")
    if not encoded:
        return {"ok": False, "error": "webdriver returned an empty screenshot"}
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    if output:
        path = Path(output)
        if not path.is_absolute():
            path = SCREENSHOT_DIR / path
    else:
        path = SCREENSHOT_DIR / f"{safe_name(NODE_NAME)}-{int(time.time())}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(base64.b64decode(encoded))
    log("browser.screenshot", {"url": url or current_url(session_id), "path": str(path)})
    return {
        "ok": True,
        "node": NODE_NAME,
        "url": url or current_url(session_id),
        "path": str(path),
        "bytes": path.stat().st_size,
        "executed": True,
        "backend": "selenium-chromium-novnc",
    }


def app_service_call(uri: str, payload: dict[str, Any]) -> dict[str, Any]:
    if uri == f"app://{NODE_NAME}/notes/command/add":
        text = str(payload.get("text") or "").strip()
        if not text:
            return {"ok": False, "error": "payload.text is required"}
        note = {"id": len(STATE["notes"]) + 1, "text": text, "tags": payload.get("tags") or []}
        STATE["notes"].append(note)
        log("notes.add", note)
        return {"ok": True, "node": NODE_NAME, "note": note, "count": len(STATE["notes"])}

    if uri == f"app://{NODE_NAME}/notes/query/list":
        limit = int(payload.get("limit") or 20)
        return {"ok": True, "node": NODE_NAME, "notes": STATE["notes"][-limit:]}

    if uri == f"app://{NODE_NAME}/orders/command/create":
        item = str(payload.get("item") or "").strip()
        if not item:
            return {"ok": False, "error": "payload.item is required"}
        quantity = int(payload.get("quantity") or 1)
        order = {"id": len(STATE["orders"]) + 1, "item": item, "quantity": quantity, "status": "created"}
        STATE["orders"].append(order)
        log("orders.create", order)
        return {"ok": True, "node": NODE_NAME, "order": order, "count": len(STATE["orders"])}

    if uri == f"app://{NODE_NAME}/orders/query/list":
        limit = int(payload.get("limit") or 20)
        return {"ok": True, "node": NODE_NAME, "orders": STATE["orders"][-limit:]}

    if uri == f"app://{NODE_NAME}/reports/command/render":
        title = str(payload.get("title") or "Daily URI flow report").strip()
        report = {
            "id": len(STATE["reports"]) + 1,
            "title": title,
            "format": str(payload.get("format") or "html"),
            "sections": payload.get("sections") or ["summary", "timeline"],
        }
        STATE["reports"].append(report)
        log("reports.render", report)
        return {"ok": True, "node": NODE_NAME, "report": report}

    if uri == f"app://{NODE_NAME}/reports/query/latest":
        latest = STATE["reports"][-1] if STATE["reports"] else None
        return {"ok": True, "node": NODE_NAME, "report": latest}

    if uri == f"app://{NODE_NAME}/monitor/command/check":
        target = str(payload.get("target") or "ifuri.com").strip()
        status = {"target": target, "status": "ok", "latencyMs": 17, "checkedAt": time.time()}
        STATE["monitor"] = status
        log("monitor.check", status)
        return {"ok": True, "node": NODE_NAME, "status": status}

    if uri == f"app://{NODE_NAME}/monitor/query/status":
        return {"ok": True, "node": NODE_NAME, "status": STATE["monitor"]}

    return {"ok": False, "error": f"app route not found: {uri}"}


def route_call(uri: str, payload: dict[str, Any]) -> dict[str, Any]:
    if uri == f"browser://{NODE_NAME}/page/command/open":
        return open_page(payload)
    if uri == f"browser://{NODE_NAME}/page/command/screenshot":
        return screenshot_page(payload)
    if uri == f"log://{NODE_NAME}/session/command/write":
        log(str(payload.get("event") or "log.write"), payload.get("detail") if isinstance(payload.get("detail"), dict) else payload)
        return {"ok": True, "node": NODE_NAME, "count": len(LOGS)}
    if uri == f"log://{NODE_NAME}/session/query/recent":
        limit = int(payload.get("limit") or 20)
        return {"ok": True, "node": NODE_NAME, "logs": LOGS[-limit:]}
    if uri.startswith(f"app://{NODE_NAME}/"):
        return app_service_call(uri, payload)
    return {"ok": False, "error": f"route not found: {uri}", "routes": ROUTES}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"{self.address_string()} - {fmt % args}")

    def do_OPTIONS(self) -> None:  # noqa: N802
        json_response(self, 200, {"ok": True})

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/" or self.path == "/health":
            json_response(self, 200, {"ok": True, "node": NODE_NAME, "selenium": SELENIUM_URL, "routes": len(ROUTES)})
            return
        if self.path == "/routes":
            json_response(self, 200, {"ok": True, "node": NODE_NAME, "routes": [{"uri": uri, "kind": route_kind(uri)} for uri in ROUTES]})
            return
        if self.path == "/logs":
            json_response(self, 200, {"ok": True, "node": NODE_NAME, "logs": LOGS[-50:]})
            return
        json_response(self, 404, {"ok": False, "error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length") or "0")
        try:
            body = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        except json.JSONDecodeError as exc:
            json_response(self, 400, {"ok": False, "error": f"invalid JSON: {exc}"})
            return
        if self.path != "/run":
            json_response(self, 404, {"ok": False, "error": "not found"})
            return
        uri = str(body.get("uri") or "")
        payload = body.get("payload") if isinstance(body.get("payload"), dict) else {}
        started = time.perf_counter()
        try:
            result = route_call(uri, payload)
        except Exception as exc:  # noqa: BLE001 - return structured demo failure
            log("route.error", {"uri": uri, "error": str(exc)})
            result = {"ok": False, "error": str(exc), "node": NODE_NAME}
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        status = 200 if result.get("ok") else 500
        json_response(self, status, {"ok": bool(result.get("ok")), "node": NODE_NAME, "uri": uri, "elapsedMs": elapsed_ms, "result": result})


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    log("node.started", {"routes": ROUTES, "selenium": SELENIUM_URL})
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"{NODE_NAME} URI node listening on http://{HOST}:{PORT} -> {SELENIUM_URL}", flush=True)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
