# Prefer the examples venv (../venv) so targets run without activating it first.
VENV_BIN := $(wildcard ../venv/bin)
ifneq ($(VENV_BIN),)
export PATH := $(abspath $(VENV_BIN)):$(PATH)
endif

.PHONY: run test help
help: ## Show commands
	@grep -E "^[a-zA-Z_-]+:.*?## .*$$" $(MAKEFILE_LIST) | awk "BEGIN{FS=\":.*?## \"}{printf \"  %-5s %s\\n\",\$$1,\$$2}"
run: ## Import the OpenAPI spec and call a route with a referenced secret
	python run.py
test: ## Same as run — it self-asserts (route runs, token never serialized)
	python run.py
