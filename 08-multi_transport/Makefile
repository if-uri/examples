# Prefer the examples venv (../venv) so targets run without activating it first.
VENV_BIN := $(wildcard ../venv/bin)
ifneq ($(VENV_BIN),)
export PATH := $(abspath $(VENV_BIN)):$(PATH)
endif

.PHONY: help test test-docker clean

help: ## Show commands
	@grep -E "^[a-zA-Z_-]+:.*?## .*$$" $(MAKEFILE_LIST) | awk "BEGIN{FS=\":.*?## \"}{printf \"  %-12s %s\\n\",\$$1,\$$2}"

test-docker: ## Run the dockerized tests
	bash run_tests.sh

test: test-docker ## Run the dockerized tests (standard examples target)

clean: ## Tear down the test containers
	docker compose -f docker-compose.test.yml down -v --remove-orphans
