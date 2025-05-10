import pytest
# Substituir importação direta do loguru por um mock
import os
import time
import pyperclip
import threading
from unittest.mock import patch, call, MagicMock
from src.main import WorkflowManager
from src.keyboard_listener import KeyboardManager
from src.animation import MagicAnimationWindow
from src.correction import (
    OpenAIError, ConnectionError, TimeoutError,
    AuthenticationError, RateLimitError, ServiceUnavailableError
)

# Para testar a função principal, precisamos mockar várias dependências e funções
# de outros módulos que são chamadas durante o fluxo

def test_workflow_manager_execute_workflow_success(mocker):
    """Testa o fluxo principal completo com sucesso usando WorkflowManager."""
    # Mock das funções principais chamadas por _execute_workflow
    mock_capture = mocker.patch('src.main.capture_selected_text')
    mock_correction = mocker.patch('src.main.get_corrected_text')
    mock_paste = mocker.patch('src.main.paste_text')
    
    # Mock de funções auxiliares
    mock_pyperclip_paste = mocker.patch('pyperclip.paste')
    mock_pyperclip_copy = mocker.patch('pyperclip.copy')
    mock_time_sleep = mocker.patch('time.sleep')
    mock_logger = mocker.patch('src.main.logger')
    
    # Configuração dos valores de retorno
    original_clipboard = "conteúdo original do clipboard"
    selected_text = "texto selecionado para corrigir"
    corrected_text = "texto corrigido pela LLM"
    
    mock_pyperclip_paste.return_value = original_clipboard
    mock_capture.return_value = selected_text
    mock_correction.return_value = corrected_text
    
    # Criar instância do WorkflowManager com um mock da animation_window
    mock_animation_window = MagicMock()
    manager = WorkflowManager(mock_animation_window)
    
    # Mock o método release do lock para evitar a exceção
    manager._lock = MagicMock()
    
    # Também mockar os sinais para capturar suas emissões
    manager.request_start_animation = MagicMock()
    manager.request_close_animation = MagicMock()
    manager.workflow_complete = MagicMock()
    
    # Executar o método diretamente
    manager._execute_workflow()
    
    # Verificações
    # 1. Fluxo de chamadas na ordem correta
    mock_capture.assert_called_once()
    mock_correction.assert_called_once_with(selected_text, api_key=mocker.ANY)
    mock_paste.assert_called_once_with(corrected_text)
    
    # 2. Salvamento e restauração do clipboard
    assert mock_pyperclip_paste.call_count >= 1  # Ao menos uma vez para salvar o conteúdo original
    assert mock_pyperclip_copy.call_count >= 1  # Ao menos uma vez para restaurar
    
    # 3. Verificar que o último pyperclip.copy é para restaurar o clipboard original
    mock_pyperclip_copy.assert_called_with(original_clipboard)
    
    # 4. Verificar emissão de sinais
    manager.request_start_animation.emit.assert_called_once()
    manager.request_close_animation.emit.assert_called_once()
    manager.workflow_complete.emit.assert_called_once()


def test_workflow_manager_capture_failure(mocker):
    """Testa o fluxo quando a captura falha (retorna None ou string vazia)."""
    # Mock das funções principais
    mock_capture = mocker.patch('src.main.capture_selected_text')
    mock_correction = mocker.patch('src.main.get_corrected_text')
    mock_paste = mocker.patch('src.main.paste_text')
    
    # Mock de funções auxiliares
    mock_pyperclip_paste = mocker.patch('pyperclip.paste')
    mock_pyperclip_copy = mocker.patch('pyperclip.copy')
    mock_logger = mocker.patch('src.main.logger')
    mock_print = mocker.patch('builtins.print')
    
    # Configuração para simular falha na captura
    original_clipboard = "conteúdo original do clipboard"
    mock_pyperclip_paste.return_value = original_clipboard
    mock_capture.return_value = None  # Simula falha na captura
    
    # Criar instância do WorkflowManager com um mock da animation_window
    mock_animation_window = MagicMock()
    manager = WorkflowManager(mock_animation_window)
    
    # Mock o método release do lock para evitar a exceção
    manager._lock = MagicMock()
    
    # Executar o método diretamente
    manager._execute_workflow()
    
    # Verificações
    mock_capture.assert_called_once()
    mock_correction.assert_not_called()  # Não deve chamar correção após falha
    mock_paste.assert_not_called()  # Não deve chamar colagem após falha
    
    # Deve restaurar o clipboard original
    mock_pyperclip_copy.assert_called_with(original_clipboard)
    
    # Verifica mensagem para o usuário
    user_message_calls = [call for call in mock_print.call_args_list if "Nenhum texto foi detectado" in str(call)]
    assert len(user_message_calls) >= 1


