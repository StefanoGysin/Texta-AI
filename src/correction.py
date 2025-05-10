import os
import asyncio
# Importar o logger pré-configurado
from .logger_config import logger
import time
from dotenv import load_dotenv
from agents import Agent, Runner, ModelSettings

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# Recupera a chave da API da OpenAI das variáveis de ambiente
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Configura a chave da API no ambiente para que o SDK de agentes possa acessá-la
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY or ""

# --- Definição do Agente de Correção ---

# Prompt de correção para o agente (carregado do .env ou usa o padrão)
DEFAULT_CORRECTION_PROMPT = (
    "Você é um assistente especialista em correção de texto em português brasileiro. "
    "Sua tarefa é corrigir a gramática, ortografia e pontuação do texto fornecido. "
    "Mantenha o significado original e o tom/estilo do texto o máximo possível. "
    "Responda APENAS com o texto corrigido, sem adicionar introduções, saudações, despedidas, explicações ou comentários adicionais. "
    "Se o texto de entrada já estiver correto, retorne o texto original sem modificações. "
    "Texto a ser corrigido:"
)

# Carrega o prompt do ambiente ou usa o padrão
CORRECTION_PROMPT = os.getenv("CORRECTION_PROMPT", DEFAULT_CORRECTION_PROMPT)

# Cria o agente de correção uma única vez
logger.info("Inicializando Agente de Correção...")
CORRECTION_AGENT = Agent(
    name="Correction Agent",
    instructions=CORRECTION_PROMPT,
    model="gpt-4o-mini",  # Modelo o4-mini conforme documentação
    model_settings=ModelSettings(temperature=0.3),  # Temperatura mais baixa para correções precisas
)
logger.info(f"Agente '{CORRECTION_AGENT.name}' inicializado com modelo '{CORRECTION_AGENT.model}'.")

# --- Classes de erro personalizadas ---

class OpenAIError(Exception):
    """Classe base para erros relacionados à API OpenAI."""
    pass

class ConnectionError(OpenAIError):
    """Erro de conexão com a API OpenAI."""
    pass

class TimeoutError(OpenAIError):
    """Timeout ao comunicar com a API OpenAI."""
    pass

class AuthenticationError(OpenAIError):
    """Erro de autenticação com a API OpenAI."""
    pass

class RateLimitError(OpenAIError):
    """Erro de limite de requisições (rate limit) na API OpenAI."""
    pass

class ServiceUnavailableError(OpenAIError):
    """Erro quando o serviço OpenAI está indisponível."""
    pass

# --- Função para Obter Texto Corrigido ---

# Número máximo de tentativas para lidar com erros transitórios
MAX_RETRIES = 3
# Tempo de espera entre tentativas (em segundos)
RETRY_DELAY = 2

