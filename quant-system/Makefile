PYTHON ?= python

.PHONY: install test run-api init-db seed-strategies startup-check demo-cycle replay deploy-openclaw

install:
	$(PYTHON) -m pip install -e .[dev]

test:
	$(PYTHON) -m pytest

run-api:
	$(PYTHON) -m uvicorn apps.agent_orchestrator.main:app --reload

init-db:
	$(PYTHON) scripts/init_db.py

seed-strategies:
	$(PYTHON) scripts/seed_strategies.py

startup-check:
	$(PYTHON) scripts/startup_check.py

demo-cycle:
	$(PYTHON) scripts/demo_cycle.py

replay:
	$(PYTHON) scripts/replay_events.py

deploy-openclaw:
	$(PYTHON) scripts/deploy_openclaw_workspaces.py