def test_workflow_manager_capture_exception(mocker):
    """Testa o fluxo quando a função de captura lança uma exceção."""
    # Mock das funções principais
    mock_capture = mocker.patch('src.main.capture_selected_text')
    mock_correction = mocker.patch('src.main.get_corrected_text')
    mock_paste = mocker.patch('src.main.paste_text')
    
    # Mock de funções auxiliares
    mock_pyperclip_paste = mocker.patch('pyperclip.paste')
    mock_pyperclip_copy = mocker.patch('pyperclip.copy')
    mock_logger = mocker.patch('src.main.logger')
    mock_print = mocker.patch('builtins.print')
    
    # Configuração para simular exceção na captura
    original_clipboard = "conteúdo original do clipboard"
    mock_pyperclip_paste.return_value = original_clipboard
    mock_capture.side_effect = Exception("Erro simulado durante a captura")
    
    # Criar instância do WorkflowManager com um mock da animation_window
    mock_animation_window = MagicMock()
    manager = WorkflowManager(mock_animation_window)
    
    # Mock o método release do lock para evitar a exceção
    manager._lock = MagicMock()
    
    # Executar o método diretamente
    manager._execute_workflow()
    
    # Verificações
    mock_capture.assert_called_once()
    mock_correction.assert_not_called()
    mock_paste.assert_not_called()
    
    # Deve restaurar o clipboard original
    mock_pyperclip_copy.assert_called_with(original_clipboard)
    
    # Deve ter logado a exceção
    mock_logger.error.assert_called_once()
    
    # Verifica mensagem para o usuário
    user_message_calls = [call for call in mock_print.call_args_list if "Erro ao capturar" in str(call)]
    assert len(user_message_calls) >= 1


def test_workflow_manager_correction_failure(mocker):
    """Testa o fluxo quando a correção falha (retorna None ou lança exceção)."""
    # Mock das funções principais
    mock_capture = mocker.patch('src.main.capture_selected_text')
    mock_correction = mocker.patch('src.main.get_corrected_text')
    mock_paste = mocker.patch('src.main.paste_text')
    
    # Mock de funções auxiliares
    mock_pyperclip_paste = mocker.patch('pyperclip.paste')
    mock_pyperclip_copy = mocker.patch('pyperclip.copy')
    mock_logger = mocker.patch('src.main.logger')
    mock_print = mocker.patch('builtins.print')
    
    # Configuração para simular falha na correção
    original_clipboard = "conteúdo original do clipboard"
    selected_text = "texto selecionado para corrigir"
    
    mock_pyperclip_paste.return_value = original_clipboard
    mock_capture.return_value = selected_text
    # Use MagicMock para evitar coroutine warning
    mock_correction.return_value = None  # Simula falha na correção
    
    # Criar instância do WorkflowManager com um mock da animation_window
    mock_animation_window = MagicMock()
    manager = WorkflowManager(mock_animation_window)
    
    # Mock o método release do lock para evitar a exceção
    manager._lock = MagicMock()
    
    # Executar o método diretamente
    manager._execute_workflow()
    
    # Verificações
    mock_capture.assert_called_once()
    mock_correction.assert_called_once()
    mock_paste.assert_not_called()  # Não deve chamar colagem após falha
    
    # Deve restaurar o clipboard original
    mock_pyperclip_copy.assert_called_with(original_clipboard)
    
    # Verifica mensagem para o usuário
    user_message_calls = [call for call in mock_print.call_args_list if "Falha ao obter correção" in str(call)]
    assert len(user_message_calls) >= 1


