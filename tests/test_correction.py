import pytest
import os
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock, call
from src.correction import (
    get_corrected_text, 
    _run_correction_async, 
    CORRECTION_AGENT,
    ConnectionError as OpenAIConnectionError,
    TimeoutError as OpenAITimeoutError,
    AuthenticationError,
    RateLimitError,
    ServiceUnavailableError,
    MAX_RETRIES,
    RETRY_DELAY
)

# Testes para src/correction.py::get_corrected_text


class MockRunnerResult:
    """Mock para simular o retorno do Runner.run"""
    def __init__(self, final_output):
        self.final_output = final_output


@pytest.fixture
def mock_env_setup(monkeypatch):
    """Fixture para configurar ambiente de testes com uma API key válida"""
    monkeypatch.setenv("OPENAI_API_KEY", "mock-api-key-for-testing")


def test_get_corrected_text_success(mocker, mock_env_setup):
    """Testa o caso de sucesso onde o texto é corrigido pela API."""
    input_text = "Este é um texto com erros de gramática."
    expected_output = "Este é um texto com correções gramaticais."
    
    # Mock do asyncio.run para evitar execução real e retornar um valor definido
    mock_asyncio_run = mocker.patch('asyncio.run')
    mock_asyncio_run.return_value = expected_output
    
    # Testar a função
    result = get_corrected_text(input_text)
    
    # Verificações
    assert result == expected_output
    mock_asyncio_run.assert_called_once()
    

def test_get_corrected_text_empty_input(mocker, mock_env_setup):
    """Testa o comportamento quando a entrada é None ou string vazia."""
    # Mock para evitar execução real
    mock_asyncio_run = mocker.patch('asyncio.run')
    
    # Caso 1: entrada None
    result_none = get_corrected_text(None)
    assert result_none is None
    
    # Caso 2: string vazia
    result_empty = get_corrected_text("")
    assert result_empty is None
    
    # Verificar que nenhuma chamada à API foi feita
    mock_asyncio_run.assert_not_called()


def test_get_corrected_text_missing_api_key(mocker):
    """Testa o comportamento quando não há API key configurada."""
    input_text = "Este é um texto com erros de gramática."
    
    # Remover a API key do ambiente
    with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=True):
        # Mock para evitar execução real
        mock_asyncio_run = mocker.patch('asyncio.run')
        
        # Executar função sem API key
        result = get_corrected_text(input_text)
        
        # Verificar que retornou None e não tentou chamar a API
        assert result is None
        mock_asyncio_run.assert_not_called()


def test_get_corrected_text_api_failure(mocker, mock_env_setup):
    """Testa o comportamento quando a API falha."""
    input_text = "Este é um texto com erros de gramática."
    
    # Mock do asyncio.run para simular erro na API
    mock_asyncio_run = mocker.patch('asyncio.run')
    mock_asyncio_run.return_value = None  # Simulando falha que retorna None
    
    # Testar a função
    result = get_corrected_text(input_text)
    
    # Verificar que o resultado é None após falha da API
    assert result is None
    mock_asyncio_run.assert_called_once()


def test_get_corrected_text_with_api_key_param(mocker):
    """Testa usando uma API key via parâmetro em vez de variável de ambiente."""
    input_text = "Este é um texto com erros de gramática."
    api_key = "custom-api-key-via-parameter"
    expected_output = "Este é um texto corrigido."
    
    # Mock para simulação
    mock_asyncio_run = mocker.patch('asyncio.run')
    mock_asyncio_run.return_value = expected_output
    
    # Garantir que não há API key no ambiente
    with patch.dict(os.environ, {}, clear=True):
        # Executar função com API key como parâmetro
        result = get_corrected_text(input_text, api_key=api_key)
        
        # Verificar que a API key foi usada corretamente
        assert result == expected_output
        mock_asyncio_run.assert_called_once()
        
        # Verificar que a API key não permaneceu no ambiente após a execução
        assert "OPENAI_API_KEY" not in os.environ


@pytest.mark.asyncio
async def test_run_correction_async_success(mocker):
    """Testa a função assíncrona _run_correction_async diretamente."""
    input_text = "Este é um texto com erros de gramática."
    expected_output = "Este é um texto corrigido."
    
    # Mock do Runner.run com AsyncMock
    mock_result = MockRunnerResult(final_output=expected_output)
    mock_runner = mocker.patch('agents.Runner.run', new_callable=AsyncMock)
    mock_runner.return_value = mock_result
    
    # Executar função assíncrona
    result = await _run_correction_async(input_text)
    
    # Verificações
    assert result == expected_output
    mock_runner.assert_called_once_with(CORRECTION_AGENT, input_text)


@pytest.mark.asyncio
async def test_run_correction_async_exception(mocker):
    """Testa _run_correction_async quando ocorre uma exceção genérica."""
    input_text = "Este é um texto com erros de gramática."
    
    # Mock do Runner.run para lançar exceção
    mock_runner = mocker.patch('agents.Runner.run', new_callable=AsyncMock)
    mock_runner.side_effect = Exception("API error genérico")
    
    # Executar função assíncrona - deve capturar exceção e retornar None
    result = await _run_correction_async(input_text)
    
    # Verificações
    assert result is None
    mock_runner.assert_called_once()


