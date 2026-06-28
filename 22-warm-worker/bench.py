#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Process-per-URI vs warm handler pool, measured on a real Python
# local-function-subprocess connector (sqlite-context). The warm worker imports
# the connector ONCE and runs each request in-process over a pipe, so the
# interpreter+import cold start is paid once instead of on every call.
from __future__ import annotations

import os, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOCAL_PATHS = [
    str(ROOT / "urirun" / "adapters" / "python"),
    str(ROOT / "urirun-connector-sqlite-context"),
]
for path in reversed(LOCAL_PATHS):
    sys.path.insert(0, path)
existing_pythonpath = os.environ.get("PYTHONPATH")
os.environ["PYTHONPATH"] = os.pathsep.join(
    LOCAL_PATHS + ([existing_pythonpath] if existing_pythonpath else [])
)

import urirun
from urirun.runtime.worker import HandlerPool
import urirun_connector_sqlite_context as sc

reg = urirun.compile_registry(sc.urirun_bindings())
pol = urirun.policy(allow=["log://*"])
URI, PAYLOAD = "log://host/logs/query/recent", {"limit": 5}


def cold():  # urirun spawns the connector subprocess every call
    return urirun.run(URI, reg, PAYLOAD, mode="execute", policy=pol)


def main() -> int:
    pool = HandlerPool()
    warm = lambda: pool.run_ref("urirun_connector_sqlite_context.core:recent_logs", PAYLOAD)

    c, w = cold(), warm()
    same = c["result"]["value"].keys() == w["result"].keys()
    print(f"correctness: cold ok={c.get('ok')} warm ok={w.get('ok')} same-shape={same}\n")

    def bench(label, fn, n=40):
        fn()
        t0 = time.perf_counter()
        for _ in range(n):
            fn()
        ms = (time.perf_counter() - t0) / n * 1000
        print(f"  {label:<34}{ms:8.1f} ms/call")
        return ms

    cold_ms = bench("local-function subprocess", cold)
    warm_ms = bench("warm handler pool", warm)
    print(f"\n  SPEEDUP: {cold_ms/warm_ms:.0f}x   ({cold_ms:.0f} ms -> {warm_ms:.1f} ms/call)")
    pool.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