def test_workflow_manager_correction_exception(mocker):
    """Testa o fluxo quando a correção lança uma exceção genérica."""
    # Mock das funções principais
    mock_capture = mocker.patch('src.main.capture_selected_text')
    mock_correction = mocker.patch('src.main.get_corrected_text')
    mock_paste = mocker.patch('src.main.paste_text')
    
    # Mock de funções auxiliares
    mock_pyperclip_paste = mocker.patch('pyperclip.paste')
    mock_pyperclip_copy = mocker.patch('pyperclip.copy')
    mock_logger = mocker.patch('src.main.logger')
    mock_print = mocker.patch('builtins.print')
    
    # Configuração para simular exceção na correção
    original_clipboard = "conteúdo original do clipboard"
    selected_text = "texto selecionado para corrigir"
    
    mock_pyperclip_paste.return_value = original_clipboard
    mock_capture.return_value = selected_text
    mock_correction.side_effect = Exception("Erro simulado na API")
    
    # Criar instância do WorkflowManager com um mock da animation_window
    mock_animation_window = MagicMock()
    manager = WorkflowManager(mock_animation_window)
    
    # Mock o método release do lock para evitar a exceção
    manager._lock = MagicMock()
    
    # Executar o método diretamente
    manager._execute_workflow()
    
    # Verificações
    mock_capture.assert_called_once()
    mock_correction.assert_called_once()
    mock_paste.assert_not_called()  # Não deve chamar colagem após exceção
    
    # Deve restaurar o clipboard original
    mock_pyperclip_copy.assert_called_with(original_clipboard)
    
    # Deve ter logado a exceção com logger.error em vez de logger.exception
    mock_logger.error.assert_called_once()
    
    # Verifica mensagem para o usuário
    user_message_calls = [call for call in mock_print.call_args_list if "erro inesperado" in str(call).lower()]
    assert len(user_message_calls) >= 1


def test_workflow_manager_paste_exception(mocker):
    """Testa o fluxo quando a colagem lança uma exceção."""
    # Mock das funções principais
    mock_capture = mocker.patch('src.main.capture_selected_text')
    mock_correction = mocker.patch('src.main.get_corrected_text')
    mock_paste = mocker.patch('src.main.paste_text')
    
    # Mock de funções auxiliares
    mock_pyperclip_paste = mocker.patch('pyperclip.paste')
    mock_pyperclip_copy = mocker.patch('pyperclip.copy')
    mock_logger = mocker.patch('src.main.logger')
    mock_print = mocker.patch('builtins.print')
    
    # Configuração para simular exceção na colagem
    original_clipboard = "conteúdo original do clipboard"
    selected_text = "texto selecionado para corrigir"
    corrected_text = "texto corrigido pela LLM"
    
    mock_pyperclip_paste.return_value = original_clipboard
    mock_capture.return_value = selected_text
    mock_correction.return_value = corrected_text
    mock_paste.side_effect = Exception("Erro simulado na colagem")
    
    # Criar instância do WorkflowManager com um mock da animation_window
    mock_animation_window = MagicMock()
    manager = WorkflowManager(mock_animation_window)
    
    # Mock o método release do lock para evitar a exceção
    manager._lock = MagicMock()
    
    # Executar o método diretamente
    manager._execute_workflow()
    
    # Verificações
    mock_capture.assert_called_once()
    mock_correction.assert_called_once()
    mock_paste.assert_called_once()
    
    # Deve restaurar o clipboard original
    mock_pyperclip_copy.assert_called_with(original_clipboard)
    
    # Deve ter logado a exceção
    mock_logger.error.assert_called_once()
    
    # Verifica mensagem para o usuário
    user_message_calls = [call for call in mock_print.call_args_list if "Erro ao colar" in str(call)]
    assert len(user_message_calls) >= 1


