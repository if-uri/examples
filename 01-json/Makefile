# Prefer the examples venv (../venv) so targets run without activating it first.
VENV_BIN := $(wildcard ../venv/bin)
ifneq ($(VENV_BIN),)
export PATH := $(abspath $(VENV_BIN)):$(PATH)
endif

.PHONY: help validate compile list test
help: ## Show commands
	@grep -E "^[a-zA-Z_-]+:.*?## .*$$" $(MAKEFILE_LIST) | awk "BEGIN{FS=\":.*?## \"}{printf \"  %-10s %s\\n\",\$$1,\$$2}"
validate: ## Validate the binding document
	urirun validate bindings.v2.example.json
compile: ## Compile the bindings into a registry
	urirun compile bindings.v2.example.json --out /tmp/registry.json
list: compile ## List the routes in the compiled registry
	urirun list /tmp/registry.json
test: ## Validate the binding document (CI)
	urirun validate bindings.v2.example.json
