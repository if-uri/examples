VENV_BIN := $(wildcard ../venv/bin)
ifneq ($(VENV_BIN),)
export PATH := $(abspath $(VENV_BIN)):$(PATH)
endif

.PHONY: help run check test
help: ## Show commands
	@grep -E "^[a-zA-Z_-]+:.*?## .*$$" $(MAKEFILE_LIST) | awk "BEGIN{FS=\":.*?## \"}{printf \"  %-7s %s\\n\",\$$1,\$$2}"
run: ## Generate + run the install and smoke flows for every connector
	python3 run.py
check: ## Use already-installed connectors (skip the install flow)
	python3 run.py --no-install
test: ## Every connector imports, compiles, and runs-or-is-gated
	python3 -m pytest test_connectors.py -q