def test_workflow_manager_connection_error(mocker):
    """Testa o fluxo quando ocorre um erro de conexão com a API OpenAI."""
    # Mock das funções principais
    mock_capture = mocker.patch('src.main.capture_selected_text')
    mock_correction = mocker.patch('src.main.get_corrected_text')
    mock_paste = mocker.patch('src.main.paste_text')
    
    # Mock de funções auxiliares
    mock_pyperclip_paste = mocker.patch('pyperclip.paste')
    mock_pyperclip_copy = mocker.patch('pyperclip.copy')
    mock_logger = mocker.patch('src.main.logger')
    mock_print = mocker.patch('builtins.print')
    
    # Configuração para simular erro de conexão
    original_clipboard = "conteúdo original do clipboard"
    selected_text = "texto selecionado para corrigir"
    
    mock_pyperclip_paste.return_value = original_clipboard
    mock_capture.return_value = selected_text
    mock_correction.side_effect = ConnectionError("Erro de conexão com a API OpenAI")
    
    # Criar instância do WorkflowManager com um mock da animation_window
    mock_animation_window = MagicMock()
    manager = WorkflowManager(mock_animation_window)
    
    # Mock o método release do lock para evitar a exceção
    manager._lock = MagicMock()
    
    # Executar o método diretamente
    manager._execute_workflow()
    
    # Verificações
    mock_capture.assert_called_once()
    mock_correction.assert_called_once()
    mock_paste.assert_not_called()
    
    # Deve restaurar o clipboard original
    mock_pyperclip_copy.assert_called_with(original_clipboard)
    
    # Verifica mensagem para o usuário - atualizada para a nova mensagem de erro
    user_message_calls = [call for call in mock_print.call_args_list if "Falha na conexão com OpenAI" in str(call)]
    assert len(user_message_calls) >= 1


def test_workflow_manager_timeout_error(mocker):
    """Testa o fluxo quando ocorre um timeout com a API OpenAI."""
    # Mock das funções principais
    mock_capture = mocker.patch('src.main.capture_selected_text')
    mock_correction = mocker.patch('src.main.get_corrected_text')
    mock_paste = mocker.patch('src.main.paste_text')
    
    # Mock de funções auxiliares
    mock_pyperclip_paste = mocker.patch('pyperclip.paste')
    mock_pyperclip_copy = mocker.patch('pyperclip.copy')
    mock_logger = mocker.patch('src.main.logger')
    mock_print = mocker.patch('builtins.print')
    
    # Configuração para simular timeout
    original_clipboard = "conteúdo original do clipboard"
    selected_text = "texto selecionado para corrigir"
    
    mock_pyperclip_paste.return_value = original_clipboard
    mock_capture.return_value = selected_text
    mock_correction.side_effect = TimeoutError("Timeout ao comunicar com a API OpenAI")
    
    # Criar instância do WorkflowManager com um mock da animation_window
    mock_animation_window = MagicMock()
    manager = WorkflowManager(mock_animation_window)
    
    # Mock o método release do lock para evitar a exceção
    manager._lock = MagicMock()
    
    # Executar o método diretamente
    manager._execute_workflow()
    
    # Verificações
    mock_capture.assert_called_once()
    mock_correction.assert_called_once()
    mock_paste.assert_not_called()
    
    # Deve restaurar o clipboard original
    mock_pyperclip_copy.assert_called_with(original_clipboard)
    
    # Verifica mensagem para o usuário
    user_message_calls = [call for call in mock_print.call_args_list if "Timeout" in str(call)]
    assert len(user_message_calls) >= 1


