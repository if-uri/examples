#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path


BASE = Path("/lab/generated")
DB = BASE / "host.db"
PROJECT = BASE / "planfile-project"
SCREENSHOTS = BASE / "screenshots"
REGISTRY = BASE / "connectors-registry.json"
POLICY = BASE / "connectors-policy.json"
IFURI_URL = "http://ifuri-site/"


def run(args: list[str], *, check: bool = True, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(args, text=True, capture_output=True, env={**os.environ, **(env or {})})
    if check and result.returncode != 0:
        raise RuntimeError(
            "command failed\n"
            f"args={args!r}\n"
            f"exit={result.returncode}\n"
            f"stdout={result.stdout}\n"
            f"stderr={result.stderr}"
        )
    return result


def run_json(args: list[str], *, env: dict[str, str] | None = None) -> dict:
    result = run(args, env=env)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"expected JSON from {args!r}, got: {result.stdout}") from exc


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def fetch_catalog() -> dict:
    base = os.environ.get("CONNECT_BASE_URL", "https://connect.ifuri.com").rstrip("/")
    with urllib.request.urlopen(f"{base}/connectors.json", timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def emit_http_check_bindings() -> None:
    code = """
import json
from urirun_connector_http_check import urirun_bindings
print(json.dumps(urirun_bindings(), indent=2))
""".strip()
    result = run(["python3", "-c", code])
    (BASE / "http-check-bindings.json").write_text(result.stdout, encoding="utf-8")


def emit_time_tools_bindings() -> None:
    code = """
import json
from urirun_connector_time_tools import urirun_bindings
print(json.dumps(urirun_bindings(), indent=2))
""".strip()
    result = run(["python3", "-c", code])
    (BASE / "time-tools-bindings.json").write_text(result.stdout, encoding="utf-8")


def build_registry() -> None:
    BASE.mkdir(parents=True, exist_ok=True)
    PROJECT.mkdir(parents=True, exist_ok=True)
    SCREENSHOTS.mkdir(parents=True, exist_ok=True)
    write_json(POLICY, {"execute": {"allow": ["**"]}})

    emit_http_check_bindings()
    emit_time_tools_bindings()
    run(["urirun", "host", "data", "bindings", "--target", "host", "--db", str(DB), "--out", str(BASE / "data-bindings.json")])
    run([
        "urirun",
        "host",
        "monitor",
        "bindings",
        "--target",
        "host",
        "--db",
        str(DB),
        "--project",
        str(PROJECT),
        "--screenshot-dir",
        str(SCREENSHOTS),
        "--out",
        str(BASE / "monitor-bindings.json"),
    ])
    run(["urirun", "host", "task", "bindings", "--target", "host", "--project", str(PROJECT), "--out", str(BASE / "task-bindings.json")])
    run([
        "urirun",
        "compile",
        str(BASE / "http-check-bindings.json"),
        str(BASE / "time-tools-bindings.json"),
        str(BASE / "data-bindings.json"),
        str(BASE / "monitor-bindings.json"),
        str(BASE / "task-bindings.json"),
        "--out",
        str(REGISTRY),
        "--on-conflict",
        "keep",
    ])
    run(["urirun", "validate", str(BASE / "http-check-bindings.json")])
    run(["urirun", "validate", str(BASE / "time-tools-bindings.json")])
    run(["urirun", "validate", str(BASE / "data-bindings.json")])
    run(["urirun", "validate", str(BASE / "monitor-bindings.json")])
    run(["urirun", "validate", str(BASE / "task-bindings.json")])


def uri_run(uri: str, payload: dict, *, execute: bool = True) -> dict:
    args = ["urirun", "run", uri, str(REGISTRY), "--payload", json.dumps(payload)]
    if execute:
        args.extend(["--execute", "--allow", "**"])
    return run_json(args)


def result_ok(envelope: dict) -> bool:
    return bool(envelope.get("ok"))


def run_connector_routes() -> dict:
    results: dict[str, dict] = {}

    results["sqlite_dataset_create"] = uri_run(
        "data://host/dataset/command/create",
        {
            "db": str(DB),
            "name": "domains",
            "description": "Domains checked by connector Docker E2E",
            "schema": {"type": "object", "properties": {"domain": {"type": "string"}, "url": {"type": "string"}}, "additionalProperties": True},
        },
    )
    results["sqlite_record_upsert"] = uri_run(
        "data://host/record/command/upsert",
        {
            "db": str(DB),
            "dataset": "domains",
            "key": "ifuri-site",
            "data": {"domain": "ifuri-site", "url": IFURI_URL, "expected_status": 200},
            "source_uri": "httpcheck://host/http/query/status",
            "confidence": 1.0,
        },
    )
    results["sqlite_search"] = uri_run("data://host/records/query/search", {"db": str(DB), "dataset": "domains", "query": "ifuri", "limit": 10})
    results["artifact_register"] = uri_run(
        "artifact://host/artifact/command/register",
        {
            "db": str(DB),
            "kind": "html-page",
            "uri": "artifact://host/page/ifuri-site",
            "path": "/lab/generated/ifuri-test-page.html",
            "meta": {"source": IFURI_URL},
        },
    )
    results["artifact_list"] = uri_run("artifact://host/artifacts/query/list", {"db": str(DB), "kind": "html-page", "limit": 10})
    results["check_add"] = uri_run(
        "check://host/check/command/add",
        {
            "db": str(DB),
            "subject": "ifuri-site",
            "check_uri": "httpcheck://host/http/query/status",
            "status": "ok",
            "result": {"url": IFURI_URL, "status": 200},
        },
    )
    results["check_recent"] = uri_run("check://host/checks/query/recent", {"db": str(DB), "subject": "ifuri-site", "limit": 10})
    results["log_write"] = uri_run("log://host/daily/command/write", {"db": str(DB), "stream": "daily", "event": "connector.e2e.started", "detail": {"url": IFURI_URL}})
    results["http_check"] = uri_run("httpcheck://host/http/query/status", {"url": IFURI_URL, "expectStatus": 200, "timeout": 5})
    results["time_now"] = uri_run("time://host/clock/query/now", {"timezone": "UTC", "output": "iso"})
    results["domain_monitor_http"] = uri_run("monitor://host/http/query/status", {"url": IFURI_URL, "expected_status": 200, "timeout": 5})
    results["domain_monitor_dns_current"] = uri_run("dns://host/records/query/current", {"domain": "ifuri-site", "record_types": ["A"]})
    results["domain_flow"] = uri_run(
        "flow://host/domain/command/check",
        {
            "db": str(DB),
            "project": str(PROJECT),
            "domain": "ifuri-site",
            "url": IFURI_URL,
            "expected": {},
            "screenshot_when": "never",
            "create_repair_ticket": False,
            "timeout": 5,
        },
    )
    mock_records = [{"Name": "@", "Type": "A", "Address": "127.0.0.1", "TTL": "60"}]
    desired_records = [{"Name": "@", "Type": "A", "Address": "127.0.0.2", "TTL": "60"}]
    results["namecheap_plan"] = uri_run(
        "dns://host/records/command/plan",
        {"domain": "example.test", "mock_records": mock_records, "desired_records": desired_records},
    )
    results["namecheap_backup"] = uri_run(
        "dns://host/records/command/backup",
        {"db": str(DB), "domain": "example.test", "mock_records": mock_records, "backup_dir": str(BASE / "dns-backups")},
    )
    backup_uri = ((results["namecheap_backup"].get("result") or {}).get("backup") or {}).get("uri")
    results["namecheap_apply_mock"] = uri_run(
        "dns://host/records/command/apply",
        {
            "domain": "example.test",
            "confirm": True,
            "backup_uri": backup_uri or "artifact://host/namecheap/dns-backup/example.test/mock",
            "current_records": mock_records,
            "desired_records": desired_records,
            "mock_apply": True,
        },
    )
    results["task_create"] = uri_run(
        "task://host/ticket/command/create",
        {
            "project": str(PROJECT),
            "name": "Connector Docker E2E ticket",
            "description": "Created through task:// URI in docker connector lab",
            "queue": "e2e",
            "label": ["connector", "docker"],
        },
    )
    ticket_id = ((results["task_create"].get("result") or {}).get("ticket") or {}).get("id")
    results["task_list"] = uri_run("task://host/tickets/query/list", {"project": str(PROJECT), "sprint": "current", "queue": "e2e"})
    results["planfile_dsl"] = uri_run("planfile://host/dsl/command/run", {"project": str(PROJECT), "command": "list tickets"})
    if ticket_id:
        results["task_complete"] = uri_run(
            "task://host/ticket/command/complete",
            {"project": str(PROJECT), "ticket_id": ticket_id, "note": "Docker connector E2E completed", "result": {"ok": True}},
        )
    results["logs_recent"] = uri_run("log://host/logs/query/recent", {"db": str(DB), "limit": 20})
    return results


def project_mcp_a2a() -> dict:
    tools = run_json(["python3", "-m", "urirun.v2_mcp", "tools", str(REGISTRY)])
    card = run_json(["python3", "-m", "urirun.v2_mcp", "card", str(REGISTRY), "--name", "connector-docker-e2e", "--url", "http://host:8765"])
    return {"tools": tools, "card": card}


def test_grpc_transport() -> dict:
    server = subprocess.Popen(
        [
            "python3",
            "-m",
            "urirun.v2_grpc",
            "serve",
            str(REGISTRY),
            "--host",
            "127.0.0.1",
            "--port",
            "50051",
            "--policy",
            str(POLICY),
            "--execute",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        time.sleep(3)
        env = {"URI_GRPC_MAP": json.dumps({"host": "127.0.0.1:50051"})}
        routes = run_json(["python3", "-c", "import json; from urirun import v2_grpc; print(json.dumps(v2_grpc.list_routes('host')))"] , env=env)
        call = run_json(
            [
                "python3",
                "-m",
                "urirun.v2_grpc",
                "call",
                "httpcheck://host/http/query/status",
                str(REGISTRY),
                "--target",
                "host",
                "--payload",
                json.dumps({"url": IFURI_URL, "expectStatus": 200, "timeout": 5}),
                "--execute",
            ],
            env=env,
        )
        return {"ok": bool(call.get("ok")), "routes": routes, "call": call}
    finally:
        server.send_signal(signal.SIGTERM)
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()


def summarize_catalog(catalog: dict, route_results: dict) -> dict:
    connectors = catalog.get("connectors") or []
    route_result_text = json.dumps(route_results, sort_keys=True)
    summary = []
    for connector in connectors:
        routes = connector.get("routes") or []
        tested = [route for route in routes if route in route_result_text]
        if connector.get("id") == "grpc-transport":
            tested = routes
        status = connector.get("status")
        summary.append(
            {
                "id": connector.get("id"),
                "status": status,
                "routes": routes,
                "testedRoutes": tested,
                "tested": bool(tested) if status == "available" else False,
                "note": "planned connector; skipped until package is available" if status != "available" else "",
            }
        )
    return {"available": [item["id"] for item in summary if item["status"] == "available"], "plannedSkipped": [item["id"] for item in summary if item["status"] != "available"], "items": summary}


def main() -> int:
    catalog = fetch_catalog()
    write_json(BASE / "connectors-catalog.json", catalog)
    build_registry()
    route_results = run_connector_routes()
    mcp_a2a = project_mcp_a2a()
    grpc = test_grpc_transport()
    catalog_summary = summarize_catalog(catalog, route_results)

    required = [
        "sqlite_dataset_create",
        "sqlite_record_upsert",
        "sqlite_search",
        "artifact_register",
        "artifact_list",
        "check_add",
        "check_recent",
        "log_write",
        "http_check",
        "time_now",
        "domain_monitor_http",
        "domain_monitor_dns_current",
        "domain_flow",
        "namecheap_plan",
        "namecheap_backup",
        "namecheap_apply_mock",
        "task_create",
        "task_list",
        "planfile_dsl",
        "task_complete",
        "logs_recent",
    ]
    failures = [name for name in required if not result_ok(route_results.get(name, {}))]
    available_not_tested = [item["id"] for item in catalog_summary["items"] if item["status"] == "available" and not item["tested"]]
    connector_tools = (mcp_a2a["tools"].get("tools") or [])
    connector_skills = (mcp_a2a["card"].get("skills") or [])
    tool_names = {tool.get("name") for tool in connector_tools}
    skill_examples = [example for skill in connector_skills for example in (skill.get("examples") or [])]
    for expected in ("httpcheck_host_http_query", "time_host_clock_query", "data_host_dataset_command", "task_host_ticket_command"):
        if expected not in tool_names:
            failures.append(f"missing MCP tool {expected}")
    if "httpcheck://host/http/query/status" not in skill_examples:
        failures.append("missing A2A skill for httpcheck")
    if "time://host/clock/query/now" not in skill_examples:
        failures.append("missing A2A skill for time-tools")
    if not grpc.get("ok"):
        failures.append("grpc transport call failed")
    if available_not_tested:
        failures.append(f"available connectors not tested: {', '.join(available_not_tested)}")

    result = {
        "ok": not failures,
        "failures": failures,
        "catalog": catalog_summary,
        "registry": json.loads(REGISTRY.read_text(encoding="utf-8")),
        "routeResults": route_results,
        "mcp": {"toolCount": len(connector_tools), "tools": connector_tools},
        "a2a": {"skillCount": len(connector_skills), "card": mcp_a2a["card"]},
        "grpc": grpc,
    }
    write_json(BASE / "connectors-result.json", result)
    print(json.dumps({"ok": result["ok"], "failures": failures, "available": catalog_summary["available"], "plannedSkipped": catalog_summary["plannedSkipped"], "mcpTools": len(connector_tools), "a2aSkills": len(connector_skills)}, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
