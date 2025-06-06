#!/bin/bash
# Script de instalação das ferramentas de desenvolvimento para Texta AI
# Uso: bash scripts/install-dev-tools.sh

set -e  # Sair em caso de erro

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Instalando ferramentas de desenvolvimento para Texta AI${NC}"
echo ""

# Verificar se Python está instalado
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo -e "${RED}❌ Python não encontrado. Instale o Python 3.9+ primeiro.${NC}"
    exit 1
fi

# Detectar comando Python
if command -v python3 &> /dev/null; then
    PYTHON=python3
    PIP=pip3
else
    PYTHON=python
    PIP=pip
fi

echo -e "${YELLOW}🐍 Usando Python: $($PYTHON --version)${NC}"

# Verificar versão do Python
PYTHON_VERSION=$($PYTHON -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
MIN_VERSION="3.9"

if ! $PYTHON -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)"; then
    echo -e "${RED}❌ Python $PYTHON_VERSION detectado. Este projeto requer Python $MIN_VERSION ou superior.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python $PYTHON_VERSION OK${NC}"

# Verificar se está em um ambiente virtual (recomendado)
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo -e "${GREEN}✅ Ambiente virtual detectado: $VIRTUAL_ENV${NC}"
else
    echo -e "${YELLOW}⚠️  Aviso: Não está em um ambiente virtual. Recomenda-se usar um venv.${NC}"
    echo -e "${YELLOW}   Para criar um: python -m venv .venv && source .venv/bin/activate${NC}"
    echo ""
fi

# Atualizar pip
echo -e "${YELLOW}📦 Atualizando pip...${NC}"
$PIP install --upgrade pip

# Instalar dependências principais
echo -e "${YELLOW}📦 Instalando dependências principais...${NC}"
$PIP install -r requirements.txt

# Instalar dependências de desenvolvimento via pyproject.toml
echo -e "${YELLOW}🛠️  Instalando dependências de desenvolvimento...${NC}"
$PIP install -e .[dev]

# Verificar instalação das ferramentas
echo ""
echo -e "${YELLOW}🔍 Verificando instalação das ferramentas...${NC}"

# Verificar Ruff
if command -v ruff &> /dev/null; then
    RUFF_VERSION=$(ruff --version)
    echo -e "${GREEN}✅ Ruff: $RUFF_VERSION${NC}"
else
    echo -e "${RED}❌ Ruff não instalado corretamente${NC}"
    exit 1
fi

# Verificar Black
if command -v black &> /dev/null; then
    BLACK_VERSION=$(black --version | head -n1)
    echo -e "${GREEN}✅ Black: $BLACK_VERSION${NC}"
else
    echo -e "${RED}❌ Black não instalado corretamente${NC}"
    exit 1
fi

# Verificar isort
if command -v isort &> /dev/null; then
    ISORT_VERSION=$(isort --version | head -n1)
    echo -e "${GREEN}✅ isort: $ISORT_VERSION${NC}"
else
    echo -e "${RED}❌ isort não instalado corretamente${NC}"
    exit 1
fi

# Verificar pytest
if command -v pytest &> /dev/null; then
    PYTEST_VERSION=$(pytest --version | head -n1)
    echo -e "${GREEN}✅ pytest: $PYTEST_VERSION${NC}"
else
    echo -e "${RED}❌ pytest não instalado corretamente${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 Instalação concluída com sucesso!${NC}"
echo ""
echo -e "${YELLOW}📋 Próximos passos:${NC}"
echo -e "  1. Execute ${GREEN}make help${NC} para ver comandos disponíveis"
echo -e "  2. Execute ${GREEN}make check${NC} para verificar o código"
echo -e "  3. Execute ${GREEN}make format${NC} para formatar o código"
echo -e "  4. Execute ${GREEN}make test${NC} para rodar os testes"
echo ""
echo -e "${YELLOW}💡 Comandos úteis:${NC}"
echo -e "  • ${GREEN}make all${NC}     - Pipeline completo (fix + format + check + test)"
echo -e "  • ${GREEN}make fix${NC}     - Correções automáticas"
echo -e "  • ${GREEN}make clean${NC}   - Limpar arquivos temporários"
echo ""
echo -e "${GREEN}✨ Desenvolvimento com qualidade configurado!${NC}" 