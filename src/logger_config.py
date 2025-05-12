"""
Configuração centralizada do Loguru para garantir consistência em todos os módulos.
Este módulo deve ser importado antes de qualquer outra chamada ao logger.
"""
import sys
import os
from loguru import logger

# Remover o logger padrão
logger.remove()

# Configurar o formato personalizado com cores para o terminal
# A tag <level> já aplica cores padrão (verde para INFO, amarelo para WARNING, vermelho para ERROR)
# Podemos adicionar cores específicas para outras partes se desejado.
# Ex: <green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>
# Por agora, vamos manter simples e colorir o nível e o módulo.
logger.add(sys.stderr, format="[<level>{level: <8}</level>] <cyan>{module}</cyan>: <level>{message}</level>", colorize=True)

# Garantir que a pasta logs existe
os.makedirs('logs', exist_ok=True)

# Configurar log para arquivo (sem cores, pois não são úteis em arquivos de log)
# Habilitamos backtrace=True e diagnose=True para diagnóstico aprimorado em erros
# backtrace=True: Garante que o traceback completo da exceção seja logado
# diagnose=True: Mostra os valores das variáveis no traceback, útil para entender o estado da aplicação no momento do erro
logger.add("logs/texta-ai.log", 
           format="[{level: <8}] {module}: {message}", 
           rotation="10 MB", 
           backtrace=True, 
           diagnose=True)

# Exporta o logger configurado
__all__ = ["logger"] 