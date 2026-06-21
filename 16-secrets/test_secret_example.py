# Author: Tom Sapletta · https://tom.sapletta.com
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import secret_demo


def test_secret_invariants_hold():
    r = secret_demo.scenarios()
    assert r["referenceOnly"] is True          # registry/bindings carry no value
    assert r["dryRunNoExec"] is True           # dry-run never resolves the secret
    assert r["deniedWithoutAllow"] is True     # deny-by-default
    assert r["executedWithAllow"] is True      # injected -> request succeeds
    assert r["authValid"] is True              # the server got the real Bearer token
    assert r["noLeakInResult"] is True         # value never on a serialized surface
