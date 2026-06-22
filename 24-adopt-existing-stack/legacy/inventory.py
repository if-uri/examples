#!/usr/bin/env python3
# Pretend this is your EXISTING inventory module — already written, already tested,
# using whatever libraries you like. urirun adopts it without a rewrite: the thin
# argparse shim at the bottom is the only "glue", and even that is optional if you
# expose a console_script. The business functions are untouched.
from __future__ import annotations

import argparse
import json
import sys

_STOCK = {"sku-1": 7, "sku-2": 0, "sku-3": 42}


def check_stock(sku: str) -> dict:
    return {"sku": sku, "available": _STOCK.get(sku, 0), "inStock": _STOCK.get(sku, 0) > 0}


def reserve(sku: str, qty: int) -> dict:
    have = _STOCK.get(sku, 0)
    ok = have >= qty > 0
    return {"sku": sku, "qty": qty, "ok": ok, "remaining": have - qty if ok else have}


def main() -> int:
    parser = argparse.ArgumentParser(prog="inventory")
    sub = parser.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check"); c.add_argument("--sku", required=True)
    r = sub.add_parser("reserve"); r.add_argument("--sku", required=True); r.add_argument("--qty", type=int, required=True)
    args = parser.parse_args()
    result = check_stock(args.sku) if args.cmd == "check" else reserve(args.sku, args.qty)
    print(json.dumps(result))
    return 0 if result.get("inStock", result.get("ok", True)) else 0


if __name__ == "__main__":
    sys.exit(main())
