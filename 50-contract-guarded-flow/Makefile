# Part of the ifURI solution.
PY ?= python3

.PHONY: run drift both test

run: ## Honest flow — connector conforms to its contract across every step
	$(PY) run.py

drift: ## Drift flow — the contract catches a mis-shaped envelope at the flow boundary
	$(PY) run.py --drift

both: ## Honest then drift
	$(PY) run.py --both

test: ## pytest: honest passes, drift caught, neutral JSON == in-process contracts
	$(PY) -m pytest test_contract_guarded_flow.py -q
