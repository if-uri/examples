# Prefer the examples venv (../venv) so targets run without activating it first.
VENV_BIN := $(wildcard ../venv/bin)
ifneq ($(VENV_BIN),)
export PATH := $(abspath $(VENV_BIN)):$(PATH)
endif

.PHONY: help demo test

PYTHONPATH := ../../../adapters/python

help: ## Show commands
	@grep -E "^[a-zA-Z_-]+:.*?## .*$$" $(MAKEFILE_LIST) | awk "BEGIN{FS=\":.*?## \"}{printf \"  %-6s %s\\n\",\$$1,\$$2}"

demo: ## Run the transports demo
	PYTHONPATH=$(PYTHONPATH) python3 demo.py

test: ## Run the transports test
	PYTHONPATH=$(PYTHONPATH) python3 test_transports.py
