#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# A tiny "package manager" connector so INSTALLING the other connectors is itself
# a URI step you can put in a flow:
#   pkg://host/connector/command/install  {name}     -> pip install -e the connector
#   pkg://host/connector/query/installed  {module}   -> is the python module importable?
# This is what lets a YAML flow make sure every urirun-connector-* is present
# before the flow that uses them runs.

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))  # if-uri/


def _route(uri, op, props, label, required=None):
    argv = [sys.executable, os.path.abspath(__file__), op]
    for k in props:
        argv += [f"--{k}", "{" + k + "}"]
    schema = {"type": "object", "additionalProperties": False, "properties": props}
    if required:
        schema["required"] = required
    return {uri: {"adapter": "argv-template", "kind": "command" if "command" in uri else "command",
                  "argv": argv, "inputSchema": schema, "meta": {"connector": "pkg", "label": label}, "uri": uri}}


def bindings() -> dict:
    b = {}
    b.update(_route("pkg://host/connector/command/install", "install",
                    {"name": {"type": "string"}}, "pip install -e a urirun connector", ["name"]))
    b.update(_route("pkg://host/connector/query/installed", "installed",
                    {"module": {"type": "string"}}, "Is a python module importable?", ["module"]))
    return {"version": "urirun.bindings.v2", "bindings": b}


def install(name: str) -> dict:
    cdir = os.path.join(ROOT, f"urirun-connector-{name}")
    if not os.path.isdir(cdir):
        return {"ok": False, "name": name, "error": f"no such connector dir: {cdir}"}
    proc = subprocess.run([sys.executable, "-m", "pip", "install", "--no-input", "--no-deps", "-e", cdir],
                          capture_output=True, text=True, timeout=300)
    ok = proc.returncode == 0
    return {"ok": ok, "name": name, "dir": cdir,
            **({} if ok else {"error": (proc.stderr or proc.stdout)[-200:]})}


def installed(module: str) -> dict:
    try:
        found = importlib.util.find_spec(module) is not None
    except (ImportError, ValueError):
        found = False
    return {"ok": found, "module": module, "installed": found}


def main(argv: list[str]) -> int:
    if argv and argv[0] == "bindings":
        print(json.dumps(bindings())); return 0
    p = argparse.ArgumentParser()
    p.add_argument("op")
    p.add_argument("--name", default="")
    p.add_argument("--module", default="")
    a = p.parse_args(argv)
    if a.op == "install":
        print(json.dumps(install(a.name)))
    elif a.op == "installed":
        print(json.dumps(installed(a.module)))
    else:
        print(json.dumps({"ok": False, "error": f"unknown op {a.op}"})); return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
