#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Pretty-print the shared transaction ledger that the camera + invoice connectors auto-append
# to (~/.urirun/ledger.jsonl). Thin viewer over invoice://host/ledger/query/list.
#
#   python3 ledger.py                 # recent rows + totals
#   python3 ledger.py --event ksef_upo
#   python3 ledger.py --json

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone

import urirun_connector_invoice.core as inv


def _fmt_ts(ts) -> str:
    try:
        return datetime.fromtimestamp(float(ts), tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:  # noqa: BLE001
        return str(ts)


def _row_detail(r: dict) -> str:
    ev = r.get("event")
    if ev == "receipt":
        return f"total={r.get('total')} {r.get('currency') or ''} nip={r.get('nip') or '-'}"
    if ev == "inspect":
        return f"passed={r.get('passed')} alerts={r.get('alerts') or []}"
    if ev == "ingest":
        return f"action={r.get('action')} bytes={r.get('uploadBytes')}"
    if ev == "ksef_build":
        return f"gross={r.get('gross')} nr={r.get('number') or '-'}"
    if ev == "ksef_upo":
        return f"KSeF#={r.get('ksefNumber')}"
    return ", ".join(f"{k}={v}" for k, v in r.items() if k not in ("ts", "connector", "event"))


def main() -> int:
    ap = argparse.ArgumentParser(description="view the ifURI transaction ledger")
    ap.add_argument("--event", default="", help="filter: receipt|inspect|ingest|ksef_build|ksef_upo")
    ap.add_argument("--connector", default="", help="filter: camera|invoice")
    ap.add_argument("--limit", type=int, default=30)
    ap.add_argument("--path", default="", help="override ledger path")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    res = inv.ledger_list(path=args.path, limit=args.limit, event=args.event, connector=args.connector)
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0
    if not res.get("exists"):
        print(f"(brak dziennika: {res.get('path')} — uruchom dowolny skan/fakturę, a zapisze się sam)")
        return 0

    s = res["summary"]
    print(f"== ifURI ledger — {res['count']} zdarzeń ({res['path']}) ==")
    print(f"zdarzenia: {s['events']}")
    print(f"paragony razem: {s['receiptsTotal']}   faktury: {s['invoicesBuilt']} "
          f"(brutto Σ {s['grossBuilt']})   KSeF potwierdzone: {s['ksefConfirmed']}")
    if s["ksefNumbers"]:
        print(f"numery KSeF: {', '.join(s['ksefNumbers'])}")
    print(f"\n{'czas (UTC)':<20} {'konektor':<9} {'zdarzenie':<11} szczegóły")
    print("-" * 78)
    for r in res["rows"]:
        print(f"{_fmt_ts(r.get('ts')):<20} {r.get('connector', '-'):<9} "
              f"{r.get('event', '-'):<11} {_row_detail(r)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
