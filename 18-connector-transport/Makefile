# Prefer the examples venv (../venv) so targets run without activating it first.
VENV_BIN := $(wildcard ../venv/bin)
ifneq ($(VENV_BIN),)
export PATH := $(abspath $(VENV_BIN)):$(PATH)
endif

.PHONY: help run test down
help: ## Show commands
	@grep -E "^[a-zA-Z_-]+:.*?## .*$$" $(MAKEFILE_LIST) | awk "BEGIN{FS=\":.*?## \"}{printf \"  %-6s %s\\n\",\$$1,\$$2}"
run: ## Run the connector-over-HTTP demo (docker compose)
	docker compose up --abort-on-container-exit --exit-code-from client
test: run ## Same as run — the client asserts the contract
down: ## Tear down the demo stack
	docker compose down -v --remove-orphans
