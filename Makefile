.PHONY: help setup setup-backend setup-frontend dev dev-backend dev-frontend test format lint build reset-db clean

VENV := .venv
PIP := $(VENV)/bin/pip
PYTHON := $(VENV)/bin/python
UVICORN := $(VENV)/bin/uvicorn
ALEMBIC := cd backend && ../$(VENV)/bin/alembic
TY := cd backend && ../$(VENV)/bin/ty

# Default target
help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# ─── Setup ────────────────────────────────────────────────────────────────────

setup: setup-backend setup-frontend ## First-time setup (backend + frontend)

setup-backend: ## Create venv, install deps, run migrations
	python3 -m venv $(VENV)
	$(PIP) install -r backend/requirements.txt
	$(ALEMBIC) upgrade head

setup-frontend: ## Install frontend npm packages
	cd frontend && npm install

# ─── Development ──────────────────────────────────────────────────────────────

dev: ## Start backend and frontend concurrently
	@echo "Starting backend on :8000 and frontend on :5173..."
	@trap 'kill 0' INT TERM; \
		$(MAKE) dev-backend & \
		$(MAKE) dev-frontend & \
		wait

dev-backend: ## Start backend server (port 8000)
	cd backend && ../$(UVICORN) app.main:app --reload --port 8000

dev-frontend: ## Start frontend dev server (port 5173)
	cd frontend && npm run dev

# ─── Testing & Quality ───────────────────────────────────────────────────────

test: ## Run backend tests
	cd backend && ../$(PYTHON) -m pytest -v

format: ## Auto-format and type-check backend code
	$(VENV)/bin/ruff check --fix backend/
	$(VENV)/bin/ruff format backend/
	$(TY) check

lint: ## Check backend and frontend linting
	$(VENV)/bin/ruff check backend/
	$(VENV)/bin/ruff format --check backend/
	$(TY) check
	cd frontend && npm run lint

# ─── Build ────────────────────────────────────────────────────────────────────

build: ## Build frontend for production
	cd frontend && npm run build

# ─── Database ─────────────────────────────────────────────────────────────────

reset-db: ## Delete the database and re-run migrations from scratch
	rm -f backend/games.db
	$(ALEMBIC) upgrade head
	@echo "Database reset complete."

# ─── Cleanup ──────────────────────────────────────────────────────────────────

clean: ## Remove venv, node_modules, and build artifacts
	rm -rf $(VENV) backend/__pycache__ backend/app/__pycache__
	rm -rf frontend/node_modules frontend/dist
	@echo "Cleaned up. Run 'make setup' to reinstall."
