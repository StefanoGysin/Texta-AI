from __future__ import annotations

import asyncio
import os
import time

from agents import Agent, ModelSettings, Runner
from dotenv import load_dotenv

# Importar o logger pré-configurado
from .logger_config import logger

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
    model_settings=ModelSettings(
        temperature=0.3
    ),  # Temperatura mais baixa para correções precisas
)
logger.info(
    f"Agente '{CORRECTION_AGENT.name}' inicializado com modelo '{CORRECTION_AGENT.model}'."
)

# --- Classes de erro personalizadas ---


class OpenAIError(Exception):
    """Classe base para erros relacionados à API OpenAI."""


class OpenAIConnectionError(OpenAIError):
    """Erro de conexão com a API OpenAI."""


class OpenAITimeoutError(OpenAIError):
    """Timeout ao comunicar com a API OpenAI."""


class AuthenticationError(OpenAIError):
    """Erro de autenticação com a API OpenAI."""


class RateLimitError(OpenAIError):
    """Erro de limite de requisições (rate limit) na API OpenAI."""


class ServiceUnavailableError(OpenAIError):
    """Erro quando o serviço OpenAI está indisponível."""


# --- Função para Obter Texto Corrigido ---

# Número máximo de tentativas para lidar com erros transitórios
MAX_RETRIES = 3
# Tempo de espera entre tentativas (em segundos)
RETRY_DELAY = 2


def _should_retry_error(error_message: str) -> bool:
    """Check if an error should trigger a retry."""
    return any(
        keyword in error_message
        for keyword in [
            "rate limit",
            "too many requests",
            "429",
            "connection",
            "network",
            "timeout",
            "service unavailable",
            "server error",
            "502",
            "503",
        ]
    )


def _is_authentication_error(error_message: str) -> bool:
    """Check if an error is authentication-related (no retry)."""
    return any(
        keyword in error_message
        for keyword in ["authentication", "unauthorized", "auth", "401"]
    )


def _get_retry_delay(attempt: int, error_message: str) -> float:
    """Get retry delay based on attempt and error type."""
    if (
        "rate limit" in error_message
        or "too many requests" in error_message
        or "429" in error_message
    ):
        return RETRY_DELAY * 2 * (attempt + 1)  # Backoff mais agressivo para rate limit
    return RETRY_DELAY * (attempt + 1)


async def _try_single_correction(text_to_correct: str) -> str:
    """Attempt a single correction API call."""
    result = await Runner.run(CORRECTION_AGENT, text_to_correct)
    return result.final_output


async def _run_correction_async(text_to_correct: str) -> str | None:
    """Função auxiliar assíncrona para rodar o agente com tratamento de erros específicos."""
    logger.info(f"Enviando texto para correção: '{text_to_correct[:70]}...'")

    for attempt in range(MAX_RETRIES):
        # Suppress PERF203 as retry logic requires exception handling within loop
        try:
            corrected = await _try_single_correction(text_to_correct)
            logger.info(f"Texto corrigido recebido: '{corrected[:70]}...'")
        except asyncio.TimeoutError as e:  # noqa: PERF203
            logger.warning(
                f"Timeout ao comunicar com a API OpenAI (tentativa {attempt + 1}/{MAX_RETRIES})"
            )
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))  # Backoff exponencial
                continue
            logger.error(f"Falha após {MAX_RETRIES} tentativas. Último erro: {e}")
            return None
        except (OSError, RuntimeError) as e:
            error_message = str(e).lower()

            if _is_authentication_error(error_message):
                logger.error(f"Erro de autenticação com a API OpenAI: {e}")
                return None  # Não tenta novamente em caso de erro de autenticação

            if not _should_retry_error(error_message):
                logger.error(f"Erro desconhecido ao executar o agente de correção: {e}")
                return None

            # Log baseado no tipo de erro
            if (
                "rate limit" in error_message
                or "too many requests" in error_message
                or "429" in error_message
            ):
                logger.warning(f"Erro de limite de requisições na API OpenAI: {e}")
            elif (
                "connection" in error_message
                or "network" in error_message
                or "timeout" in error_message
            ):
                logger.warning(
                    f"Erro de conexão com a API OpenAI (tentativa {attempt + 1}/{MAX_RETRIES}): {e}"
                )
            elif (
                "service unavailable" in error_message
                or "server error" in error_message
                or "502" in error_message
                or "503" in error_message
            ):
                logger.warning(
                    f"Serviço OpenAI indisponível (tentativa {attempt + 1}/{MAX_RETRIES}): {e}"
                )

            if attempt < MAX_RETRIES - 1:
                delay = _get_retry_delay(attempt, error_message)
                time.sleep(delay)
                continue

            logger.error(f"Falha após {MAX_RETRIES} tentativas. Último erro: {e}")
            return None
        else:
            return corrected

    return None


async def get_corrected_text(text_to_correct: str, api_key: str | None = None) -> str | None:
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

    corrected_text = None
    try:
        logger.info("Iniciando execução do agente...")
        # Executa a função assíncrona do Runner
        corrected_text = await _run_correction_async(text_to_correct)
        if corrected_text:
            logger.info("Execução do agente concluída com sucesso.")
        else:
            logger.error(
                "A correção falhou após várias tentativas ou devido a erro crítico."
            )
    finally:
        # Restaura a API key original se foi alterada
        if api_key and api_key != original_api_key:
            logger.debug("Restaurando API key original da variável de ambiente.")
            if original_api_key:
                os.environ["OPENAI_API_KEY"] = original_api_key
            else:
                # Se não havia chave original, remove a temporária de forma segura
                os.environ.pop("OPENAI_API_KEY", None)

    return corrected_text
