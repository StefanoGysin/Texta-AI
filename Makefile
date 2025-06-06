# Makefile para Texta AI - Ferramentas de Desenvolvimento
# Uso: make [comando]

.PHONY: help install dev-install check format format-black fix lint test coverage clean all setup

# Detectar Python 
PYTHON := $(shell command -v python3 2>/dev/null || command -v python 2>/dev/null)
PIP := $(shell command -v pip3 2>/dev/null || command -v pip 2>/dev/null)

# Diretórios principais
SRC_DIR := src
TEST_DIR := tests
SCRIPTS_DIR := scripts

# Cores para output
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Mostra esta mensagem de ajuda
	@echo "$(GREEN)Texta AI - Ferramentas de Desenvolvimento$(NC)"
	@echo ""
	@echo "$(YELLOW)Comandos disponíveis:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(YELLOW)Exemplos:$(NC)"
	@echo "  make setup     # Configuração inicial completa"
	@echo "  make all       # Executa fix + format + check"
	@echo "  make test      # Roda todos os testes com cobertura"

setup: install dev-install ## Configuração inicial completa do ambiente de desenvolvimento
	@echo "$(GREEN)✅ Ambiente configurado com sucesso!$(NC)"

install: ## Instala dependências principais
	@echo "$(YELLOW)📦 Instalando dependências principais...$(NC)"
	$(PIP) install -r requirements.txt

dev-install: ## Instala dependências de desenvolvimento
	@echo "$(YELLOW)🛠️  Instalando dependências de desenvolvimento...$(NC)"
	$(PIP) install -e .[dev]

check: ## Executa verificação de linting com Ruff
	@echo "$(YELLOW)🔍 Executando verificação de linting...$(NC)"
	ruff check $(SRC_DIR) $(TEST_DIR) $(SCRIPTS_DIR)

format: ## Formata código com Ruff (recomendado)
	@echo "$(YELLOW)🎨 Formatando código com Ruff...$(NC)"
	ruff format $(SRC_DIR) $(TEST_DIR) $(SCRIPTS_DIR)

format-black: ## Formata código com Black + isort (alternativo)
	@echo "$(YELLOW)🎨 Formatando código com Black + isort...$(NC)"
	isort $(SRC_DIR) $(TEST_DIR) $(SCRIPTS_DIR)
	black $(SRC_DIR) $(TEST_DIR) $(SCRIPTS_DIR)

fix: ## Executa correções automáticas com Ruff
	@echo "$(YELLOW)🔧 Executando correções automáticas...$(NC)"
	ruff check --fix $(SRC_DIR) $(TEST_DIR) $(SCRIPTS_DIR)

lint: check ## Alias para check

test: ## Executa todos os testes com cobertura
	@echo "$(YELLOW)🧪 Executando testes...$(NC)"
	pytest

test-fast: ## Executa testes sem cobertura (mais rápido)
	@echo "$(YELLOW)⚡ Executando testes rápidos...$(NC)"
	pytest --no-cov

coverage: ## Gera relatório de cobertura HTML
	@echo "$(YELLOW)📊 Gerando relatório de cobertura...$(NC)"
	pytest --cov-report=html
	@echo "$(GREEN)Relatório disponível em htmlcov/index.html$(NC)"

clean: ## Remove arquivos temporários e cache
	@echo "$(YELLOW)🧹 Limpando arquivos temporários...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	find . -type f -name "*.log" -delete

all: fix format check test ## Executa pipeline completo (fix + format + check + test)
	@echo "$(GREEN)🎉 Pipeline completo executado com sucesso!$(NC)"

# Comandos específicos para CI/CD
ci-check: ## Verifica código sem fazer alterações (para CI)
	@echo "$(YELLOW)🔍 Verificação CI/CD...$(NC)"
	ruff check $(SRC_DIR) $(TEST_DIR) $(SCRIPTS_DIR)
	ruff format --check $(SRC_DIR) $(TEST_DIR) $(SCRIPTS_DIR)

ci-test: ## Executa testes para CI/CD
	@echo "$(YELLOW)🧪 Testes CI/CD...$(NC)"
	pytest --cov-report=xml --cov-fail-under=65

# Comandos de desenvolvimento avançado
profile: ## Executa profiling básico do código principal
	@echo "$(YELLOW)⚡ Executando profiling...$(NC)"
	$(PYTHON) -m cProfile -s cumulative $(SRC_DIR)/main.py

run: ## Executa a aplicação principal
	@echo "$(YELLOW)🚀 Executando Texta AI...$(NC)"
	$(PYTHON) $(SRC_DIR)/main.py

run-gui: ## Executa a aplicação com GUI
	@echo "$(YELLOW)🖥️  Executando Texta AI (modo GUI)...$(NC)"
	$(PYTHON) $(SRC_DIR)/main.py --gui

# Verificações de ambiente
check-python: ## Verifica instalação do Python
	@echo "$(YELLOW)🐍 Verificando Python...$(NC)"
	@$(PYTHON) --version || (echo "$(RED)❌ Python não encontrado$(NC)" && exit 1)
	@echo "$(GREEN)✅ Python: $(shell $(PYTHON) --version)$(NC)"

check-deps: ## Verifica dependências instaladas
	@echo "$(YELLOW)📦 Verificando dependências...$(NC)"
	@$(PIP) list | grep -E "(ruff|black|isort|pytest)" || echo "$(RED)❌ Algumas dependências não estão instaladas$(NC)"

# Comando de informações do projeto
info: ## Mostra informações do projeto
	@echo "$(GREEN)📋 Informações do Projeto$(NC)"
	@echo "Nome: Texta AI"
	@echo "Versão: 1.0.0"
	@echo "Python: $(shell $(PYTHON) --version)"
	@echo "Diretórios:"
	@echo "  - Código fonte: $(SRC_DIR)/"
	@echo "  - Testes: $(TEST_DIR)/"
	@echo "  - Scripts: $(SCRIPTS_DIR)/"
	@echo ""
	@echo "$(YELLOW)Ferramentas configuradas:$(NC)"
	@echo "  - Ruff: Linting e formatação"
	@echo "  - Black: Formatação alternativa"
	@echo "  - isort: Organização de imports"
	@echo "  - pytest: Framework de testes"

# Comando padrão
.DEFAULT_GOAL := help 