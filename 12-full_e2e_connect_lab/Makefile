.PHONY: public-smoke test up scenario down logs clean help

public-smoke:
	./scripts/public_smoke.sh

test:
	./scripts/run_full_scenario.sh

up:
	docker compose up -d --build

scenario:
	./scripts/run_full_scenario.sh --no-up

down:
	docker compose down -v --remove-orphans

logs:
	docker compose logs --tail=200

clean:
	rm -rf generated/*

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  %-14s %s\n",$$1,$$2}'
