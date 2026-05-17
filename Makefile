.PHONY: setup validate test lint format typecheck repo-hygiene policy-integrity security docker-build docker-test demo clean check-python

# Target interpreter: Python 3.12 (see .python-version). Override if needed.
PYTHON ?= python3.12
VENV ?= .venv
BIN := $(VENV)/bin

setup: check-host-python
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -e ".[dev]"
	$(BIN)/python scripts/check_python_version.py

check-host-python:
	@command -v $(PYTHON) >/dev/null 2>&1 || { \
		echo "ERROR: $(PYTHON) not found. Install Python 3.12 or set PYTHON=python3.12"; \
		exit 1; \
	}

check-python:
	$(BIN)/python scripts/check_python_version.py

validate: check-python lint format-check typecheck test repo-hygiene policy-integrity security docker-build docker-test

repo-hygiene: check-python
	$(BIN)/python scripts/validate_repo.py

policy-integrity: check-python
	$(BIN)/python scripts/validate_policy.py

test: check-python
	$(BIN)/python -m pytest

lint: check-python
	$(BIN)/python -m ruff check .

format: check-python
	$(BIN)/python -m ruff format .

format-check: check-python
	$(BIN)/python -m ruff format --check .

typecheck: check-python
	$(BIN)/python -m mypy src tests scripts/validate_repo.py scripts/validate_policy.py

security: check-python
	$(BIN)/python -m bandit -r src
	$(BIN)/python -m pip_audit

docker-build:
	docker compose build

docker-test:
	docker compose run --rm app python -m pytest

demo: check-python
	$(BIN)/python -m agent_control_plane.demo

clean:
	rm -rf $(VENV) .pytest_cache .mypy_cache .ruff_cache htmlcov dist build *.egg-info audit_logs
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
