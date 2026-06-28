# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
"""The autonomy safety stack: a plan is routed (where) before it executes (shape-guarded).

- a routable plan runs and conforms;
- a rogue plan (a node not in the mesh) is BLOCKED by the router pre-flight, before any action."""
import run as ex
from urirun_connector_router import routing as router


def test_routable_plan_runs_and_conforms():
    assert ex.run(rogue=False) == 0


def test_rogue_plan_is_blocked_preflight_not_executed():
    # the agent's rogue plan targets a node not in the mesh; the router must refuse it
    plan = ex.agent_plan("audit", rogue=True)
    diag = router.diagnose_plan(plan, ex.MESH)
    assert diag["ok"] is False
    assert diag["blockedSteps"][0]["blockedAt"] == "target"
    assert ex.run(rogue=True) == 0  # run returns 0 because the router correctly aborted


def test_router_pins_every_step_location():
    plan = ex.agent_plan("audit", rogue=False)
    diag = router.diagnose_plan(plan, ex.MESH)
    assert diag["ok"] is True
    # every step's execution location is known BEFORE acting
    assert all(s["runsOn"] == "host" for s in diag["steps"])


def test_contract_conforms():
    from urirun_contract import conform
    conform(ex.CONTRACTS)
