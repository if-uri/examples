# Prefer the examples venv (../venv) so targets run without activating it first.
VENV_BIN := $(wildcard ../venv/bin)
ifneq ($(VENV_BIN),)
export PATH := $(abspath $(VENV_BIN)):$(PATH)
endif

.PHONY: help setup run test clean
help: ## Show commands
	@grep -E "^[a-zA-Z_-]+:.*?## .*$$" $(MAKEFILE_LIST) | awk "BEGIN{FS=\":.*?## \"}{printf \"  %-7s %s\\n\",\$$1,\$$2}"
setup: ## Install the browser-control connector (editable) for a real package install
	# --no-deps keeps your local editable `urirun`; the connector pins an older pinned urirun
	pip install -e ../../urirun-connector-browser-control --no-deps
run: ## Run the LLM-over-URI agent on a sample goal
	python3 agent.py "check and read https://example.com"
test: ## Run the agent tests
	python3 -m pytest test_agent.py -q
clean: ## Remove the agent run log
	rm -f agent-run.log
