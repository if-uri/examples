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
