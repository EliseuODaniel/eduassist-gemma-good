SHELL := /bin/bash

COMPOSE_FILE := infra/compose/compose.yaml
ENV_FILE := .env

.PHONY: env install app llm-up llm-down llm-logs demo-up demo-down eval test lint fmt check

env:
	@if [ ! -f $(ENV_FILE) ]; then cp .env.example $(ENV_FILE); fi

install:
	uv sync --dev

app: env
	uv run streamlit run src/eduassist_gemma_good/app.py --server.port $${STREAMLIT_SERVER_PORT:-8501}

llm-up: env
	docker compose --profile local-llm --env-file $(ENV_FILE) -f $(COMPOSE_FILE) up -d --build local-llm-gemma4e4b

llm-down: env
	docker compose --profile local-llm --env-file $(ENV_FILE) -f $(COMPOSE_FILE) stop local-llm-gemma4e4b

llm-logs: env
	docker compose --profile local-llm --env-file $(ENV_FILE) -f $(COMPOSE_FILE) logs -f --tail=200 local-llm-gemma4e4b

demo-up: env
	docker compose --profile demo --profile local-llm --env-file $(ENV_FILE) -f $(COMPOSE_FILE) up -d --build

demo-down: env
	docker compose --profile demo --profile local-llm --env-file $(ENV_FILE) -f $(COMPOSE_FILE) down --remove-orphans

eval:
	uv run python -m eduassist_gemma_good.eval_runner

test:
	uv run python -m pytest -s tests

lint:
	uv run ruff check .

fmt:
	uv run ruff format .

check: lint test eval