def test_workflow_manager_authentication_error(mocker):
    """Testa o fluxo quando ocorre um erro de autenticação com a API OpenAI."""
    # Mock das funções principais
    mock_capture = mocker.patch('src.main.capture_selected_text')
    mock_correction = mocker.patch('src.main.get_corrected_text')
    mock_paste = mocker.patch('src.main.paste_text')
    
    # Mock de funções auxiliares
    mock_pyperclip_paste = mocker.patch('pyperclip.paste')
    mock_pyperclip_copy = mocker.patch('pyperclip.copy')
    mock_logger = mocker.patch('src.main.logger')
    mock_print = mocker.patch('builtins.print')
    
    # Configuração para simular erro de autenticação
    original_clipboard = "conteúdo original do clipboard"
    selected_text = "texto selecionado para corrigir"
    
    mock_pyperclip_paste.return_value = original_clipboard
    mock_capture.return_value = selected_text
    mock_correction.side_effect = AuthenticationError("Erro de autenticação com a API OpenAI")
    
    # Criar instância do WorkflowManager com um mock da animation_window
    mock_animation_window = MagicMock()
    manager = WorkflowManager(mock_animation_window)
    
    # Mock o método release do lock para evitar a exceção
    manager._lock = MagicMock()
    
    # Executar o método diretamente
    manager._execute_workflow()
    
    # Verificações
    mock_capture.assert_called_once()
    mock_correction.assert_called_once()
    mock_paste.assert_not_called()
    
    # Deve restaurar o clipboard original
    mock_pyperclip_copy.assert_called_with(original_clipboard)
    
    # Verifica mensagem para o usuário
    user_message_calls = [call for call in mock_print.call_args_list if "API OpenAI inválida" in str(call)]
    assert len(user_message_calls) >= 1


def test_workflow_manager_rate_limit_error(mocker):
    """Testa o fluxo quando ocorre um erro de limite de requisições."""
    # Mock das funções principais
    mock_capture = mocker.patch('src.main.capture_selected_text')
    mock_correction = mocker.patch('src.main.get_corrected_text')
    mock_paste = mocker.patch('src.main.paste_text')
    
    # Mock de funções auxiliares
    mock_pyperclip_paste = mocker.patch('pyperclip.paste')
    mock_pyperclip_copy = mocker.patch('pyperclip.copy')
    mock_logger = mocker.patch('src.main.logger')
    mock_print = mocker.patch('builtins.print')
    
    # Configuração para simular rate limit
    original_clipboard = "conteúdo original do clipboard"
    selected_text = "texto selecionado para corrigir"
    
    mock_pyperclip_paste.return_value = original_clipboard
    mock_capture.return_value = selected_text
    mock_correction.side_effect = RateLimitError("Limite de requisições excedido")
    
    # Criar instância do WorkflowManager com um mock da animation_window
    mock_animation_window = MagicMock()
    manager = WorkflowManager(mock_animation_window)
    
    # Mock o método release do lock para evitar a exceção
    manager._lock = MagicMock()
    
    # Executar o método diretamente
    manager._execute_workflow()
    
    # Verificações
    mock_capture.assert_called_once()
    mock_correction.assert_called_once()
    mock_paste.assert_not_called()
    
    # Deve restaurar o clipboard original
    mock_pyperclip_copy.assert_called_with(original_clipboard)
    
    # Verifica mensagem para o usuário - atualizada para a nova mensagem de erro
    user_message_calls = [call for call in mock_print.call_args_list if "Limite de uso OpenAI excedido" in str(call)]
    assert len(user_message_calls) >= 1


