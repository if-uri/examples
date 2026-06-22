.PHONY: help tree flow test
help: ## Show commands
	@grep -E "^[a-zA-Z_-]+:.*?## .*$$" $(MAKEFILE_LIST) | awk "BEGIN{FS=\":.*?## \"}{printf \"  %-6s %s\\n\",\$$1,\$$2}"
tree: ## Regenerate uri-tree.yaml from the connect.ifuri.com catalog
	python build_uri_tree.py > uri-tree.yaml
flow: ## Emit the ops flow YAML (navigates uri-tree.yaml)
	python ops_flow.py
test: ## Verify the tree builds and the flow resolves its leaves
	python -c "import yaml,ops_flow; t=yaml.safe_load(open('uri-tree.yaml'))['uri_tree']; assert len(t)>=8; assert ops_flow.flow.steps; print('uri_tree:',len(t),'connectors; flow:',len(ops_flow.flow.steps),'steps — ok')"
