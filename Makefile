# Prefer the examples venv (venv/) so `make` uses it without activating it first.
VENV_BIN := $(wildcard venv/bin)
ifneq ($(VENV_BIN),)
export PATH := $(abspath $(VENV_BIN)):$(PATH)
endif

.PHONY: connectors
connectors: ## Install urirun + sibling libs + every Python connector editable (examples then run with no PYTHONPATH juggling)
	pip install -e ../urirun-contract
	pip install -e ../urirun/adapters/python
	@for d in ../urirun-*/; do \
	  case "$$d" in */urirun-contract/|*/urirun-connector-*) continue;; esac; \
	  if [ -f "$$d/pyproject.toml" ]; then echo "installing lib $$d"; pip install -q -e "$$d" --no-deps || exit 1; fi; \
	done
	@for d in ../urirun-connector-*/; do \
	  if [ -f "$$d/pyproject.toml" ]; then echo "installing $$d"; pip install -q -e "$$d" --no-deps || exit 1; fi; \
	done

.PHONY: test
test: ## Run the fast host smoke (Docker demos skipped; not every pytest example)
	./run_tests.sh

.PHONY: test-all
test-all: ## Run the full host pytest suite for examples/
	PYTHONPATH=../urirun/adapters/python python -m pytest -q .

.PHONY: audit
audit: ## Report examples test coverage versus the smoke runner
	python scripts/audit_test_coverage.py --verbose

.PHONY: test-connectors
test-connectors: ## Run pytest for every sibling Python connector with a tests/ dir (runs all, reports the failures)
	@fail=0; n=0; failed=""; \
	for d in ../urirun-connector-*/; do \
	  if [ -d "$$d/tests" ]; then \
	    n=$$((n+1)); echo "== $$d =="; \
	    ( cd "$$d" && PYTHONPATH=. python -m pytest tests -q ) || { fail=1; failed="$$failed $$(basename $$d)"; }; \
	  fi; \
	done; \
	echo "----------------------------------------"; \
	if [ "$$fail" = "0" ]; then echo "all $$n connector suites passed"; else echo "FAILED:$$failed"; fi; \
	exit $$fail

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  %-12s %s\n",$$1,$$2}'

.PHONY: site deploy
site: ## Build the static examples site into _site/
	python3 scripts/build_site.py _site

deploy: ## Build + publish the site to examples.ifuri.com (Plesk)
	bash scripts/deploy-plesk.sh
