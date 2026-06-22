# Prefer the examples venv (../venv) so targets run without activating it first.
VENV_BIN := $(wildcard ../venv/bin)
ifneq ($(VENV_BIN),)
export PATH := $(abspath $(VENV_BIN)):$(PATH)
endif

.PHONY: help setup local web ksef declarative test clean
help: ## List targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  %-12s %s\n",$$1,$$2}'
setup: tools.bindings.json ksef.bindings.json ## Generate the registries the flows reference
tools.bindings.json: ## capability routes (time/httpcheck/browser/log) from example 14
	python3 ../14-llm-uri-agent/tools.py bindings > $@
ksef.bindings.json: ## KSeF declarative routes from the connector
	urirun-connector-ksef bindings > $@ 2>/dev/null || python3 -c "import json,urirun_connector_ksef as k; print(json.dumps(k.urirun_bindings()))" > $@
local: setup ## Run scenario 1 (offline)
	./flow-local.sh
web: setup ## Run scenario 2 (network + Chrome)
	./flow-web-recon.sh
ksef: setup ## Run scenario 5 (dry-run)
	./flow-ksef.sh
declarative: ## Run scenario 3 (network)
	./flow-declarative.sh
test: ## Offline CI test
	python3 -m pytest test_flows.py -q
clean: ## Remove generated registries
	rm -f tools.bindings.json ksef.bindings.json httpbin.registry.json agent-run.log
