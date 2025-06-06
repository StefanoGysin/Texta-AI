# Script PowerShell de instalação das ferramentas de desenvolvimento para Texta AI
# Uso: .\scripts\install-dev-tools.ps1

# Configurar política de execução se necessário
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Cores para output
$Green = "Green"
$Yellow = "Yellow" 
$Red = "Red"

Write-Host "🚀 Instalando ferramentas de desenvolvimento para Texta AI" -ForegroundColor $Green
Write-Host ""

# Verificar se Python está instalado
$pythonCmd = $null
if (Get-Command python3 -ErrorAction SilentlyContinue) {
    $pythonCmd = "python3"
    $pipCmd = "pip3"
}
elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCmd = "python"
    $pipCmd = "pip"
}
else {
    Write-Host "❌ Python não encontrado. Instale o Python 3.9+ primeiro." -ForegroundColor $Red
    Write-Host "Download: https://www.python.org/downloads/" -ForegroundColor $Yellow
    exit 1
}

$pythonVersion = & $pythonCmd --version
Write-Host "🐍 Usando Python: $pythonVersion" -ForegroundColor $Yellow

# Verificar versão do Python
$versionOutput = & $pythonCmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
$version = [Version]$versionOutput
$minVersion = [Version]"3.9"

if ($version -lt $minVersion) {
    Write-Host "❌ Python $versionOutput detectado. Este projeto requer Python 3.9 ou superior." -ForegroundColor $Red
    exit 1
}

Write-Host "✅ Python $versionOutput OK" -ForegroundColor $Green

# Verificar se está em um ambiente virtual (recomendado)
if ($env:VIRTUAL_ENV) {
    Write-Host "✅ Ambiente virtual detectado: $env:VIRTUAL_ENV" -ForegroundColor $Green
}
else {
    Write-Host "⚠️  Aviso: Não está em um ambiente virtual. Recomenda-se usar um venv." -ForegroundColor $Yellow
    Write-Host "   Para criar um: python -m venv .venv && .venv\Scripts\Activate.ps1" -ForegroundColor $Yellow
    Write-Host ""
}

# Atualizar pip
Write-Host "📦 Atualizando pip..." -ForegroundColor $Yellow
try {
    & $pipCmd install --upgrade pip
    Write-Host "✅ pip atualizado" -ForegroundColor $Green
}
catch {
    Write-Host "❌ Erro ao atualizar pip: $_" -ForegroundColor $Red
    exit 1
}

# Instalar dependências principais
Write-Host "📦 Instalando dependências principais..." -ForegroundColor $Yellow
try {
    & $pipCmd install -r requirements.txt
    Write-Host "✅ Dependências principais instaladas" -ForegroundColor $Green
}
catch {
    Write-Host "❌ Erro ao instalar dependências principais: $_" -ForegroundColor $Red
    exit 1
}

# Instalar dependências de desenvolvimento via pyproject.toml
Write-Host "🛠️  Instalando dependências de desenvolvimento..." -ForegroundColor $Yellow
try {
    & $pipCmd install -e ".[dev]"
    Write-Host "✅ Dependências de desenvolvimento instaladas" -ForegroundColor $Green
}
catch {
    Write-Host "❌ Erro ao instalar dependências de desenvolvimento: $_" -ForegroundColor $Red
    exit 1
}

# Verificar instalação das ferramentas
Write-Host ""
Write-Host "🔍 Verificando instalação das ferramentas..." -ForegroundColor $Yellow

# Verificar Ruff
try {
    $ruffVersion = & ruff --version
    Write-Host "✅ Ruff: $ruffVersion" -ForegroundColor $Green
}
catch {
    Write-Host "❌ Ruff não instalado corretamente" -ForegroundColor $Red
    exit 1
}

# Verificar Black
try {
    $blackVersion = & black --version
    Write-Host "✅ Black: $($blackVersion -split '\n')[0]" -ForegroundColor $Green
}
catch {
    Write-Host "❌ Black não instalado corretamente" -ForegroundColor $Red
    exit 1
}

# Verificar isort
try {
    $isortVersion = & isort --version
    Write-Host "✅ isort: $($isortVersion -split '\n')[0]" -ForegroundColor $Green
}
catch {
    Write-Host "❌ isort não instalado corretamente" -ForegroundColor $Red
    exit 1
}

# Verificar pytest
try {
    $pytestVersion = & pytest --version
    Write-Host "✅ pytest: $($pytestVersion -split '\n')[0]" -ForegroundColor $Green
}
catch {
    Write-Host "❌ pytest não instalado corretamente" -ForegroundColor $Red
    exit 1
}

Write-Host ""
Write-Host "🎉 Instalação concluída com sucesso!" -ForegroundColor $Green
Write-Host ""
Write-Host "📋 Próximos passos:" -ForegroundColor $Yellow
Write-Host "  1. Execute " -NoNewline; Write-Host "python scripts/dev-tools.py check" -ForegroundColor $Green -NoNewline; Write-Host " para verificar o código"
Write-Host "  2. Execute " -NoNewline; Write-Host "python scripts/dev-tools.py format" -ForegroundColor $Green -NoNewline; Write-Host " para formatar o código"
Write-Host "  3. Execute " -NoNewline; Write-Host "pytest" -ForegroundColor $Green -NoNewline; Write-Host " para rodar os testes"
Write-Host ""
Write-Host "💡 Comandos úteis:" -ForegroundColor $Yellow
Write-Host "  • " -NoNewline; Write-Host "python scripts/dev-tools.py all" -ForegroundColor $Green -NoNewline; Write-Host "  - Pipeline completo (fix + format + check + test)"
Write-Host "  • " -NoNewline; Write-Host "python scripts/dev-tools.py fix" -ForegroundColor $Green -NoNewline; Write-Host "   - Correções automáticas"
Write-Host "  • " -NoNewline; Write-Host "ruff check src/" -ForegroundColor $Green -NoNewline; Write-Host "             - Verificação direta"
Write-Host ""
Write-Host "✨ Desenvolvimento com qualidade configurado!" -ForegroundColor $Green 