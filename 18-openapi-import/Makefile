.PHONY: run test help
help: ## Show commands
	@grep -E "^[a-zA-Z_-]+:.*?## .*$$" $(MAKEFILE_LIST) | awk "BEGIN{FS=\":.*?## \"}{printf \"  %-5s %s\\n\",\$$1,\$$2}"
run: ## Import the OpenAPI spec and call a route with a referenced secret
	python run.py
test: ## Same as run — it self-asserts (route runs, token never serialized)
	python run.py