def test_workflow_manager_service_unavailable_error(mocker):
    """Testa o fluxo quando o serviço OpenAI está indisponível."""
    # Mock das funções principais
    mock_capture = mocker.patch('src.main.capture_selected_text')
    mock_correction = mocker.patch('src.main.get_corrected_text')
    mock_paste = mocker.patch('src.main.paste_text')
    
    # Mock de funções auxiliares
    mock_pyperclip_paste = mocker.patch('pyperclip.paste')
    mock_pyperclip_copy = mocker.patch('pyperclip.copy')
    mock_logger = mocker.patch('src.main.logger')
    mock_print = mocker.patch('builtins.print')
    
    # Configuração para simular serviço indisponível
    original_clipboard = "conteúdo original do clipboard"
    selected_text = "texto selecionado para corrigir"
    
    mock_pyperclip_paste.return_value = original_clipboard
    mock_capture.return_value = selected_text
    mock_correction.side_effect = ServiceUnavailableError("Serviço OpenAI indisponível")
    
    # Criar instância do WorkflowManager com um mock da animation_window
    mock_animation_window = MagicMock()
    manager = WorkflowManager(mock_animation_window)
    
    # Mock o método release do lock para evitar a exceção
    manager._lock = MagicMock()
    
    # Executar o método diretamente
    manager._execute_workflow()
    
    # Verificações
    mock_capture.assert_called_once()
    mock_correction.assert_called_once()
    mock_paste.assert_not_called()
    
    # Deve restaurar o clipboard original
    mock_pyperclip_copy.assert_called_with(original_clipboard)
    
    # Verifica mensagem para o usuário - atualizada para a nova mensagem de erro
    user_message_calls = [call for call in mock_print.call_args_list if "Serviço OpenAI indisponível" in str(call)]
    assert len(user_message_calls) >= 1


def test_keyboard_manager(mocker):
    """Testa a classe KeyboardManager que gerencia os hotkeys."""
    # Mock para as funções da biblioteca pynput
    mock_global_hotkeys = mocker.patch('src.keyboard_listener.GlobalHotKeys')
    # Configurar o retorno do mock para não levantar exceção
    mock_global_hotkeys.return_value.start.return_value = None
    mock_global_hotkeys.return_value.stop.return_value = None
    mock_global_hotkeys.return_value.join.return_value = None
    
    mock_logger = mocker.patch('src.keyboard_listener.logger')
    
    # Criar uma função de callback para testar
    callback_fn = MagicMock()
    callback_fn.__name__ = "test_callback"  # Necessário para o log
    
    # Criar instância do KeyboardManager
    manager = KeyboardManager()
    
    # Testar registro de hotkey - mockando qualquer exceção interna
    mocker.patch.object(manager, '_format_hotkey_string', return_value="<ctrl>+<alt>+c")
    
    # Garantir que o método add_hotkey não levante exceção - sem usar 'with'
    mocker.patch('src.keyboard_listener.logger.error')
    result = manager.add_hotkey("ctrl+alt+c", callback_fn)
    
    # Verificar que o mockado retornou True
    assert result is True
    
    # Verificar que o formato da hotkey foi convertido corretamente
    assert "<ctrl>+<alt>+c" in manager.hotkey_mappings
    assert manager.hotkey_mappings["<ctrl>+<alt>+c"] == callback_fn
    
    # Testar início do listener
    manager.start()
    mock_global_hotkeys.assert_called_once()
    mock_global_hotkeys.return_value.start.assert_called_once()
    
    # Testar parada do listener
    manager.stop()
    mock_global_hotkeys.return_value.stop.assert_called_once()
    mock_global_hotkeys.return_value.join.assert_called_once()


