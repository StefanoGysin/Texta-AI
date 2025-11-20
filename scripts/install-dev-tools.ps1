# Script PowerShell de instalação das ferramentas de desenvolvimento para Texta AI
# Uso: .\scripts\install-dev-tools.ps1 (execute no diretório raiz do projeto)

# Cores para output
$Green = "Green"
$Yellow = "Yellow" 
$Red = "Red"
$Blue = "Blue"

Write-Host "🚀 Instalando ferramentas de desenvolvimento para Texta AI" -ForegroundColor $Green
Write-Host ""

function Check-Command {
    param (
        [string]$CommandName
    )
    (Get-Command $CommandName -ErrorAction SilentlyContinue) -ne $null
}

# --- 1. Verificar e instalar Poetry ---
Write-Host "🔍 Verificando instalação do Poetry..." -ForegroundColor $Yellow
if (-not (Check-Command "poetry")) {
    Write-Host "❌ Poetry não encontrado." -ForegroundColor $Red
    Write-Host "   Instalando Poetry..." -ForegroundColor $Yellow
    try {
        Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing | python -
        # Adicionar Poetry ao PATH para a sessão atual, se necessário
        $env:Path += ";$($env:APPDATA)\pypoetry\venv\Scripts"
        Write-Host "✅ Poetry instalado. Pode ser necessário reiniciar o terminal." -ForegroundColor $Green
    }
    catch {
        Write-Host "❌ Erro ao instalar Poetry: $_" -ForegroundColor $Red
        Write-Host "   Por favor, instale manualmente: https://python-poetry.org/docs/#installation" -ForegroundColor $Yellow
        exit 1
    }
}
Write-Host "✅ Poetry encontrado." -ForegroundColor $Green

# --- 2. Configurar Poetry para criar ambiente virtual no projeto ---
Write-Host "⚙️  Configurando Poetry para criar ambiente virtual no projeto..." -ForegroundColor $Yellow
try {
    poetry config virtualenvs.in-project true
    Write-Host "✅ Configuração 'virtualenvs.in-project' definida para 'true'." -ForegroundColor $Green
}
catch {
    Write-Host "❌ Erro ao configurar Poetry: $_" -ForegroundColor $Red
    exit 1
}

# --- 3. Verificar pyproject.toml ---
Write-Host "🔍 Verificando 'pyproject.toml'..." -ForegroundColor $Yellow
if (-not (Test-Path "pyproject.toml")) {
    Write-Host "❌ Arquivo 'pyproject.toml' não encontrado no diretório atual." -ForegroundColor $Red
    Write-Host "   Certifique-se de executar este script no diretório raiz do projeto." -ForegroundColor $Yellow
    exit 1
}
Write-Host "✅ 'pyproject.toml' encontrado." -ForegroundColor $Green

# --- 4. Instalar dependências ---
Write-Host "📦 Instalando dependências principais e de desenvolvimento com Poetry..." -ForegroundColor $Yellow
try {
    poetry install --with dev
    Write-Host "✅ Dependências instaladas com sucesso." -ForegroundColor $Green
}
catch {
    Write-Host "❌ Erro ao instalar dependências com Poetry: $_" -ForegroundColor $Red
    Write-Host "   Verifique o 'pyproject.toml' e a saída do erro acima." -ForegroundColor $Yellow
    exit 1
}

# --- 5. Verificar versão do Python (via Poetry) ---
Write-Host "🐍 Verificando versão do Python no ambiente Poetry..." -ForegroundColor $Yellow
try {
    $pythonVersion = (poetry run python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")
    $minVersion = [Version]"3.9"
    $currentVersion = [Version]$pythonVersion

    if ($currentVersion -lt $minVersion) {
        Write-Host "❌ Python $pythonVersion detectado no ambiente Poetry. Este projeto requer Python 3.9 ou superior." -ForegroundColor $Red
        Write-Host "   Considere usar 'poetry env use pythonX.Y' para selecionar uma versão compatível." -ForegroundColor $Yellow
        exit 1
    }
    Write-Host "✅ Python $pythonVersion OK no ambiente Poetry." -ForegroundColor $Green
}
catch {
    Write-Host "❌ Erro ao verificar a versão do Python no ambiente Poetry: $_" -ForegroundColor $Red
    exit 1
}

# --- 6. Verificar instalação das ferramentas de desenvolvimento ---
Write-Host ""
Write-Host "🔍 Verificando instalação das ferramentas de desenvolvimento..." -ForegroundColor $Yellow

$tools = @{
    "Ruff" = "ruff --version"
    "pytest" = "pytest --version"
}

foreach ($tool in $tools.GetEnumerator()) {
    try {
        $output = (poetry run $($tool.Value) | Select-String -Pattern "version" -CaseSensitive -SimpleMatch | Select-Object -First 1).ToString().Trim()
        Write-Host "✅ $($tool.Name): $($output)" -ForegroundColor $Green
    }
    catch {
        Write-Host "❌ $($tool.Name) não instalado ou não funcionando corretamente: $_" -ForegroundColor $Red
        exit 1
    }
}

Write-Host ""
Write-Host "🎉 Instalação e configuração concluídas com sucesso!" -ForegroundColor $Green
Write-Host ""
Write-Host "📋 Próximos passos:" -ForegroundColor $Yellow
Write-Host "  1. Ative o ambiente virtual com " -NoNewline; Write-Host "poetry shell" -ForegroundColor $Blue
Write-Host "  2. Para executar comandos, use " -NoNewline; Write-Host "poetry run [comando]" -ForegroundColor $Blue
Write-Host ""
Write-Host "💡 Comandos úteis:" -ForegroundColor $Yellow
Write-Host "  • " -NoNewline; Write-Host "poetry run ruff check --fix ." -ForegroundColor $Green -NoNewline; Write-Host "   - Verifica e corrige problemas de linting e formatação"
Write-Host "  • " -NoNewline; Write-Host "poetry run ruff format ." -ForegroundColor $Green -NoNewline; Write-Host "      - Formata o código"
Write-Host "  • " -NoNewline; Write-Host "poetry run pytest" -ForegroundColor $Green -NoNewline; Write-Host "                - Executa a suíte de testes"
Write-Host "  • " -NoNewline; Write-Host "poetry run python src/main.py" -ForegroundColor $Green -NoNewline; Write-Host "      - Inicia a aplicação"
Write-Host ""
Write-Host "✨ Desenvolvimento com qualidade configurado!" -ForegroundColor $Green