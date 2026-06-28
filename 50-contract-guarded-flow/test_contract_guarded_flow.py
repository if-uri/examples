# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
"""The example must do two things: pass the honest flow, and CATCH the drift.

Plus: the in-process Python CONTRACTS and the neutral `contracts.json` (which drives the
JS/Go SDK guards) declare the SAME shape — one source of truth, any language."""
import json
import os

import pytest

import run as ex

HERE = os.path.dirname(os.path.abspath(__file__))


def test_honest_flow_conforms():
    assert ex.run(drift=False) == 0


def test_drift_is_caught_by_contract():
    # run(drift=True) returns 0 only because the contract CAUGHT the drift
    assert ex.run(drift=True) == 0


def test_contract_conforms_standalone():
    from urirun_contract import conform
    conform(ex.CONTRACTS)


def test_neutral_json_matches_inprocess_contracts():
    """contracts.json (for JS/Go guards) declares the same routes + out shape as the Python CONTRACTS."""
    doc = json.load(open(os.path.join(HERE, "contracts.json")))
    assert set(doc["contracts"]) == set(ex.CONTRACTS)
    for route, c in doc["contracts"].items():
        assert c["effect"] == ex.CONTRACTS[route].effect
        assert c["out"] == ex.CONTRACTS[route].out


def _contracts_from_neutral_json():
    from urirun_contract import Contract

    doc = json.load(open(os.path.join(HERE, "contracts.json")))
    return {
        route: Contract(
            version=c["version"],
            effect=c["effect"],
            reversible=c["reversible"],
            inverse_route=c.get("inverseRoute") or "",
            inp=c.get("inp", {}),
            out=c.get("out", {}),
            errors=tuple(c.get("errors", ())),
            examples=tuple(c.get("examples", ())),
        )
        for route, c in doc["contracts"].items()
    }


def _neutral_doc():
    return json.load(open(os.path.join(HERE, "contracts.json")))


def test_neutral_json_contract_guards_the_connector_envelope():
    """The portable contracts.json is strong enough to catch handler drift, not only compare shape."""
    from urirun_contract import conform, envelope_violation

    contracts = _contracts_from_neutral_json()
    conform(contracts)

    ex._STORE.clear()
    try:
        ex._DRIFT = False
        honest = ex.append(text="buy milk", tag="todo")
        assert envelope_violation(contracts["entry/command/append"], honest) is None

        ex._DRIFT = True
        drifted = ex.append(text="call Ada", tag="todo")
        assert envelope_violation(contracts["entry/command/append"], drifted) is not None
    finally:
        ex._DRIFT = False


def test_attached_contract_reaches_mcp_and_a2a_output_schema():
    """Connector + contract must survive registry projection into MCP/A2A tool surfaces."""
    from urirun_contract import attach_contracts
    from urirun_runtime.v2_mcp import to_a2a_card, to_mcp_tools

    attach_contracts(ex.notes, ex.CONTRACTS)
    registry = ex.notes.registry()

    tools = {tool["_uri"]: tool for tool in to_mcp_tools(registry)}
    append_tool = tools["notes://host/entry/command/append"]
    assert append_tool["outputSchema"]["properties"]["count"] == {"type": "integer"}
    assert append_tool["outputSchema"]["properties"]["connector"] == {"const": "notes"}
    assert append_tool["outputSchema"]["examples"][0]["action"] == "append"

    card = to_a2a_card(registry)
    skills = {skill["examples"][0]: skill for skill in card["skills"]}
    append_skill = skills["notes://host/entry/command/append"]
    assert append_skill["outputSchema"] == append_tool["outputSchema"]


def test_neutral_contract_json_schema_validates_golden_examples():
    """The portable contract dialect projects to JSON Schema that validates its golden corpus."""
    import pytest
    from urirun_contract.contract_jsonschema import to_json_schema_document

    jsonschema = pytest.importorskip("jsonschema")
    doc = _neutral_doc()
    for route, c in doc["contracts"].items():
        in_schema = to_json_schema_document(route, c.get("inp", {}), kind="input")
        out_schema = to_json_schema_document(route, c.get("out", {}), kind="output")
        jsonschema.Draft202012Validator.check_schema(in_schema)
        jsonschema.Draft202012Validator.check_schema(out_schema)
        for example in c.get("examples", []):
            jsonschema.validate(example.get("payload", {}), in_schema)
            jsonschema.validate(example.get("result", {}), out_schema)


def test_neutral_contract_drives_codegen_for_all_routes():
    """contracts.json is a generator input: Python/JS/Go stubs cover exactly the connector routes."""
    from urirun_contract.codegen import _load_contracts_json, emit_go_module, emit_js_module, emit_py_module

    path = os.path.join(HERE, "contracts.json")
    contracts = _load_contracts_json(path)
    routes = set(_neutral_doc()["contracts"])

    py_code = emit_py_module(contracts)
    compile(py_code, "notes_handlers_generated.py", "exec")
    js_code = emit_js_module(contracts)
    go_code = emit_go_module(contracts)

    assert {line.split('"')[1] for line in py_code.splitlines()
            if line.startswith("@conn.handler(")} == routes
    for route in routes:
        assert route in js_code
        assert route in go_code
    assert js_code.count("export function ") == len(routes)
    assert go_code.count("func ") == len(routes)


def test_neutral_contract_is_the_reversibility_schema_source():
    """The reversible engine can derive mutating/non-mutating facts from the contract alone."""
    from urirun_contract.contract_reversible import callspec_fields

    contracts = _neutral_doc()["contracts"]
    append = callspec_fields("entry/command/append", contracts["entry/command/append"],
                             conn_uri=ex.notes.uri)
    list_notes = callspec_fields("entry/query/list", contracts["entry/query/list"],
                                 conn_uri=ex.notes.uri)

    assert append == {
        "uri": "notes://host/entry/command/append",
        "mutates": True,
        "reversible": False,
        "note": "from contract",
    }
    assert list_notes == {
        "uri": "notes://host/entry/query/list",
        "mutates": False,
        "reversible": False,
        "note": "from contract",
    }
