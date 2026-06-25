#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Check the REAL task scenarios against the reversibility contract
# (urirun-connector-kvm/docs/reversibility-contract.md): for each step, is it a mutation, does
# it have a registered inverse, and so — is the whole flow rollback-able, where does the
# invariant BLOCK (irreversible mutation), and where would saga-compensation undo on failure.
#
# The point: prove the contract against flows we actually run, and surface the surface-principle
# — on os-level (blind) most input mutations are irreversible (no readable state to invert to);
# on cdp the same flow becomes reversible. Run: python reversibility_check.py [--surface cdp|os]
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_scenarios as rs   # reuse the YAML loader + placeholder logic


def _suffix(uri: str) -> str:
    body = uri.split("://", 1)[1] if "://" in uri else uri
    return body.split("/", 1)[1] if "/" in body else body


# Reversibility classification per the contract. Returns (mutates, reversible, inverse_note).
# `surface` matters: cdp can READ state (so fill/type/navigate/scroll get a sound inverse);
# os-level is blind, so the same writes are irreversible -> the invariant blocks them.
# READ-ONLY routes that wear a `/command/` path but mutate NOTHING (a `/command/` is not
# automatically a mutation — a finding from running this over the real scenarios, where
# shell date/uname/which were wrongly blocked as writes).
# keyed on the path AFTER scheme://node/ (what _suffix returns), e.g. shell://n/command/date
# -> "command/date". A fixed-arg shell read is a query in disguise, not a world mutation.
_READ_ONLY_COMMANDS = {"command/date", "command/uname", "command/which", "command/echo"}


def classify(uri: str, payload: dict, surface: str) -> tuple[bool, bool, str]:
    suf = _suffix(uri)
    cdp = surface == "cdp"
    if "/query/" in uri or suf.endswith(("/ensure", "/ready")) or suf in _READ_ONLY_COMMANDS:
        return False, True, "read-only (query / fixed-arg command) — not a mutation"
    # log/session append: a write, but append-only & low-stakes — inverse = delete the entry.
    if suf in ("session/command/write", "log/session/command/write"):
        return True, True, "log append⟂delete-entry (benign, reversible)"
    if suf == "cdp/page/command/navigate":
        return True, True, "navigate⟂navigate(prev)"
    if suf == "ui/command/fill":
        return True, cdp, "fill⟂fill(prev)" if cdp else "needs CDP to read prev value"
    if suf == "input/command/type":
        return True, cdp, "type⟂clear (only if field empty, CDP)" if cdp else "blind type — no inverse"
    if suf in ("ui/command/click", "ui/command/click-text"):
        return True, cdp, "reversible IF effect captured (open/nav/create/toggle) — needs CDP" if cdp \
            else "blind click — effect unknown, no inverse"
    if suf == "input/command/key":
        keys = str(payload.get("keys", "")).lower()
        # ctrl+a (select) is benign/reversible-ish; submit/save/close keys are irreversible.
        if keys in ("ctrl+a", "tab"):
            return True, True, f"{keys}: navigational, trivially reversible"
        return True, False, f"{keys}: side-effecting keypress (submit/save/close) — IRREVERSIBLE"
    if suf == "input/command/scroll":
        return True, True, "scroll⟂scroll-to(prev) (cdp) / -dy approx (os)"
    if suf == "desktop/command/launch":
        return True, True, "launch⟂kill(pid)"
    if suf == "proc/command/kill":
        return True, False, "cannot un-kill — IRREVERSIBLE"
    return True, False, "unknown command — assume irreversible (fail-safe)"


def analyse(scenario: dict, surface: str) -> dict:
    rows, mutations, reversible, first_block = [], 0, 0, None
    for i, step in enumerate(scenario.get("steps") or []):
        uri = str(step.get("uri", "")).replace("{host}", "host")
        mut, rev, note = classify(uri, step.get("payload") or {}, surface)
        if mut:
            mutations += 1
            reversible += int(rev)
            if not rev and first_block is None:
                first_block = i
        rows.append((i, _suffix(uri), mut, rev, note))
    return {"name": scenario.get("name"), "rows": rows, "mutations": mutations,
            "reversible": reversible, "first_block": first_block}


def main() -> None:
    surface = "cdp" if "--surface" in sys.argv and "cdp" in sys.argv else \
        (sys.argv[sys.argv.index("--surface") + 1] if "--surface" in sys.argv else "os")
    files = sorted((HERE / "scenarios").glob("*.yaml"))
    print(f"Reversibility check — surface={surface}  ({len(files)} scenarios)\n" + "=" * 78)
    fully_rev = blocked = 0
    for f in files:
        sc = rs._load_yaml(f)
        a = analyse(sc, surface)
        if not a["mutations"]:
            verdict = "read-only (nothing to undo)"
        elif a["reversible"] == a["mutations"]:
            verdict = "FULLY REVERSIBLE → rollback/compensation works end-to-end"; fully_rev += 1
        else:
            verdict = f"INVARIANT BLOCKS at step {a['first_block']} (irreversible mutation, NOT run)"; blocked += 1
        print(f"\n▸ {a['name']:42} {a['reversible']}/{a['mutations']} mut reversible — {verdict}")
        for i, suf, mut, rev, note in a["rows"]:
            tag = "·query " if not mut else ("✓rev  " if rev else "✗BLOCK")
            print(f"    {i:>2} {tag} {suf:34} {note}")
    print("\n" + "=" * 78)
    print(f"SUMMARY (surface={surface}): {fully_rev} fully reversible · {blocked} blocked by invariant "
          f"· {len(files) - fully_rev - blocked} read-only")
    print("On os-level, blind input writes (type/click/submit-keys) are irreversible → the invariant")
    print("refuses them BEFORE running, so the prefix stays undoable. On cdp the connector can read")
    print("state, so fill/type/click/navigate gain sound inverses and the same flows become reversible.")


if __name__ == "__main__":
    main()
