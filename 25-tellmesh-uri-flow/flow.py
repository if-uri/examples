#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# A multi-step URI FLOW across three adopted tellmesh-style packs, executed for real
# through urirun — each step's output feeds the next:
#
#   kvm://{host}/monitor/command/capture   --image_id-->  (1)
#   ocr://{host}/image/query/text          --text------>  (2)
#   llm://{host}/chat/command/complete     --summary--->  (3)
#
# One registry carries all three schemes. The flow runner threads the real result of
# each `urirun.run(..., mode="execute")` into the next step's payload, under a policy
# that only allows these three schemes. This proves the URIs interoperate in action,
# not just resolve.

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# make the bundled handler packages importable (flow_kvm/flow_ocr/flow_llm)
sys.path.insert(0, str(HERE / "packs"))
# prefer the in-repo urirun
sys.path.insert(0, str(HERE.parent.parent / "urirun" / "adapters" / "python"))

from urirun import v2  # noqa: E402
from urirun.runtime import _runtime as runtime, adopt_pack  # noqa: E402


def build_registry() -> dict:
    """Adopt every pack manifest, hydrate its python handler descriptor, compile one
    registry that can actually execute the handlers in-process."""
    bindings: dict[str, dict] = {}
    for manifest in sorted((HERE / "packs").glob("*/manifest.yaml")):
        doc = adopt_pack.adopt(str(manifest))
        for uri, b in doc["bindings"].items():
            ref = b.get("ref", "")
            if ":" in ref:  # "module:export" -> re-importable descriptor for execute
                module, _, export = ref.partition(":")
                b["python"] = {"type": "python", "module": module, "export": export}
            bindings[uri] = b
    return v2.compile_registry({"version": "urirun.bindings.v2", "bindings": bindings})


def run_flow(registry: dict, *, host: str = "host1", monitor: int = 0) -> list[dict]:
    """Execute the chain, threading each step's result into the next step's payload."""
    policy = runtime.build_policy(None, ["kvm://**", "ocr://**", "llm://**"], None)

    def step(uri: str, payload: dict) -> dict:
        env = v2.run(uri, registry, payload=payload, mode="execute", policy=policy)
        if not env.get("ok"):
            raise SystemExit(f"step failed: {uri} -> {json.dumps(env)[:300]}")
        return env["result"]["value"]

    steps: list[dict] = []

    # (1) capture a monitor -> image_id
    cap = step(f"kvm://{host}/monitor/command/capture", {"monitor": monitor})
    steps.append({"uri": f"kvm://{host}/monitor/command/capture", "out": cap})

    # (2) OCR that exact image_id (output of step 1) -> text
    ocr = step(f"ocr://{host}/image/query/text", {"image_id": cap["image_id"]})
    steps.append({"uri": f"ocr://{host}/image/query/text", "out": ocr})

    # (3) summarize the OCR text (output of step 2) -> summary
    llm = step(f"llm://{host}/chat/command/complete",
               {"prompt": f"Summarize this scanned text:\n{ocr['text']}"})
    steps.append({"uri": f"llm://{host}/chat/command/complete", "out": llm})

    return steps


def main() -> int:
    registry = build_registry()
    n = len(v2.list_routes(registry, None))
    print(f"== one registry, {n} routes across 3 adopted packs (kvm, ocr, llm) ==\n")
    steps = run_flow(registry)
    for i, s in enumerate(steps, start=1):
        print(f"  [{i}] {s['uri']}")
        print(f"      -> {json.dumps(s['out'])}")
    summary = steps[-1]["out"]["summary"]
    print(f"\nflow result: {summary!r}")
    # the whole point: step 3's summary is derived from step 2's text, which came from
    # step 1's image_id — the URIs interoperated, executed, end to end.
    ok = "42.00" in summary and "2026-07-01" in summary
    print("end-to-end data threaded correctly:", ok)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
