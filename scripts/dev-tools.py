#!/usr/bin/env python3
"""Script de desenvolvimento para executar ferramentas de qualidade de código.

Uso: python scripts/dev-tools.py [comando]

Comandos disponíveis:
- check: Executa linting com ruff
- format: Formata código com ruff (ou opcionalmente black + isort)
- format-black: Formata código com black + isort (separadamente)
- fix: Executa ruff com --fix para correções automáticas
- all: Executa check + format
- install: Instala dependências de desenvolvimento
"""

from pathlib import Path
import subprocess
import sys

# Constantes
MINIMUM_ARGS = 2
ALLOWED_COMMANDS = ['ruff', 'black', 'isort', 'pip']


def run_command(command: list[str], description: str) -> bool:
    """Executa um comando e retorna True se bem-sucedido."""
    print(f"\n🔄 {description}")
    print(f"Executando: {' '.join(command)}")

    # Validação de segurança: verificar se o comando é permitido
    if command[0] not in ALLOWED_COMMANDS:
        print(f"❌ {description} - Comando não permitido: {command[0]}")
        return False

    try:
        subprocess.run(command, check=True, cwd=Path(__file__).parent.parent)  # noqa: S603
        print(f"✅ {description} - Sucesso!")
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - Falhou com código {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"❌ {description} - Comando não encontrado: {command[0]}")
        print("Certifique-se de que as dependências estão instaladas.")
        return False
    else:
        return True


def ruff_check() -> bool:
    """Executa verificação de linting com ruff."""
    return run_command(
        ["ruff", "check", "src/", "tests/", "scripts/"],
        "Verificação de linting com Ruff",
    )


def ruff_format() -> bool:
    """Formata código com ruff."""
    return run_command(
        ["ruff", "format", "src/", "tests/", "scripts/"],
        "Formatação de código com Ruff",
    )


def ruff_fix() -> bool:
    """Executa ruff com --fix para correções automáticas."""
    return run_command(
        ["ruff", "check", "--fix", "src/", "tests/", "scripts/"],
        "Correção automática com Ruff",
    )


def black_format() -> bool:
    """Formata código com black."""
    return run_command(
        ["black", "src/", "tests/", "scripts/"], "Formatação de código com Black"
    )


def isort_imports() -> bool:
    """Organiza imports com isort."""
    return run_command(
        ["isort", "src/", "tests/", "scripts/"], "Organização de imports com isort"
    )


def install_dev_deps() -> bool:
    """Instala dependências de desenvolvimento."""
    return run_command(
        ["pip", "install", "-e", ".[dev]"],
        "Instalação de dependências de desenvolvimento",
    )


def main() -> None:
    """Função principal."""
    if len(sys.argv) < MINIMUM_ARGS:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1].lower()
    success = True

    print(f"🚀 Executando comando: {command}")

    if command == "check":
        success = ruff_check()

    elif command == "format":
        print("Usando Ruff para formatação (recomendado)")
        success = ruff_format()

    elif command == "format-black":
        print("Usando Black + isort para formatação")
        success = isort_imports() and black_format()

    elif command == "fix":
        success = ruff_fix()

    elif command == "all":
        print("Executando verificação completa...")
        success = ruff_fix() and ruff_format() and ruff_check()

    elif command == "install":
        success = install_dev_deps()

    else:
        print(f"❌ Comando desconhecido: {command}")
        print(__doc__)
        sys.exit(1)

    if success:
        print(f"\n🎉 Comando '{command}' executado com sucesso!")
        sys.exit(0)
    else:
        print(f"\n💥 Comando '{command}' falhou!")
        sys.exit(1)


if __name__ == "__main__":
    main()