async def _run_correction_async(text_to_correct: str) -> str | None:
    """Função auxiliar assíncrona para rodar o agente com tratamento de erros específicos."""
    logger.info(f"Enviando texto para correção: '{text_to_correct[:70]}...'")
    
    retries = 0
    last_error = None
    
    while retries < MAX_RETRIES:
        try:
            # O Runner.run é assíncrono
            result = await Runner.run(CORRECTION_AGENT, text_to_correct)
            corrected = result.final_output
            logger.info(f"Texto corrigido recebido: '{corrected[:70]}...'")
            # Retorna apenas o output final como string
            return corrected
        except asyncio.TimeoutError as e:
            last_error = e
            logger.warning(f"Timeout ao comunicar com a API OpenAI (tentativa {retries+1}/{MAX_RETRIES})")
            retries += 1
            if retries < MAX_RETRIES:
                time.sleep(RETRY_DELAY * retries)  # Backoff exponencial
        except Exception as e:
            error_message = str(e).lower()
            
            # Análise do erro para classificação
            if "rate limit" in error_message or "too many requests" in error_message or "429" in error_message:
                logger.warning(f"Erro de limite de requisições na API OpenAI: {e}")
                last_error = RateLimitError(f"Limite de requisições excedido: {e}")
                # Para erros de rate limit, espera mais tempo entre tentativas
                retries += 1
                if retries < MAX_RETRIES:
                    time.sleep(RETRY_DELAY * 2 * retries)  # Backoff mais agressivo
                    continue
                
            elif "authentication" in error_message or "unauthorized" in error_message or "auth" in error_message or "401" in error_message:
                logger.error(f"Erro de autenticação com a API OpenAI: {e}")
                return None  # Não tenta novamente em caso de erro de autenticação
                
            elif "connection" in error_message or "network" in error_message or "timeout" in error_message:
                logger.warning(f"Erro de conexão com a API OpenAI (tentativa {retries+1}/{MAX_RETRIES}): {e}")
                last_error = ConnectionError(f"Problema de conexão: {e}")
                retries += 1
                if retries < MAX_RETRIES:
                    time.sleep(RETRY_DELAY * retries)
                    continue
                    
            elif "service unavailable" in error_message or "server error" in error_message or "502" in error_message or "503" in error_message:
                logger.warning(f"Serviço OpenAI indisponível (tentativa {retries+1}/{MAX_RETRIES}): {e}")
                last_error = ServiceUnavailableError(f"Serviço indisponível: {e}")
                retries += 1
                if retries < MAX_RETRIES:
                    time.sleep(RETRY_DELAY * retries)
                    continue
                    
            else:
                # Erro genérico, não tentamos novamente
                logger.error(f"Erro desconhecido ao executar o agente de correção: {e}")
                return None
    
    # Se chegamos aqui, esgotamos as tentativas
    if last_error:
        logger.error(f"Falha após {MAX_RETRIES} tentativas. Último erro: {last_error}")
    return None

def get_corrected_text(text_to_correct: str, api_key=None) -> str | None:
    """Recebe um texto, executa o agente de correção e retorna o texto corrigido.

    Args:
        text_to_correct (str): O texto que precisa ser corrigido.
        api_key (str, optional): Parâmetro mantido para compatibilidade mas não é mais utilizado.
                                O SDK usa a variável de ambiente OPENAI_API_KEY.

    Returns:
        str | None: O texto corrigido pela LLM, ou None se ocorrer um erro.
    """
    if not text_to_correct:
        logger.warning("Texto de entrada vazio.")
        return None
    
    # Verifica se a API key está disponível no ambiente
    current_api_key = os.environ.get("OPENAI_API_KEY")
    key_source = "Variável de Ambiente"
    
    if not current_api_key and not api_key:
        logger.error("Nenhuma API key configurada (variável de ambiente ou parâmetro).")
        return None
    
    # Se uma nova API key foi fornecida via parâmetro, atualiza temporariamente a variável de ambiente
    original_api_key = current_api_key
    if api_key and api_key != current_api_key:
        logger.debug("Usando API key fornecida temporariamente via parâmetro.")
        os.environ["OPENAI_API_KEY"] = api_key
        key_source = "Parâmetro Temporário"
    else:
        logger.debug(f"Usando API key da {key_source}.")

    
    try:
        logger.info("Iniciando execução do agente...")
        # Executa a função assíncrona do Runner de forma síncrona
        corrected_text = asyncio.run(_run_correction_async(text_to_correct))
        if corrected_text:
            logger.info("Execução do agente concluída com sucesso.")
            return corrected_text
        else:
            logger.error("A correção falhou após várias tentativas ou devido a erro crítico.")
            return None
    except Exception as e:
        logger.error(f"Erro não tratado durante a correção: {e}")
        return None
    finally:
        # Restaura a API key original se foi alterada
        if api_key and api_key != original_api_key:
            logger.debug("Restaurando API key original da variável de ambiente.")
            if original_api_key:
                 os.environ["OPENAI_API_KEY"] = original_api_key
            else:
                 # Se não havia chave original, remove a temporária
                 del os.environ["OPENAI_API_KEY"]

# --- Bloco de Teste Local (opcional) ---
# if __name__ == '__main__':
#     test_text = "este testo contem alguns errros de escrita e pontuacão,"
#     logger.info(f"Texto Original: {test_text}")
#     corrected = get_corrected_text(test_text)
#     if corrected:
#         logger.info(f"Texto Corrigido: {corrected}")
#     else:
#         logger.error("Falha ao corrigir o texto.") 