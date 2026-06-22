# Prefer the examples venv (../venv) so targets run without activating it first.
VENV_BIN := $(wildcard ../venv/bin)
ifneq ($(VENV_BIN),)
export PATH := $(abspath $(VENV_BIN)):$(PATH)
endif

.PHONY: help run test clean
help: ## Show commands
	@grep -E "^[a-zA-Z_-]+:.*?## .*$$" $(MAKEFILE_LIST) | awk "BEGIN{FS=\":.*?## \"}{printf \"  %-7s %s\\n\",\$$1,\$$2}"
run: ## Run the NL->YAML->execute->repair loop on a sample goal
	python3 agent_repair.py --execute "zapisz notatke o uruchomieniu"
dry: ## Same, but dry-run (plan only, nothing executes)
	python3 agent_repair.py "zapisz notatke o uruchomieniu"
test: ## Run the repair-loop tests
	python3 -m pytest test_repair.py -q
clean: ## Remove demo artifacts
	rm -f notes.json agent-run.log
