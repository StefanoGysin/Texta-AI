"""Script de teste para demonstrar o sistema de exceções com logging detalhado."""

from typing import Any

from src.logger_config import logger

# Constantes para mensagens de erro
ERR_USUARIO_NAO_DICT = "Usuário deve ser um dicionário"


def processa_usuario(usuario: dict[str, Any]) -> tuple[str, float]:
    """Processa informações do usuário e calcula a média de idade do grupo."""
    # Valida a estrutura do dicionário
    if not isinstance(usuario, dict):
        raise TypeError(ERR_USUARIO_NAO_DICT)

    # Acessa dados aninhados que podem causar erros
    grupo = usuario["dados"]["grupo"]

    # Tenta calcular a média de idade do grupo
    total_idades = sum(membro["idade"] for membro in grupo)
    media_idade = total_idades / len(grupo)

    return (
        usuario["nome"],
        media_idade,
    )


# Exemplo de usuário com problemas para demonstrar diagnóstico
usuario = {
    "nome": "João Silva",
    "dados": {
        "perfil": {"idade": 35, "cidade": "São Paulo"},
        "grupo": [
            {"nome": "Maria", "idade": 28},
            {"nome": "Pedro", "idade": 32},
            {"nome": "Ana", "idade": None},  # Causará erro na soma
        ],
    },
}

try:
    # Tentar processar o usuário
    resultado = processa_usuario(usuario)
    print(f"Processamento completo: {resultado}")
except (TypeError, KeyError, ValueError, ZeroDivisionError):
    # Logger registrará o traceback completo com valores das variáveis
    nome_usuario = usuario.get("nome", "desconhecido") if isinstance(usuario, dict) else "desconhecido"
    logger.exception(f"Erro ao processar usuário: {nome_usuario}")
    print(
        "Ocorreu um erro ao processar o usuário. Verifique o arquivo de log para detalhes completos."
    )
