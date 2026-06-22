# Prefer the examples venv (../venv) so targets run without activating it first.
VENV_BIN := $(wildcard ../venv/bin)
ifneq ($(VENV_BIN),)
export PATH := $(abspath $(VENV_BIN)):$(PATH)
endif

.PHONY: help registry run test test-docker clean

help: ## Show commands
	@grep -E "^[a-zA-Z_-]+:.*?## .*$$" $(MAKEFILE_LIST) | awk "BEGIN{FS=\":.*?## \"}{printf \"  %-12s %s\\n\",\$$1,\$$2}"

registry: ## Generate the registry
	bash generate_registry.sh

run: ## Run the flow
	bash run.sh

test-docker: ## Run the dockerized tests
	bash run_tests.sh

test: registry ## Run the flow tests
	python3 test_flow_runner.py
	python3 test_flow_e2e.py
	PYTHONPATH=../../../adapters/python python3 test_service_adapter.py
	docker compose config >/tmp/urirun-v2-docker-uri-flow.compose.yaml

clean: ## Tear down containers and generated files
	docker compose down -v --remove-orphans
	find generated -type f ! -name .gitignore -delete