def test_workflow_manager_with_gui_integration(mocker):
    """Testa a integração entre WorkflowManager e a GUI com sinais e slots."""
    # Mock das funções principais
    mock_capture = mocker.patch('src.main.capture_selected_text')
    mock_correction = mocker.patch('src.main.get_corrected_text')
    mock_paste = mocker.patch('src.main.paste_text')
    
    # Mock de funções auxiliares
    mock_pyperclip_paste = mocker.patch('pyperclip.paste')
    mock_pyperclip_copy = mocker.patch('pyperclip.copy')
    mock_time_sleep = mocker.patch('time.sleep')
    mock_logger = mocker.patch('src.main.logger')
    
    # Configuração dos valores de retorno
    original_clipboard = "conteúdo original do clipboard"
    selected_text = "texto selecionado para corrigir"
    corrected_text = "texto corrigido pela LLM"
    
    mock_pyperclip_paste.return_value = original_clipboard
    mock_capture.return_value = selected_text
    mock_correction.return_value = corrected_text
    
    # Criar instância do WorkflowManager com mocks da animation_window e gui_window
    mock_animation_window = MagicMock()
    mock_gui_window = MagicMock()
    
    # Criar o manager com os mocks
    manager = WorkflowManager(mock_animation_window, mock_gui_window)
    
    # Substituir os sinais por mocks para poder rastrear as emissões
    manager.update_text_display = MagicMock()
    manager.update_status = MagicMock()
    manager.workflow_complete = MagicMock()
    manager.request_start_animation = MagicMock()
    manager.request_close_animation = MagicMock()
    
    # Mock o método release do lock para evitar a exceção
    manager._lock = MagicMock()
    
    # Executar o método diretamente
    manager._execute_workflow()
    
    # Verificações básicas do fluxo
    mock_capture.assert_called_once()
    mock_correction.assert_called_once_with(selected_text, api_key=mocker.ANY)
    mock_paste.assert_called_once_with(corrected_text)
    
    # Verificações específicas da integração com a GUI
    # 1. Verificar que o update_text_display foi emitido corretamente
    assert manager.update_text_display.emit.call_count >= 2
    # Com texto original após captura
    manager.update_text_display.emit.assert_any_call(selected_text, "")
    # Com texto original e corrigido após correção
    manager.update_text_display.emit.assert_any_call(selected_text, corrected_text)
    
    # 2. Verificar que o workflow_complete foi emitido para atualizar a GUI
    manager.workflow_complete.emit.assert_called_once_with(True)
    

def test_workflow_manager_gui_error_handling(mocker):
    """Testa o tratamento de erros na integração do WorkflowManager com a GUI."""
    # Mock das funções principais
    mock_capture = mocker.patch('src.main.capture_selected_text')
    mock_correction = mocker.patch('src.main.get_corrected_text')
    mock_paste = mocker.patch('src.main.paste_text')
    mock_print = mocker.patch('builtins.print')
    
    # Mock de funções auxiliares
    mock_pyperclip_paste = mocker.patch('pyperclip.paste')
    mock_pyperclip_copy = mocker.patch('pyperclip.copy')
    
    # Configuração para simular falha na captura
    original_clipboard = "conteúdo original do clipboard"
    mock_pyperclip_paste.return_value = original_clipboard
    mock_capture.return_value = None  # Simula falha na captura
    
    # Criar instância do WorkflowManager com mocks
    mock_animation_window = MagicMock()
    mock_gui_window = MagicMock()
    
    # Criar o manager com os mocks
    manager = WorkflowManager(mock_animation_window, mock_gui_window)
    
    # Substituir os sinais por mocks para poder rastrear as emissões
    manager.update_text_display = MagicMock()
    manager.update_status = MagicMock()
    manager.workflow_complete = MagicMock()
    manager.request_start_animation = MagicMock()
    manager.request_close_animation = MagicMock()
    
    # Mock o método release do lock
    manager._lock = MagicMock()
    
    # Executar o fluxo de workflow
    manager._execute_workflow()
    
    # Verificações de tratamento de erro
    # 1. Verificar que o sinal de status de erro foi emitido
    manager.update_status.emit.assert_called_once()
    error_args = manager.update_status.emit.call_args[0]
    assert "Nenhum texto foi detectado" in error_args[0]
    assert error_args[1] is True  # error=True
    
    # 2. Verificar que o workflow_complete é chamado com False para indicar falha
    manager.workflow_complete.emit.assert_called_once_with(False) 