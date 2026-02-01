# QualCoder v2 Development Makefile
# =================================

.PHONY: init install-deps sync install-hooks test test-unit test-all lint format pre-commit clean help

# Default target
.DEFAULT_GOAL := help

# Environment variables for headless Qt
export QT_QPA_PLATFORM ?= offscreen

# =============================================================================
# Setup
# =============================================================================

init: install-deps sync install-hooks ## Full initialization: install system deps + uv sync + pre-commit hooks
	@echo "Initialization complete!"

install-deps: ## Install required system libraries for Qt
	@echo "Installing system dependencies..."
	@if command -v apt-get >/dev/null 2>&1; then \
		sudo apt-get update -qq && \
		sudo apt-get install -y -qq libegl1 libxkbcommon0 2>/dev/null || \
		apt-get update -qq && apt-get install -y -qq libegl1 libxkbcommon0; \
	else \
		echo "Warning: apt-get not available, skipping system deps"; \
	fi
	@echo "System dependencies installed."

sync: ## Run uv sync with all extras
	@echo "Syncing Python dependencies..."
	uv sync --all-extras
	@echo "Python dependencies synced."

install-hooks: ## Install pre-commit hooks
	@echo "Installing pre-commit hooks..."
	uv run pre-commit install
	@echo "Pre-commit hooks installed."

# =============================================================================
# Testing
# =============================================================================

test: ## Run all project-related tests (domain, application, infrastructure, viewmodel)
	uv run pytest \
		src/domain/projects/tests/ \
		src/application/projects/tests/ \
		src/infrastructure/projects/tests/ \
		src/presentation/viewmodels/tests/test_file_manager_viewmodel.py \
		-v

test-unit: ## Run unit tests only (fast, no Qt required)
	uv run pytest -m unit -v -p no:pytest-qt

test-all: ## Run entire test suite
	uv run pytest -v

test-coverage: ## Run tests with coverage report
	uv run pytest --cov=src --cov-report=term-missing -v

# =============================================================================
# Code Quality
# =============================================================================

lint: ## Run ruff linter
	uv run ruff check src/ design_system/

format: ## Format code with ruff
	uv run ruff format src/ design_system/
	uv run ruff check --fix src/ design_system/

pre-commit: ## Run pre-commit checks on all files
	uv run pre-commit run --all-files

typecheck: ## Run type checking (if mypy is available)
	uv run mypy src/ --ignore-missing-imports || echo "mypy not configured"

# =============================================================================
# Development
# =============================================================================

run: ## Run the application
	uv run python -m src.main

shell: ## Open Python shell with project context
	uv run python -c "from src.presentation import *; print('QualCoder v2 shell ready')" -i

# =============================================================================
# Cleanup
# =============================================================================

clean: ## Remove build artifacts and caches
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	rm -rf __pycache__/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "Cleaned build artifacts."

clean-all: clean ## Remove all generated files including .venv
	rm -rf .venv/
	@echo "Cleaned virtual environment."

# =============================================================================
# Help
# =============================================================================

help: ## Show this help message
	@echo "QualCoder v2 Development Commands"
	@echo "================================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Examples:"
	@echo "  make init        # First-time setup"
	@echo "  make test        # Run project tests"
	@echo "  make lint        # Check code style"
