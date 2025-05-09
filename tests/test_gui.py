import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtCore import Qt, Signal, Slot, QTimer
from PySide6.QtWidgets import QApplication
import sys
import os

# Importando os componentes a serem testados
from src.gui import TextaGuiWindow
from src.main import WorkflowManager


@pytest.fixture
def app():
    """Fixture para criar uma instância de QApplication."""
    # Verificar se já existe uma instância
    if not QApplication.instance():
        app = QApplication(sys.argv)
    else:
        app = QApplication.instance()
    yield app
    # Não finaliza o app para não afetar outros testes


@pytest.fixture
def gui_window(app):
    """Fixture para criar uma instância de TextaGuiWindow."""
    window = TextaGuiWindow()
    return window


def test_gui_window_creation(gui_window):
    """Testa a criação básica da janela GUI."""
    assert gui_window is not None
    assert gui_window.windowTitle() == "Texta AI"
    assert gui_window.width() == 820  # Tamanho definido na implementação
    assert gui_window.height() == 500


def test_gui_set_text_content(gui_window):
    """
    Testa a funcionalidade de definir o conteúdo de texto original e corrigido.
    """
    original_text = "Este é um texto original para teste."
    corrected_text = "Este é um texto corrigido para teste."
    
    # Chamar o método que estamos testando
    gui_window.set_text_content(original_text, corrected_text)
    
    # Verificar se os textos foram definidos corretamente nos widgets
    assert gui_window.original_text == original_text
    assert gui_window.corrected_text == corrected_text
    assert gui_window.original_text_edit.toPlainText() == original_text
    assert gui_window.corrected_text_edit.toPlainText() == corrected_text


def test_gui_set_status(gui_window, mocker):
    """
    Testa a definição de mensagens de status com diferentes estilos.
    """
    # Precisamos mockear a verificação isVisible() para o teste funcionar
    mocker.patch.object(gui_window, 'isVisible', return_value=True)
    
    # Capturar diretamente as chamadas ao método setText do QLabel 
    mock_set_text = mocker.patch.object(gui_window.status_label, 'setText')
    
    # Testando mensagem de sucesso
    success_message = "Operação concluída com sucesso!"
    gui_window.set_status(success_message)
    mock_set_text.assert_called_with(success_message)
    
    # Testando mensagem de erro
    error_message = "Ocorreu um erro na operação!"
    gui_window.set_status(error_message, error=True)
    mock_set_text.assert_called_with(error_message)


def test_gui_button_click(gui_window, mocker):
    """
    Testa o comportamento do botão Corrigir quando clicado.
    """
    # Mock para QApplication.processEvents()
    mock_process_events = mocker.patch('src.gui.QApplication.processEvents')
    # Mock para time.sleep()
    mock_sleep = mocker.patch('src.gui.time.sleep')
    
    # Espionar o sinal button_clicked
    gui_window.button_clicked = MagicMock()
    
    # Executar o clique no botão
    gui_window._on_button_clicked()
    
    # Verificações
    assert gui_window.is_processing is True  # Estado de processamento ativado
    assert not gui_window.isVisible()  # Janela deve estar oculta
    mock_process_events.assert_called_once()  # processEvents deve ter sido chamado
    mock_sleep.assert_called_once()  # time.sleep deve ter sido chamado
    gui_window.button_clicked.emit.assert_called_once()  # Sinal deve ter sido emitido


def test_gui_reset_state_success(gui_window, mocker):
    """
    Testa o reset da GUI após uma operação bem-sucedida.
    """
    # Mock para toggle_visibility
    mock_toggle = mocker.patch.object(gui_window, 'toggle_visibility')
    # Mock para set_status
    mock_set_status = mocker.patch.object(gui_window, 'set_status')
    # Mock para QTimer.singleShot
    mock_timer = mocker.patch('src.gui.QTimer.singleShot')
    
    # Configurar para um estado inicial de processamento
    gui_window._set_processing_state(True)
    gui_window.hide()  # Ocultar a janela como se estivesse processando
    
    # Chamar reset_state com sucesso=True
    gui_window.reset_state(True)
    
    # Verificações
    assert gui_window.is_processing is False  # Estado de processamento desativado
    mock_toggle.assert_called_once()  # toggle_visibility deve ter sido chamado
    mock_set_status.assert_called_with("Texto corrigido!")
    mock_timer.assert_called_once()  # Timer para limpar mensagem de status


