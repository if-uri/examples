.PHONY: run test help
help: ## Show commands
	@grep -E "^[a-zA-Z_-]+:.*?## .*$$" $(MAKEFILE_LIST) | awk "BEGIN{FS=\":.*?## \"}{printf \"  %-6s %s\\n\",\$$1,\$$2}"
run: ## Run the screen→OCR→VQL→LLM→alert flow
	python run.py
test: ## Adopt + validate + dispatch every vendored pack
	python test_packs.py
