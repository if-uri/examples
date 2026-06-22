# Prefer the examples venv (../venv) so targets run without activating it first.
VENV_BIN := $(wildcard ../venv/bin)
ifneq ($(VENV_BIN),)
export PATH := $(abspath $(VENV_BIN)):$(PATH)
endif

.PHONY: help python js test
help: ## Show commands
	@grep -E "^[a-zA-Z_-]+:.*?## .*$$" $(MAKEFILE_LIST) | awk "BEGIN{FS=\":.*?## \"}{printf \"  %-8s %s\\n\",\$$1,\$$2}"
python: ## Generate + validate bindings from the Python connector
	python3 python_connector.py > /tmp/defaults.bindings.json && urirun validate /tmp/defaults.bindings.json
js: ## Generate + validate bindings from the JS connector
	node js/example.mjs > /tmp/defaults-js.bindings.json && urirun validate /tmp/defaults-js.bindings.json
test: python ## Run every connector smoke test that is installed
	@command -v node >/dev/null && $(MAKE) js || echo "skip js (no node)"