def test_gui_reset_state_failure(gui_window, mocker):
    """
    Testa o reset da GUI após uma operação malsucedida.
    """
    # Mock para toggle_visibility
    mock_toggle = mocker.patch.object(gui_window, 'toggle_visibility')
    # Mock para set_status
    mock_set_status = mocker.patch.object(gui_window, 'set_status')
    
    # Configurar para um estado inicial de processamento
    gui_window._set_processing_state(True)
    gui_window.hide()  # Ocultar a janela como se estivesse processando
    
    # Chamar reset_state com sucesso=False
    gui_window.reset_state(False)
    
    # Verificações
    assert gui_window.is_processing is False  # Estado de processamento desativado
    mock_toggle.assert_called_once()  # toggle_visibility deve ter sido chamado
    mock_set_status.assert_called_with("Ocorreu um erro no fluxo.", error=True)


def test_signal_structure():
    """
    Teste simplificado para verificar existência de sinais no WorkflowManager.
    Evita problemas com mocks do Qt.
    """
    # Criar instâncias mínimas necessárias
    mock_animation = MagicMock()
    manager = WorkflowManager(mock_animation)
    
    # Verificar existência de sinais
    assert hasattr(manager, 'update_text_display')
    assert hasattr(manager, 'update_status')
    assert isinstance(manager.update_text_display, Signal)
    assert isinstance(manager.update_status, Signal)


def test_workflow_manager_update_gui_signals(mocker):
    """
    Testa a emissão de sinais do WorkflowManager para atualizar a GUI.
    """
    # Mock para as instâncias necessárias
    mock_animation_window = MagicMock()
    mock_gui_window = MagicMock()
    
    # Criar o WorkflowManager com os mocks
    manager = WorkflowManager(mock_animation_window, mock_gui_window)
    
    # Substituir os sinais por mocks para poder rastrear as emissões
    manager.update_text_display = MagicMock()
    manager.update_status = MagicMock()
    manager.request_start_animation = MagicMock()
    manager.request_close_animation = MagicMock()
    manager.workflow_complete = MagicMock()
    
    # Simular a captura de texto bem-sucedida
    original_text = "texto capturado"
    corrected_text = "texto corrigido"
    
    # Patch várias funções para não executarem ações reais
    with patch('src.main.capture_selected_text', return_value=original_text), \
         patch('src.main.get_corrected_text', return_value=corrected_text), \
         patch('src.main.paste_text'), \
         patch('time.sleep'), \
         patch('pyperclip.paste', return_value=""), \
         patch('pyperclip.copy'):
        
        # Executar o fluxo
        manager._lock = MagicMock()  # Evitar bloqueio real
        manager._execute_workflow()
        
        # Verificar se os sinais foram emitidos com os argumentos corretos
        assert manager.update_text_display.emit.call_count >= 2
        
        # Verificar primeira emissão com texto original
        first_call_args = manager.update_text_display.emit.call_args_list[0][0]
        assert first_call_args[0] == original_text
        
        # Verificar segunda emissão com ambos os textos
        second_call_args = manager.update_text_display.emit.call_args_list[1][0]
        assert second_call_args[0] == original_text
        assert second_call_args[1] == corrected_text


def test_workflow_manager_error_handling_signals(mocker):
    """
    Testa a emissão de sinais de erro do WorkflowManager para a GUI.
    """
    # Mock para as instâncias necessárias
    mock_animation_window = MagicMock()
    mock_gui_window = MagicMock()
    
    # Criar o WorkflowManager com os mocks
    manager = WorkflowManager(mock_animation_window, mock_gui_window)
    
    # Substituir os sinais por mocks para poder rastrear as emissões
    manager.update_status = MagicMock()
    manager.request_start_animation = MagicMock()
    manager.request_close_animation = MagicMock()
    manager.workflow_complete = MagicMock()
    
    # Simular um erro na captura
    with patch('src.main.capture_selected_text', side_effect=Exception("Erro simulado")), \
         patch('time.sleep'), \
         patch('pyperclip.paste', return_value=""), \
         patch('pyperclip.copy'), \
         patch('builtins.print'):
        
        # Executar o fluxo
        manager._lock = MagicMock()  # Evitar bloqueio real
        manager._execute_workflow()
        
        # Verificar se o sinal de erro foi emitido
        manager.update_status.emit.assert_called_once()
        error_call_args = manager.update_status.emit.call_args[0]
        assert "Erro" in error_call_args[0]
        assert error_call_args[1] is True  # error=True 


