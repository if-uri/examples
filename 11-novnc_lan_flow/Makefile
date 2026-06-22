# Prefer the examples venv (../venv) so targets run without activating it first.
VENV_BIN := $(wildcard ../venv/bin)
ifneq ($(VENV_BIN),)
export PATH := $(abspath $(VENV_BIN)):$(PATH)
endif

.PHONY: up up-full flow flow-full test test-full down logs clean help

up:
	docker compose up -d --build
	@D=$${DASHBOARD_PORT:-8192}; P1V=$${PC1_NOVNC_PORT:-7901}; P2V=$${PC2_NOVNC_PORT:-7902}; P1A=$${PC1_API_PORT:-9001}; P2A=$${PC2_API_PORT:-9002}; \
	  printf 'dashboard: http://127.0.0.1:%s/?pc1NovncPort=%s&pc2NovncPort=%s&pc1ApiPort=%s&pc2ApiPort=%s\n' "$$D" "$$P1V" "$$P2V" "$$P1A" "$$P2A"
	@echo "pc1 noVNC: http://127.0.0.1:$${PC1_NOVNC_PORT:-7901}/?autoconnect=1&resize=scale"
	@echo "pc2 noVNC: http://127.0.0.1:$${PC2_NOVNC_PORT:-7902}/?autoconnect=1&resize=scale"

up-full:
	docker compose --profile full up -d --build
	@D=$${DASHBOARD_PORT:-8192}; P1V=$${PC1_NOVNC_PORT:-7901}; P2V=$${PC2_NOVNC_PORT:-7902}; P3V=$${PC3_NOVNC_PORT:-7903}; P4V=$${PC4_NOVNC_PORT:-7904}; P1A=$${PC1_API_PORT:-9001}; P2A=$${PC2_API_PORT:-9002}; P3A=$${PC3_API_PORT:-9003}; P4A=$${PC4_API_PORT:-9004}; \
	  printf 'dashboard: http://127.0.0.1:%s/?pcs=pc1,pc2,pc3,pc4&pc1NovncPort=%s&pc2NovncPort=%s&pc3NovncPort=%s&pc4NovncPort=%s&pc1ApiPort=%s&pc2ApiPort=%s&pc3ApiPort=%s&pc4ApiPort=%s\n' "$$D" "$$P1V" "$$P2V" "$$P3V" "$$P4V" "$$P1A" "$$P2A" "$$P3A" "$$P4A"

flow:
	python3 orchestrator/run_flow.py

flow-full:
	FLOW_MODE=full python3 orchestrator/run_flow.py

test:
	bash scripts/smoke.sh

test-full:
	FLOW_MODE=full bash scripts/smoke.sh

down:
	docker compose down -v --remove-orphans

logs:
	docker compose logs --tail=200

clean:
	rm -f generated/flow-result.json generated/smoke-output.json generated/screenshots/*.png
	mkdir -p generated/screenshots

help:
	@printf '%s\n' \
	  'make up       start dashboard + pc1/pc2 noVNC desktops' \
	  'make up-full  start dashboard + pc1..pc4 noVNC desktops' \
	  'make flow     run the browser:// URI flow against running desktops' \
	  'make flow-full run the four-computer URI flow' \
	  'make test     start pc1/pc2, run flow, verify screenshots' \
	  'make test-full start pc1..pc4, run flow, verify screenshots/services' \
	  'make down     stop containers'
