# 🛠️ Ferramentas de Desenvolvimento - Texta AI

Este documento descreve as ferramentas de qualidade de código configuradas no projeto Texta AI.

## 📋 Visão Geral

O projeto está configurado com as melhores ferramentas da comunidade Python para garantir código de alta qualidade:

- **🚀 Ruff** - Linting e formatação ultra-rápidos (substitui Flake8, Black, isort)
- **🎨 Black** - Formatação de código padrão da comunidade
- **📦 isort** - Organização automática de imports
- **🧪 pytest** - Framework de testes com cobertura

## 🔧 Instalação

### Método 1: Script Automatizado (Recomendado)
```bash
bash scripts/install-dev-tools.sh
```

### Método 2: Makefile
```bash
make setup  # Instala tudo automaticamente
```

### Método 3: Manual
```bash
# Instalar dependências principais
pip install -r requirements.txt

# Instalar dependências de desenvolvimento
pip install -e .[dev]
```

## 🚀 Uso Rápido

### Comandos Makefile (Recomendado)
```bash
make help           # Ver todos os comandos disponíveis
make check          # Verificar código (linting)
make format         # Formatar código
make fix            # Corrigir problemas automaticamente
make test           # Executar testes
make all            # Pipeline completo (fix + format + check + test)
```

### Comandos Diretos

#### Ruff (Principal)
```bash
# Verificar código
ruff check src/ tests/ scripts/

# Formatar código
ruff format src/ tests/ scripts/

# Corrigir problemas automaticamente
ruff check --fix src/ tests/ scripts/

# Organizar imports
ruff check --select I --fix src/ tests/ scripts/
```

#### Black + isort (Alternativo)
```bash
# Formatar com Black
black src/ tests/ scripts/

# Organizar imports com isort
isort src/ tests/ scripts/
```

#### Testes
```bash
# Executar todos os testes
pytest

# Testes com cobertura
pytest --cov=src

# Testes específicos
pytest tests/test_main.py

# Testes rápidos (sem cobertura)
pytest --no-cov
```

## ⚙️ Configuração

### pyproject.toml
Todas as configurações estão centralizadas no arquivo `pyproject.toml`:

```toml
[tool.ruff]
line-length = 88
target-version = "py39"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "N", "D", "UP", "B", ...]

[tool.black]
line-length = 88
target-version = ['py39', 'py310', 'py311', 'py312']

[tool.isort]
profile = "black"
known_first_party = ["src"]
```

### Configurações Personalizadas

#### Ruff (Principais regras ativadas)
- **E, W** - Erros e avisos do pycodestyle (PEP 8)
- **F** - Erros do Pyflakes  
- **I** - Organização de imports (isort)
- **N** - Convenções de nomenclatura
- **D** - Estilo de docstrings (Google style)
- **UP** - Modernização do código (pyupgrade)
- **B** - Bug patterns (flake8-bugbear)
- **S** - Verificações de segurança (bandit)
- **C4** - List/dict comprehensions
- **SIM** - Simplificações de código
- **PL** - Pylint checks

#### Regras Ignoradas
- **E501** - Linha muito longa (gerenciado pelo formatter)
- **D100-D107** - Docstrings obrigatórios (flexibilidade durante desenvolvimento)
- **S101** - Uso de assert (comum em testes)

## 🎯 Integração com Editores

### VS Code
Instale as extensões:
- **Ruff** (charliermarsh.ruff)
- **Black Formatter** (ms-python.black-formatter)
- **isort** (ms-python.isort)

Configuração no `settings.json`:
```json
{
  "[python]": {
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll.ruff": "explicit",
      "source.organizeImports.ruff": "explicit"
    }
  },
  "ruff.enable": true,
  "ruff.organizeImports": true
}
```

### PyCharm/IntelliJ
1. Instale o plugin Ruff
2. Configure External Tools para Black e isort
3. Ative "Format on Save"

## 📊 Pipeline de CI/CD

### GitHub Actions (Exemplo)
```yaml
name: Code Quality
on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          pip install -e .[dev]
      
      - name: Run linting
        run: |
          ruff check src/ tests/
      
      - name: Check formatting
        run: |
          ruff format --check src/ tests/
      
      - name: Run tests
        run: |
          pytest --cov=src --cov-fail-under=65
```

### Comandos para CI
```bash
make ci-check    # Verifica sem alterar arquivos
make ci-test     # Testes para CI com XML coverage
```

## 📈 Relatórios e Métricas

### Cobertura de Código
```bash
# Gerar relatório HTML
make coverage

# Ver relatório no navegador
open htmlcov/index.html
```

### Análise de Qualidade
```bash
# Estatísticas de regras violadas
ruff check --statistics src/

# Mostrar todas as configurações
ruff check --show-settings src/

# Mostrar arquivos que serão analisados
ruff check --show-files src/
```

## 🔄 Workflow de Desenvolvimento

### 1. Antes de Commitar
```bash
make all  # Fix + Format + Check + Test
```

### 2. Durante Desenvolvimento
```bash
make fix     # Correções rápidas
make format  # Formatação
make check   # Verificação
```

### 3. Antes de PR
```bash
make clean   # Limpar arquivos temporários
make all     # Pipeline completo
make coverage # Verificar cobertura
```

## 🐛 Solução de Problemas

### Ruff não encontrado
```bash
# Verificar instalação
which ruff
ruff --version

# Reinstalar se necessário
pip install --upgrade ruff
```

### Conflitos entre Black e Ruff
O Ruff está configurado para ser compatível com Black. Se houver conflitos:
```bash
# Use apenas Ruff (recomendado)
make format

# Ou force compatibilidade
ruff format --config "quote-style = 'double'"
```

### Muitos erros de linting
```bash
# Corrigir automaticamente o que for possível
make fix

# Desabilitar regras específicas temporariamente
ruff check --ignore E501,D100 src/
```

### Performance
```bash
# Verificar cache
ls -la .ruff_cache/

# Limpar cache se necessário
make clean
```

## 📚 Recursos Adicionais

### Documentação Oficial
- [Ruff](https://docs.astral.sh/ruff/)
- [Black](https://black.readthedocs.io/)
- [isort](https://pycqa.github.io/isort/)
- [pytest](https://docs.pytest.org/)

### Configurações Avançadas
- [Ruff Rules](https://docs.astral.sh/ruff/rules/)
- [Black Configuration](https://black.readthedocs.io/en/stable/usage_and_configuration/the_basics.html)
- [isort Settings](https://pycqa.github.io/isort/docs/configuration/config_files.html)

## 💡 Dicas e Melhores Práticas

### 1. Pre-commit Hooks
```bash
# Instalar pre-commit
pip install pre-commit

# Configurar hooks
pre-commit install

# Executar manualmente
pre-commit run --all-files
```

### 2. Configurações por Arquivo
Use comentários `# noqa` ou `# ruff: noqa` para ignorar regras específicas:
```python
import os  # noqa: F401
password = "secret"  # ruff: noqa: S105
```

### 3. Performance
- Ruff é ~100x mais rápido que Flake8
- Use `make fix` frequentemente para manter código limpo
- Configure seu editor para formatar ao salvar

### 4. Customização
Ajuste as regras no `pyproject.toml` conforme necessário do projeto:
```toml
[tool.ruff.lint]
# Adicionar mais regras
extend-select = ["ARG", "PTH"]

# Ignorar regras específicas  
extend-ignore = ["D213", "D203"]
```

---

**🎉 Com essas ferramentas configuradas, o Texta AI mantém código de alta qualidade automaticamente!** 