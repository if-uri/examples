# Part of the ifURI solution.
VENV_BIN := $(wildcard ../venv/bin)
ifneq ($(VENV_BIN),)
export PATH := $(abspath $(VENV_BIN)):$(PATH)
endif

export PYTHONPATH := ../../urirun-contract:../../urirun-connector-router:../../urirun/adapters/python:$(PYTHONPATH)

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
