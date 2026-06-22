# Prefer the examples venv (../venv) so targets run without activating it first.
VENV_BIN := $(wildcard ../venv/bin)
ifneq ($(VENV_BIN),)
export PATH := $(abspath $(VENV_BIN)):$(PATH)
endif

.PHONY: help js nodejs ts php go test
help: ## Show commands
	@grep -E "^[a-zA-Z_-]+:.*?## .*$$" $(MAKEFILE_LIST) | awk "BEGIN{FS=\":.*?## \"}{printf \"  %-8s %s\\n\",\$$1,\$$2}"
js: ## Generate + validate bindings from the JS helper
	node js/example.mjs > /tmp/gen_js.json && urirun validate /tmp/gen_js.json
nodejs: ## Generate + validate bindings from the Node script
	node nodejs/generate-bindings.mjs /tmp/gen_node.json && urirun validate /tmp/gen_node.json
ts: ## Generate + validate bindings from the TypeScript decorators
	rm -rf /tmp/gen_ts && tsc --target ES2022 --module ES2022 --outDir /tmp/gen_ts ts/decorators.ts && node /tmp/gen_ts/decorators.js > /tmp/gen_ts.json && urirun validate /tmp/gen_ts.json
php: ## Generate + validate bindings from the PHP attributes
	php php/example.php > /tmp/gen_php.json && urirun validate /tmp/gen_php.json
go: ## Generate + validate bindings from the Go descriptors
	go run go/example.go > /tmp/gen_go.json && urirun validate /tmp/gen_go.json
test: ## Validate every language generator that is installed
	@command -v node >/dev/null && $(MAKE) js nodejs || echo "skip js/nodejs (no node)"
	@command -v tsc  >/dev/null && $(MAKE) ts || echo "skip ts (no tsc)"
	@command -v php  >/dev/null && $(MAKE) php || echo "skip php (no php)"
	@command -v go   >/dev/null && $(MAKE) go || echo "skip go (no go)"
