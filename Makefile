PYTHON ?= python3
VENV := .venv
BIN := $(VENV)/bin
DJANGO := $(BIN)/python manage.py

.PHONY: install up down migrate seed run test lint fmt shell

## install: create venv and install dependencies
install:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -r requirements.txt

## up: start Postgres and Redis via Docker Compose
up:
	docker compose up -d

## down: stop Docker Compose services (data volume is kept)
down:
	docker compose down

## migrate: apply database migrations
migrate:
	$(DJANGO) migrate

## seed: create the 5 demo users (one per role)
seed:
	$(DJANGO) seed_demo_users

## run: start the Django dev server on http://localhost:8000
run:
	$(DJANGO) runserver

## test: run the test suite
test:
	$(BIN)/python -m pytest

## lint: check with ruff and black (mypy runs on services.py per CLAUDE.md)
lint:
	$(BIN)/ruff check .
	$(BIN)/black --check .
	@files=$$(find apps -name "services.py" | tr '\n' ' '); \
	if [ -n "$$files" ]; then \
		$(BIN)/python -m mypy $$files; \
	else \
		echo "mypy: no services.py yet (nothing to type-check)"; \
	fi

## fmt: format with black and ruff
fmt:
	$(BIN)/black .
	$(BIN)/ruff check --fix .

## shell: open a Django shell
shell:
	$(DJANGO) shell
