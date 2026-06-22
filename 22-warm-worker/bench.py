#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Process-per-URI vs warm-worker pool, measured on a real Python argv-template
# connector (sqlite-context). The warm worker imports the connector ONCE and runs
# each request in-process over a pipe, so the interpreter+import cold start is paid
# once instead of on every call.
from __future__ import annotations

import json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "urirun" / "adapters" / "python"))
sys.path.insert(0, str(ROOT / "urirun-connector-sqlite-context"))

import urirun
from urirun.runtime.worker import WorkerPool
import urirun_connector_sqlite_context as sc

reg = urirun.compile_registry(sc.urirun_bindings())
pol = urirun.policy(allow=["log://*"])
URI, PAYLOAD = "log://host/logs/query/recent", {"limit": 5}


def cold():  # urirun spawns the connector subprocess every call
    return urirun.run(URI, reg, PAYLOAD, mode="execute", policy=pol)


def main() -> int:
    pool = WorkerPool("urirun_connector_sqlite_context.cli:main")
    warm = lambda: pool.run_uri(URI, reg, PAYLOAD)

    c, w = cold(), warm()
    same = json.loads(c["result"]["stdout"]).keys() == w["result"].keys()
    print(f"correctness: cold ok={c.get('ok')} warm ok={w.get('ok')} same-shape={same}\n")

    def bench(label, fn, n=40):
        fn()
        t0 = time.perf_counter()
        for _ in range(n):
            fn()
        ms = (time.perf_counter() - t0) / n * 1000
        print(f"  {label:<34}{ms:8.1f} ms/call")
        return ms

    cold_ms = bench("process-per-URI (cold spawn)", cold)
    warm_ms = bench("warm-worker pool (import once)", warm)
    print(f"\n  SPEEDUP: {cold_ms/warm_ms:.0f}x   ({cold_ms:.0f} ms -> {warm_ms:.1f} ms/call)")
    pool.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
