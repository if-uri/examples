# Part of the ifURI solution.
PY ?= python3

.PHONY: run rogue both test

run: ## Routable plan: router pins each step to host, executes under contract
	$(PY) run.py

rogue: ## Agent picks a node not in the mesh → router blocks the plan pre-flight
	$(PY) run.py --rogue

both: ## Routable then rogue
	$(PY) run.py --both

test: ## pytest: routable runs+conforms, rogue blocked before execution
	$(PY) -m pytest test_router_guarded_autonomy.py -q