@pytest.mark.asyncio
async def test_run_correction_async_timeout_with_retry(mocker):
    """Testa _run_correction_async com timeout da API e retentativas."""
    input_text = "Este é um texto com erros de gramática."
    expected_output = "Este é um texto corrigido."
    
    # Mock para time.sleep para que não haja espera real em testes
    mock_sleep = mocker.patch('time.sleep')
    
    # Mock do Runner.run para falhar nas primeiras tentativas e depois ter sucesso
    mock_runner = mocker.patch('agents.Runner.run', new_callable=AsyncMock)
    mock_runner.side_effect = [
        asyncio.TimeoutError("Timeout na API"),  # Primeira tentativa falha com timeout
        MockRunnerResult(final_output=expected_output)  # Segunda tentativa tem sucesso
    ]
    
    # Executar função assíncrona
    result = await _run_correction_async(input_text)
    
    # Verificações
    assert result == expected_output
    assert mock_runner.call_count == 2
    mock_sleep.assert_called_once_with(RETRY_DELAY * 1)  # Deve dormir após a primeira falha


@pytest.mark.asyncio
async def test_run_correction_async_connection_error_with_retry(mocker):
    """Testa _run_correction_async com erro de conexão e retentativas."""
    input_text = "Este é um texto com erros de gramática."
    
    # Mock para time.sleep para que não haja espera real em testes
    mock_sleep = mocker.patch('time.sleep')
    
    # Mock do Runner.run para simular erro de conexão em todas as tentativas
    mock_runner = mocker.patch('agents.Runner.run', new_callable=AsyncMock)
    mock_runner.side_effect = Exception("connection error occurred")
    
    # Executar função assíncrona
    result = await _run_correction_async(input_text)
    
    # Verificações
    assert result is None
    assert mock_runner.call_count == MAX_RETRIES
    # Verifica se sleep foi chamado MAX_RETRIES-1 vezes (não dorme após a última tentativa)
    assert mock_sleep.call_count == MAX_RETRIES - 1
    # Verifica a sequência de chamadas com backoff
    expected_calls = [call(RETRY_DELAY * i) for i in range(1, MAX_RETRIES)]
    mock_sleep.assert_has_calls(expected_calls)


@pytest.mark.asyncio
async def test_run_correction_async_rate_limit_with_retry(mocker):
    """Testa _run_correction_async com erro de rate limit e retentativas com backoff mais agressivo."""
    input_text = "Este é um texto com erros de gramática."
    
    # Mock para time.sleep para que não haja espera real em testes
    mock_sleep = mocker.patch('time.sleep')
    
    # Mock do Runner.run para simular erro de rate limit em todas as tentativas
    mock_runner = mocker.patch('agents.Runner.run', new_callable=AsyncMock)
    mock_runner.side_effect = Exception("rate limit exceeded 429")
    
    # Executar função assíncrona
    result = await _run_correction_async(input_text)
    
    # Verificações
    assert result is None
    assert mock_runner.call_count == MAX_RETRIES
    # Verifica se sleep foi chamado MAX_RETRIES-1 vezes (não dorme após a última tentativa)
    assert mock_sleep.call_count == MAX_RETRIES - 1
    # Verifica a sequência de chamadas com backoff mais agressivo para rate limit
    expected_calls = [call(RETRY_DELAY * 2 * i) for i in range(1, MAX_RETRIES)]
    mock_sleep.assert_has_calls(expected_calls)


@pytest.mark.asyncio
async def test_run_correction_async_auth_error_no_retry(mocker):
    """Testa _run_correction_async com erro de autenticação que não deve fazer retry."""
    input_text = "Este é um texto com erros de gramática."
    
    # Mock para time.sleep para garantir que não é chamado
    mock_sleep = mocker.patch('time.sleep')
    
    # Mock do Runner.run para simular erro de autenticação
    mock_runner = mocker.patch('agents.Runner.run', new_callable=AsyncMock)
    mock_runner.side_effect = Exception("authentication failed 401 unauthorized")
    
    # Executar função assíncrona
    result = await _run_correction_async(input_text)
    
    # Verificações
    assert result is None
    mock_runner.assert_called_once()  # Apenas uma tentativa, sem retry
    mock_sleep.assert_not_called()  # Não deve dormir


@pytest.mark.asyncio
async def test_run_correction_async_service_unavailable_with_retry(mocker):
    """Testa _run_correction_async com erro de indisponibilidade do serviço e retentativas."""
    input_text = "Este é um texto com erros de gramática."
    expected_output = "Este é um texto corrigido."
    
    # Mock para time.sleep para que não haja espera real em testes
    mock_sleep = mocker.patch('time.sleep')
    
    # Mock do Runner.run para simular indisponibilidade e depois sucesso
    mock_runner = mocker.patch('agents.Runner.run', new_callable=AsyncMock)
    mock_runner.side_effect = [
        Exception("service unavailable 503"),  # Primeira tentativa falha
        Exception("service unavailable 503"),  # Segunda tentativa falha
        MockRunnerResult(final_output=expected_output)  # Terceira tentativa tem sucesso
    ]
    
    # Executar função assíncrona
    result = await _run_correction_async(input_text)
    
    # Verificações
    assert result == expected_output
    assert mock_runner.call_count == 3
    # Deve dormir após cada falha
    assert mock_sleep.call_count == 2
    expected_calls = [call(RETRY_DELAY * 1), call(RETRY_DELAY * 2)]
    mock_sleep.assert_has_calls(expected_calls) 