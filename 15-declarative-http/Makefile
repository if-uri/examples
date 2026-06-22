# Prefer the examples venv (../venv) so targets run without activating it first.
VENV_BIN := $(wildcard ../venv/bin)
ifneq ($(VENV_BIN),)
export PATH := $(abspath $(VENV_BIN)):$(PATH)
endif

.PHONY: help build test clean
help: ## Show commands
	@grep -E "^[a-zA-Z_-]+:.*?## .*$$" $(MAKEFILE_LIST) | awk "BEGIN{FS=\":.*?## \"}{printf \"  %-6s %s\\n\",\$$1,\$$2}"
build: ## Build + validate + compile the httpbin spec
	urirun connectors from-spec httpbin.toml > httpbin.bindings.json
	urirun validate httpbin.bindings.json
	urirun compile httpbin.bindings.json --out httpbin.registry.json
test: ## Build + validate the httpbin and ksef specs
	urirun connectors from-spec httpbin.toml > httpbin.bindings.json && urirun validate httpbin.bindings.json
	urirun connectors from-spec ksef.toml > ksef.bindings.json && urirun validate ksef.bindings.json
clean: ## Remove the generated bindings/registry
	rm -f httpbin.bindings.json httpbin.registry.json ksef.bindings.json