def test_app_icon_setup(gui_window, mocker):
    """Testa a configuração do ícone do aplicativo com logo existente."""
    # Criar um caminho de logo de teste
    test_resources_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src', 'resources', 'images')
    test_logo_path = os.path.join(test_resources_dir, 'logo.png')
    
    # Mock para verificar se o arquivo existe
    mock_exists = mocker.patch('os.path.exists', return_value=True)
    # Mock para QIcon para evitar operações reais com arquivos
    mock_icon = MagicMock()
    mock_qicon = mocker.patch('src.gui.QIcon', return_value=mock_icon)
    # Mock para setWindowIcon
    mock_set_icon = mocker.patch.object(gui_window, 'setWindowIcon')
    # Mock para QApplication.instance()
    mock_app_instance = MagicMock()
    mock_qapp = mocker.patch('src.gui.QApplication.instance', return_value=mock_app_instance)
    
    # Chamar o método de configuração do ícone
    gui_window._set_app_icon()
    
    # Verificar se os métodos corretos foram chamados
    mock_exists.assert_called_with(test_logo_path)
    mock_qicon.assert_called_once_with(test_logo_path)
    # Verificar se o ícone foi definido para a janela
    mock_set_icon.assert_called_once_with(mock_icon)
    # Verificar se tentou definir o ícone para toda a aplicação
    mock_app_instance.setWindowIcon.assert_called_once_with(mock_icon)


def test_app_icon_setup_no_logo(gui_window, mocker):
    """Testa o comportamento quando o arquivo de logo não existe."""
    # Mock para verificar se o arquivo existe (retornando False)
    mock_exists = mocker.patch('os.path.exists', return_value=False)
    # Mock para QIcon para evitar operações reais com arquivos
    mock_qicon = mocker.patch('src.gui.QIcon')
    # Mock para setWindowIcon
    mock_set_icon = mocker.patch.object(gui_window, 'setWindowIcon')
    
    # Chamar o método de configuração do ícone
    gui_window._set_app_icon()
    
    # Verificar que QIcon não foi chamado
    mock_qicon.assert_not_called()
    # Verificar que setWindowIcon não foi chamado
    mock_set_icon.assert_not_called()
    # Verificar que app_icon foi definido como None
    assert gui_window.app_icon is None


def test_gui_logo_in_header(mocker, app):
    """Testa a exibição do logo no cabeçalho da GUI quando existe."""
    # Precisamos criar uma nova instância do widget com os mocks prontos antes da inicialização
    # Mock para verificar se o arquivo existe (antes de criar o widget)
    mock_exists = mocker.patch('os.path.exists', return_value=True)
    # Mock para QPixmap e scaled
    mock_scaled = MagicMock()
    mock_pixmap = MagicMock()
    mock_pixmap.scaled.return_value = mock_scaled
    mock_qpixmap = mocker.patch('src.gui.QPixmap', return_value=mock_pixmap)
    # Mock para o método setPixmap
    with patch('PySide6.QtWidgets.QLabel.setPixmap') as mock_set_pixmap:
        # Criar uma instância com os mocks já configurados
        gui_window = TextaGuiWindow()
        
        # Verificações
        mock_exists.assert_called()
        mock_qpixmap.assert_called()
        # Verificar que o pixmap foi escalado com os parâmetros corretos
        mock_pixmap.scaled.assert_called_with(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        # Verificar que setPixmap foi chamado com o pixmap escalado
        assert mock_set_pixmap.called


def test_gui_logo_fallback(mocker, app):
    """Testa o fallback para emoji quando o logo não está disponível."""
    # Precisamos criar uma nova instância com mocks prontos
    # Mock para verificar se o arquivo existe (retornando False)
    mock_exists = mocker.patch('os.path.exists', return_value=False)
    # Mock para QPixmap
    mock_qpixmap = mocker.patch('src.gui.QPixmap')
    # Mock para setText
    with patch('PySide6.QtWidgets.QLabel.setText') as mock_set_text:
        # Criar instância depois dos mocks
        gui_window = TextaGuiWindow()
        
        # Verificações
        mock_exists.assert_called()
        mock_qpixmap.assert_not_called()
        # Verificar que setText foi chamado com o emoji
        mock_set_text.assert_any_call("🤖") 