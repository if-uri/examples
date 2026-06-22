# Prefer the examples venv (../venv) so targets run without activating it first.
VENV_BIN := $(wildcard ../venv/bin)
ifneq ($(VENV_BIN),)
export PATH := $(abspath $(VENV_BIN)):$(PATH)
endif

.PHONY: help run llm test clean
help: ## Show commands
	@grep -E "^[a-zA-Z_-]+:.*?## .*$$" $(MAKEFILE_LIST) | awk "BEGIN{FS=\":.*?## \"}{printf \"  %-6s %s\\n\",\$$1,\$$2}"
run: ## Run all 6 office scenarios (deterministic) with verification
	python3 run.py
llm: ## Plan one scenario with a real model (needs examples/.env)
	python3 run.py --scenario report --llm
test: ## Offline test: each task plans >=10 steps, executes, and verifies
	python3 -m pytest test_office.py -q
clean: ## Remove the scratch office state
	rm -f .office_state.json
