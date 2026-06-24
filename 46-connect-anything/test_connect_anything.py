"""Self-contained verification for example 46 (connect anything through adopt://).

`run_examples.sh` demos the flow against real local repos; this test reproduces the same
three steps — inspect, plan, scan — on throwaway fixtures so the example is verifiable
anywhere (CI included), with no dependency on `/home/tom/github/*` checkouts.

Run: `python -m pytest examples/46-connect-anything/test_connect_anything.py -q`
(needs `urirun-connector-adopt` installed, e.g. the repo venv).
"""
from __future__ import annotations

import json

import pytest

adopt = pytest.importorskip("urirun_connector_adopt")
from urirun_connector_adopt import inspect_project, plan_project, scan_projects  # noqa: E402


def _docker_service_project(base):
    (base / "Dockerfile").write_text("FROM python:3.12-slim\nCMD [\"uvicorn\",\"app:app\"]\n", encoding="utf-8")
    (base / "pyproject.toml").write_text(
        '[project]\nname = "pdf-ocr"\ndescription = "FastAPI OCR service"\ndependencies = ["fastapi","uvicorn"]\n',
        encoding="utf-8",
    )
    return base


def test_inspect_classifies_a_docker_service_project(tmp_path):
    project = inspect_project(str(_docker_service_project(tmp_path)))["project"]
    groups = {g["id"] for g in project["groups"]}
    # A Dockerfile + a FastAPI pyproject is reusable as a container, a service and an API.
    assert {"docker", "service", "api", "library"} <= groups
    assert project["primaryGroup"] == "docker"


def test_plan_attaches_a_connector_scheme_and_realization_contracts(tmp_path):
    plan_result = plan_project(str(_docker_service_project(tmp_path)))
    value = plan_result.get("result", {}).get("value", plan_result)  # CLI-envelope tolerant
    plan = value.get("plan", plan_result.get("plan", {}))
    connector = plan.get("connector", {})
    assert connector.get("scheme")            # a scheme is chosen for the wrapper
    contract_groups = {c.get("group") for c in plan.get("contracts", [])}
    # Each adoptable surface gets a realization contract before any command may execute.
    assert {"docker", "service", "api"} <= contract_groups


def test_scan_classifies_a_mixed_workspace(tmp_path):
    (tmp_path / "svc").mkdir()
    _docker_service_project(tmp_path / "svc")
    (tmp_path / "tool").mkdir()
    (tmp_path / "tool" / "pyproject.toml").write_text(
        '[project]\nname = "mytool"\n[project.scripts]\nmytool = "mytool.cli:main"\n', encoding="utf-8")
    (tmp_path / "pack").mkdir()
    (tmp_path / "pack" / "pyproject.toml").write_text(
        '[project]\nname = "mypack"\n[tool.urirun]\nbindings = "bindings.v2.json"\n', encoding="utf-8")

    result = scan_projects([str(tmp_path)], maxDepth=2, limit=25)
    by_name = {p["path"].rstrip("/").split("/")[-1]: p for p in result["projects"]}
    assert result["count"] >= 3
    assert by_name["svc"]["primaryGroup"] == "docker"
    assert "cli" in by_name["tool"]["groups"]
    assert "uri-pack" in by_name["pack"]["groups"]


def test_inspect_returns_a_uri_surface(tmp_path):
    project = inspect_project(str(_docker_service_project(tmp_path)))["project"]
    uris = {r["uri"] for r in project["uriSurface"]}
    # The whole point: a plain project now has a stable, callable URI surface.
    assert any(u.startswith(("service://", "docker://", "api://")) for u in uris), json.dumps(sorted(uris))
