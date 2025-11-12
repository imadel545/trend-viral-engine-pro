# ═══════════════════════════════════════════════════════════════════
# TREND & VIRAL ENGINE PRO - MAKEFILE
# ═══════════════════════════════════════════════════════════════════
# Commandes disponibles: make help
# ═══════════════════════════════════════════════════════════════════

.DEFAULT_GOAL := help
SHELL := /bin/bash
PYTHON := python3
PIP := $(PYTHON) -m pip
PYTEST := pytest
UVICORN := uvicorn

# ───────────────────────────────────────────────────────────────────
# Colors for pretty output
# ───────────────────────────────────────────────────────────────────
CYAN := \033[0;36m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m

# ═══════════════════════════════════════════════════════════════════
# HELP
# ═══════════════════════════════════════════════════════════════════
.PHONY: help
help: ## Afficher l'aide
	@echo ""
	@echo "$(CYAN)╔═══════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(CYAN)║  TREND & VIRAL ENGINE PRO - Commandes disponibles            ║$(NC)"
	@echo "$(CYAN)╚═══════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "Usage: make $(CYAN)<target>$(NC)\n\n"} \
		/^[a-zA-Z_-]+:.*?##/ { \
			printf "  $(CYAN)%-20s$(NC) %s\n", $$1, $$2 \
		}' $(MAKEFILE_LIST)
	@echo ""

# ═══════════════════════════════════════════════════════════════════
# INSTALLATION
# ═══════════════════════════════════════════════════════════════════
.PHONY: install install-core install-dev install-ml install-full

install: install-full ## Installation complète (alias de install-full)

install-core: ## Installation runtime production uniquement
	@echo "$(YELLOW)Installing core dependencies...$(NC)"
	./install.sh core

install-dev: ## Installation runtime + dev tools
	@echo "$(YELLOW)Installing core + dev dependencies...$(NC)"
	./install.sh dev

install-ml: ## Installation runtime + dev + ML avancé
	@echo "$(YELLOW)Installing core + dev + ML advanced...$(NC)"
	./install.sh full

install-full: ## Installation complète (core + dev + ML + editable)
	@echo "$(YELLOW)Running full installation...$(NC)"
	./install.sh full

# ═══════════════════════════════════════════════════════════════════
# ENVIRONNEMENT
# ═══════════════════════════════════════════════════════════════════
.PHONY: venv clean-venv env-check

venv: ## Créer un environnement virtuel
	@echo "$(YELLOW)Creating virtual environment...$(NC)"
	$(PYTHON) -m venv venv
	@echo "$(GREEN)✓ Venv created. Activate with: source venv/bin/activate$(NC)"

clean-venv: ## Supprimer l'environnement virtuel
	@echo "$(RED)Removing virtual environment...$(NC)"
	rm -rf venv
	@echo "$(GREEN)✓ Venv removed$(NC)"

env-check: ## Vérifier la configuration .env
	@if [ ! -f .env ]; then \
		echo "$(RED)✗ .env not found$(NC)"; \
		echo "$(YELLOW)Creating from .env.example...$(NC)"; \
		cp .env.example .env; \
		echo "$(GREEN)✓ .env created - EDIT IT WITH YOUR API KEYS$(NC)"; \
	else \
		echo "$(GREEN)✓ .env exists$(NC)"; \
		grep -q "GROQ_API_KEY=your" .env && \
			echo "$(YELLOW)⚠  GROQ_API_KEY not configured$(NC)" || \
			echo "$(GREEN)✓ GROQ_API_KEY configured$(NC)"; \
	fi

# ═══════════════════════════════════════════════════════════════════
# TESTS
# ═══════════════════════════════════════════════════════════════════
.PHONY: test test-unit test-integration test-e2e test-cov test-fast

test: ## Lancer tous les tests
	@echo "$(YELLOW)Running all tests...$(NC)"
	$(PYTEST) tests/ -v --tb=short

test-unit: ## Lancer uniquement les tests unitaires
	@echo "$(YELLOW)Running unit tests...$(NC)"
	$(PYTEST) tests/ -v -m unit --tb=short

test-integration: ## Lancer les tests d'intégration
	@echo "$(YELLOW)Running integration tests...$(NC)"
	$(PYTEST) tests/ -v -m integration --tb=short

test-e2e: ## Lancer les tests end-to-end
	@echo "$(YELLOW)Running E2E tests...$(NC)"
	$(PYTEST) tests/ -v -m e2e --tb=short

test-cov: ## Lancer les tests avec coverage
	@echo "$(YELLOW)Running tests with coverage...$(NC)"
	$(PYTEST) tests/ -v --cov=src --cov-report=term-missing --cov-report=html
	@echo "$(GREEN)✓ Coverage report: htmlcov/index.html$(NC)"

test-fast: ## Lancer tests rapides (sans les slow)
	@echo "$(YELLOW)Running fast tests...$(NC)"
	$(PYTEST) tests/ -v -m "not slow" --tb=short

# ═══════════════════════════════════════════════════════════════════
# CODE QUALITY
# ═══════════════════════════════════════════════════════════════════
.PHONY: format lint type-check quality

format: ## Formatter le code (black + isort)
	@echo "$(YELLOW)Formatting code...$(NC)"
	black src/ tests/ scripts/
	isort src/ tests/ scripts/
	@echo "$(GREEN)✓ Code formatted$(NC)"

lint: ## Linter le code (ruff)
	@echo "$(YELLOW)Linting code...$(NC)"
	ruff check src/ tests/ scripts/
	@echo "$(GREEN)✓ Linting complete$(NC)"

type-check: ## Vérifier les types (mypy)
	@echo "$(YELLOW)Type checking...$(NC)"
	mypy src/ --ignore-missing-imports
	@echo "$(GREEN)✓ Type checking complete$(NC)"

quality: format lint type-check ## Vérifications complètes (format + lint + type)

# ═══════════════════════════════════════════════════════════════════
# DÉVELOPPEMENT
# ═══════════════════════════════════════════════════════════════════
.PHONY: run run-dev run-prod api

run: run-dev ## Lancer l'API (alias de run-dev)

run-dev: env-check ## Lancer l'API en mode développement (hot reload)
	@echo "$(GREEN)Starting API in development mode...$(NC)"
	@echo "$(CYAN)API docs: http://localhost:8000/docs$(NC)"
	$(UVICORN) src.api.main:app --reload --host 0.0.0.0 --port 8000

run-prod: env-check ## Lancer l'API en mode production
	@echo "$(GREEN)Starting API in production mode...$(NC)"
	$(UVICORN) src.api.main:app --host 0.0.0.0 --port 8000 --workers 4

api: run-dev ## Alias de run-dev

# ═══════════════════════════════════════════════════════════════════
# ML PIPELINE
# ═══════════════════════════════════════════════════════════════════
.PHONY: collect-data train-model evaluate-model

collect-data: ## Collecter des données (mock pour tests)
	@echo "$(YELLOW)Collecting mock data...$(NC)"
	$(PYTHON) scripts/fix_ingestion.py
	@echo "$(GREEN)✓ Data collected in data/raw/$(NC)"

train-model: ## Entraîner le modèle baseline
	@echo "$(YELLOW)Training baseline model...$(NC)"
	$(PYTHON) scripts/training/train_baseline.py --min-samples 5
	@echo "$(GREEN)✓ Model saved in models/$(NC)"

evaluate-model: ## Évaluer le modèle
	@echo "$(YELLOW)Evaluating model...$(NC)"
	$(PYTHON) scripts/training/evaluate.py
	@echo "$(GREEN)✓ Evaluation complete$(NC)"

pipeline-e2e: collect-data train-model ## Pipeline E2E complet (collect → train)
	@echo "$(GREEN)✓ E2E pipeline complete$(NC)"

# ═══════════════════════════════════════════════════════════════════
# DOCKER
# ═══════════════════════════════════════════════════════════════════
.PHONY: docker-build docker-up docker-down docker-restart docker-logs start stop restart logs

docker-build: ## Construire l'image Docker
	@echo "$(YELLOW)Building Docker image...$(NC)"
	docker-compose build
	@echo "$(GREEN)✓ Docker image built$(NC)"

docker-up: ## Démarrer les services Docker
	@echo "$(YELLOW)Starting Docker services...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✓ Services started$(NC)"
	@echo "$(CYAN)API: http://localhost:8000$(NC)"
	@echo "$(CYAN)MLflow: http://localhost:5000$(NC)"
	@echo "$(CYAN)Prometheus: http://localhost:9090$(NC)"
	@echo "$(CYAN)Grafana: http://localhost:3000$(NC)"

docker-down: ## Arrêter les services Docker
	@echo "$(YELLOW)Stopping Docker services...$(NC)"
	docker-compose down
	@echo "$(GREEN)✓ Services stopped$(NC)"

docker-restart: docker-down docker-up ## Redémarrer les services Docker

docker-logs: ## Afficher les logs Docker
	docker-compose logs -f

# Aliases historiques
start: docker-up
stop: docker-down
restart: docker-restart
logs: docker-logs

# ═══════════════════════════════════════════════════════════════════
# NETTOYAGE
# ═══════════════════════════════════════════════════════════════════
.PHONY: clean clean-data clean-models clean-logs clean-pycache clean-all

clean: clean-pycache ## Nettoyage léger (cache Python)

clean-data: ## Supprimer les données collectées
	@echo "$(RED)Removing data files...$(NC)"
	rm -rf data/raw/* data/features/* data/feedback/*
	@echo "$(GREEN)✓ Data cleaned$(NC)"

clean-models: ## Supprimer les modèles entraînés
	@echo "$(RED)Removing models...$(NC)"
	rm -rf models/*.pkl models/*.joblib
	@echo "$(GREEN)✓ Models cleaned$(NC)"

clean-logs: ## Supprimer les logs
	@echo "$(RED)Removing logs...$(NC)"
	rm -rf logs/*.log
	@echo "$(GREEN)✓ Logs cleaned$(NC)"

clean-pycache: ## Supprimer les caches Python
	@echo "$(YELLOW)Removing Python cache...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov/ .coverage
	@echo "$(GREEN)✓ Cache cleaned$(NC)"

clean-all: clean-data clean-models clean-logs clean-pycache ## Nettoyage complet
	@echo "$(GREEN)✓ Full cleanup complete$(NC)"

# ═══════════════════════════════════════════════════════════════════
# MONITORING
# ═══════════════════════════════════════════════════════════════════
.PHONY: mlflow grafana prometheus

mlflow: ## Ouvrir MLflow UI
	@echo "$(CYAN)Opening MLflow at http://localhost:5000$(NC)"
	@open http://localhost:5000 2>/dev/null || xdg-open http://localhost:5000 2>/dev/null || echo "Visit http://localhost:5000"

grafana: ## Ouvrir Grafana UI
	@echo "$(CYAN)Opening Grafana at http://localhost:3000$(NC)"
	@open http://localhost:3000 2>/dev/null || xdg-open http://localhost:3000 2>/dev/null || echo "Visit http://localhost:3000"

prometheus: ## Ouvrir Prometheus UI
	@echo "$(CYAN)Opening Prometheus at http://localhost:9090$(NC)"
	@open http://localhost:9090 2>/dev/null || xdg-open http://localhost:9090 2>/dev/null || echo "Visit http://localhost:9090"

# ═══════════════════════════════════════════════════════════════════
# DOCUMENTATION
# ═══════════════════════════════════════════════════════════════════
.PHONY: docs docs-serve

docs: ## Générer la documentation
	@echo "$(YELLOW)Building documentation...$(NC)"
	mkdocs build
	@echo "$(GREEN)✓ Documentation built in site/$(NC)"

docs-serve: ## Servir la documentation localement
	@echo "$(CYAN)Serving docs at http://localhost:8001$(NC)"
	mkdocs serve -a localhost:8001

# ═══════════════════════════════════════════════════════════════════
# ORCHESTRATION
# ═══════════════════════════════════════════════════════════════════
.PHONY: deploy

deploy: ## Déployer les flows Prefect
	@echo "$(YELLOW)Deploying Prefect flows...$(NC)"
	$(PYTHON) scripts/flows/deployments.py
	@echo "$(GREEN)✓ Flows deployed$(NC)"

# ═══════════════════════════════════════════════════════════════════
# DEBUGGING
# ═══════════════════════════════════════════════════════════════════
.PHONY: debug-install debug-env debug-imports

debug-install: ## Debugger l'installation
	@echo "$(CYAN)Python version:$(NC)"
	@$(PYTHON) --version
	@echo ""
	@echo "$(CYAN)Pip version:$(NC)"
	@$(PIP) --version
	@echo ""
	@echo "$(CYAN)Installed packages:$(NC)"
	@$(PIP) list | head -n 20
	@echo "$(YELLOW)... (truncated, total: $$($(PIP) list | wc -l) packages)$(NC)"

debug-env: ## Afficher les variables d'environnement
	@echo "$(CYAN)Environment variables:$(NC)"
	@env | grep -E "^(PYTHON|GROQ|REDDIT|GOOGLE)" || echo "No relevant env vars"

debug-imports: ## Tester les imports critiques
	@echo "$(YELLOW)Testing critical imports...$(NC)"
	@$(PYTHON) -c "import fastapi; print('✓ fastapi:', fastapi.__version__)"
	@$(PYTHON) -c "import torch; print('✓ torch:', torch.__version__)"
	@$(PYTHON) -c "import transformers; print('✓ transformers:', transformers.__version__)"
	@$(PYTHON) -c "import lightgbm; print('✓ lightgbm:', lightgbm.__version__)"
	@$(PYTHON) -c "import pandas; print('✓ pandas:', pandas.__version__)"
	@echo "$(GREEN)✓ All imports successful$(NC)"

# ═══════════════════════════════════════════════════════════════════
# CI/CD
# ═══════════════════════════════════════════════════════════════════
.PHONY: ci pre-commit

ci: quality test-cov ## Pipeline CI complète (quality + tests avec coverage)
	@echo "$(GREEN)✓ CI pipeline complete$(NC)"

pre-commit: ## Installer pre-commit hooks
	@echo "$(YELLOW)Installing pre-commit hooks...$(NC)"
	pre-commit install
	@echo "$(GREEN)✓ Pre-commit hooks installed$(NC)"

# ═══════════════════════════════════════════════════════════════════
# MISC
# ═══════════════════════════════════════════════════════════════════
.PHONY: version tree

version: ## Afficher les versions
	@echo "$(CYAN)╔═══════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(CYAN)║  VERSIONS$(NC)"
	@echo "$(CYAN)╚═══════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(GREEN)Python:$(NC)       $$($(PYTHON) --version)"
	@echo "$(GREEN)PyTorch:$(NC)      $$($(PYTHON) -c 'import torch; print(torch.__version__)')"
	@echo "$(GREEN)Transformers:$(NC) $$($(PYTHON) -c 'import transformers; print(transformers.__version__)')"
	@echo "$(GREEN)FastAPI:$(NC)      $$($(PYTHON) -c 'import fastapi; print(fastapi.__version__)')"
	@echo "$(GREEN)LightGBM:$(NC)     $$($(PYTHON) -c 'import lightgbm; print(lightgbm.__version__)')"

tree: ## Afficher la structure du projet
	@echo "$(CYAN)Project structure:$(NC)"
	@tree -L 2 -I 'venv|__pycache__|*.pyc|.git|node_modules|htmlcov' --dirsfirst
