# Author: Tom Sapletta · https://tom.sapletta.com
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_all


def test_all_connectors_valid_and_runnable():
    check_all.setup_polyglot_bin()
    rows = [check_all.check(c) for c in check_all.CONNECTORS]
    broken = [r["connector"] for r in rows if not r.get("valid")]
    assert not broken, f"connectors with invalid/erroring bindings: {broken}"
    assert len(rows) == 17
    executed = [r["connector"] for r in rows if r.get("ok")]
    # the offline/network-safe routes must actually execute end-to-end
    for name in ("base64", "hash", "uuid", "time-tools", "mcp-filesystem", "email", "sqlite-context"):
        assert name in executed, f"{name} did not execute its route"
