# Prefer the examples venv (../venv) so targets run without activating it first.
VENV_BIN := $(wildcard ../venv/bin)
ifneq ($(VENV_BIN),)
export PATH := $(abspath $(VENV_BIN)):$(PATH)
endif

.PHONY: public-smoke test up scenario down logs clean help

public-smoke: ## Run the public smoke test
	./scripts/public_smoke.sh

test: ## Run the full e2e scenario
	./scripts/run_full_scenario.sh

up: ## Build and start the stack
	docker compose up -d --build

scenario: ## Run the scenario against an already-running stack
	./scripts/run_full_scenario.sh --no-up

down: ## Stop and remove containers
	docker compose down -v --remove-orphans

logs: ## Tail container logs
	docker compose logs --tail=200

clean: ## Remove generated files
	rm -rf generated/*

help: ## Show commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  %-14s %s\n",$$1,$$2}'
