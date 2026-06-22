# Prefer the examples venv (venv/) so `make` uses it without activating it first.
VENV_BIN := $(wildcard venv/bin)
ifneq ($(VENV_BIN),)
export PATH := $(abspath $(VENV_BIN)):$(PATH)
endif

.PHONY: connectors
connectors: ## Install urirun + every sibling Python connector editable (examples then run with no PYTHONPATH juggling)
	pip install -e ../urirun/adapters/python
	@for d in ../urirun-connector-*/; do \
	  if [ -f "$$d/pyproject.toml" ]; then echo "installing $$d"; pip install -q -e "$$d" --no-deps || exit 1; fi; \
	done

.PHONY: test
test: ## Run host-runnable checks for every NN-* example (Docker demos skipped)
	./run_tests.sh

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  %-12s %s\n",$$1,$$2}'

.PHONY: site deploy
site: ## Build the static examples site into _site/
	python3 scripts/build_site.py _site

deploy: ## Build + publish the site to examples.ifuri.com (Plesk)
	bash scripts/deploy-plesk.sh
