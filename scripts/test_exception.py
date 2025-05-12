from src.logger_config import logger

def processa_usuario(usuario):
    """Processa informações do usuário e calcula a média de idade do grupo."""
    # Valida a estrutura do dicionário
    if not isinstance(usuario, dict):
        raise TypeError("Usuário deve ser um dicionário")
    
    # Acessa dados aninhados que podem causar erros
    idade = usuario['dados']['perfil']['idade']
    grupo = usuario['dados']['grupo']
    
    # Tenta calcular a média de idade do grupo
    total_idades = sum(membro['idade'] for membro in grupo)
    media_idade = total_idades / len(grupo)
    
    return {
        'nome': usuario['nome'],
        'idade': idade,
        'media_idade_grupo': media_idade,
        'status': 'processado'
    }

# Exemplo de usuário com problemas para demonstrar diagnóstico
usuario = {
    'nome': 'João Silva',
    'dados': {
        'perfil': {
            'idade': 35,
            'cidade': 'São Paulo'
        },
        'grupo': [
            {'nome': 'Maria', 'idade': 28},
            {'nome': 'Pedro', 'idade': 32},
            {'nome': 'Ana', 'idade': None}  # Causará erro na soma
        ]
    }
}

try:
    # Tentar processar o usuário
    resultado = processa_usuario(usuario)
    print(f"Processamento completo: {resultado}")
except Exception as e:
    # Logger registrará o traceback completo com valores das variáveis
    logger.exception(f"Erro ao processar usuário: {usuario['nome']}")
    print("Ocorreu um erro ao processar o usuário. Verifique o arquivo de log para detalhes completos.") 