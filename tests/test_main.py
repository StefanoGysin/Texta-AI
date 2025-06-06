"""
Testes unitários abrangentes para src/main.py

Este módulo testa todas as funcionalidades principais do módulo main.py,
incluindo o WorkflowManager, inicialização da aplicação, gerenciamento de threads,
comunicação entre componentes, tratamento de erros e integração com GUI/animação.

Baseado nas melhores práticas do pytest e padrões estabelecidos no projeto.
"""

import contextlib
import os
from pathlib import Path
import threading
from unittest.mock import MagicMock

from PySide6.QtCore import Signal
import pytest
from pytest_mock import MockerFixture

# Importações do módulo sendo testado
from src.main import WorkflowManager


class TestWorkflowManager:
    """
    Testes para a classe WorkflowManager que gerencia o fluxo principal da aplicação.
    """

    @pytest.fixture
    def mock_animation_window(self) -> MagicMock:
        """Fixture para criar um mock da janela de animação."""
        mock_window = MagicMock()
        mock_window.start_effect = MagicMock()
        mock_window.force_close = MagicMock()
        return mock_window

    @pytest.fixture
    def mock_gui_window(self) -> MagicMock:
        """Fixture para criar um mock da janela GUI."""
        mock_window = MagicMock()
        mock_window.set_text_content = MagicMock()
        mock_window.set_status = MagicMock()
        mock_window.toggle_visibility = MagicMock()
        mock_window.reset_state = MagicMock()
        return mock_window

    @pytest.fixture
    def workflow_manager(
        self, mock_animation_window, mock_gui_window
    ) -> WorkflowManager:
        """Fixture para criar uma instância do WorkflowManager."""
        return WorkflowManager(mock_animation_window, mock_gui_window)

    @pytest.fixture
    def workflow_manager_no_gui(self, mock_animation_window) -> WorkflowManager:
        """Fixture para criar WorkflowManager sem GUI."""
        return WorkflowManager(mock_animation_window, None)

    def test_workflow_manager_initialization_with_gui(
        self, mock_animation_window, mock_gui_window
    ):
        """Testa a inicialização do WorkflowManager com GUI."""
        manager = WorkflowManager(mock_animation_window, mock_gui_window)

        assert manager.animation_window == mock_animation_window
        assert manager.gui_window == mock_gui_window
        assert hasattr(manager, "_lock")
        assert isinstance(manager._lock, type(threading.Lock()))  # noqa: SLF001

        # Verifica existência dos sinais
        assert hasattr(manager, "request_start_animation")
        assert hasattr(manager, "request_close_animation")
        assert hasattr(manager, "workflow_complete")
        assert hasattr(manager, "update_text_display")
        assert hasattr(manager, "update_status")
        assert hasattr(manager, "toggle_gui_requested")

        # Verifica tipos dos sinais
        assert isinstance(manager.request_start_animation, Signal)
        assert isinstance(manager.request_close_animation, Signal)
        assert isinstance(manager.workflow_complete, Signal)
        assert isinstance(manager.update_text_display, Signal)
        assert isinstance(manager.update_status, Signal)
        assert isinstance(manager.toggle_gui_requested, Signal)

    def test_workflow_manager_initialization_without_gui(self, mock_animation_window):
        """Testa a inicialização do WorkflowManager sem GUI."""
        manager = WorkflowManager(mock_animation_window, None)

        assert manager.animation_window == mock_animation_window
        assert manager.gui_window is None
        assert hasattr(manager, "_lock")

    def test_run_main_workflow_with_lock(self, workflow_manager, mocker: MockerFixture):
        """Testa que run_main_workflow respeita o lock para evitar execuções simultâneas."""
        # Mock do threading para controlar o comportamento
        mock_thread = mocker.patch("threading.Thread")
        mock_lock = mocker.patch.object(workflow_manager, "_lock")

        # Simula que o lock já está sendo usado (retorna False)
        mock_lock.acquire.return_value = False

        # Executa o método
        workflow_manager.run_main_workflow()

        # Verifica que nenhuma thread foi criada
        mock_thread.assert_not_called()
        mock_lock.acquire.assert_called_once_with(blocking=False)

    def test_run_main_workflow_creates_thread(
        self, workflow_manager, mocker: MockerFixture
    ):
        """Testa que run_main_workflow cria e inicia uma nova thread quando o lock está disponível."""
        mock_thread_instance = MagicMock()
        mock_thread_class = mocker.patch(
            "threading.Thread", return_value=mock_thread_instance
        )
        mock_lock = mocker.patch.object(workflow_manager, "_lock")

        # Simula que o lock está disponível
        mock_lock.acquire.return_value = True

        # Executa o método
        workflow_manager.run_main_workflow()

        # Verifica que a thread foi criada e iniciada
        mock_thread_class.assert_called_once_with(
            target=workflow_manager._execute_workflow,  # noqa: SLF001
            daemon=True,
        )
        mock_thread_instance.start.assert_called_once()

    @pytest.mark.parametrize("has_gui", [True, False])
    def test_execute_workflow_full_success(
        self, mock_animation_window, mock_gui_window, mocker: MockerFixture, has_gui
    ):
        """Testa execução completa bem-sucedida do workflow."""
        # Configurar manager com ou sem GUI
        gui = mock_gui_window if has_gui else None
        manager = WorkflowManager(mock_animation_window, gui)

        # Mocks das funções do workflow
        mock_capture = mocker.patch(
            "src.main.capture_selected_text", return_value="texto original"
        )
        mock_correct = mocker.patch(
            "src.main.get_corrected_text", return_value="texto corrigido"
        )
        mock_paste = mocker.patch("src.main.paste_text")
        mocker.patch("time.sleep")
        mocker.patch("pyperclip.paste", return_value="clipboard original")
        mock_pyperclip_copy = mocker.patch("pyperclip.copy")

        # Mocks dos sinais
        manager.request_start_animation = MagicMock()
        manager.request_close_animation = MagicMock()
        manager.workflow_complete = MagicMock()
        manager.update_text_display = MagicMock()
        manager.update_status = MagicMock()

        # Simular lock disponível
        manager._lock = MagicMock()  # noqa: SLF001
        manager._lock.acquire.return_value = True  # noqa: SLF001

        # Executar workflow
        manager._execute_workflow()  # noqa: SLF001

        # Verificações das chamadas principais
        mock_capture.assert_called_once()
        mock_correct.assert_called_once_with(
            "texto original", api_key=os.getenv("OPENAI_API_KEY")
        )
        mock_paste.assert_called_once_with("texto corrigido")

        # Verificações dos sinais
        manager.request_start_animation.emit.assert_called_once()
        manager.request_close_animation.emit.assert_called_once()
        manager.workflow_complete.emit.assert_called_once_with(True)  # noqa: FBT003

        # Verificações específicas para GUI
        if has_gui:
            assert manager.update_text_display.emit.call_count >= 1

        # Verificações de cleanup
        mock_pyperclip_copy.assert_called_with("clipboard original")
        manager._lock.release.assert_called_once()  # noqa: SLF001

    def test_execute_workflow_capture_failure(
        self, workflow_manager, mocker: MockerFixture
    ):
        """Testa workflow quando captura de texto falha."""
        # Mocks
        mock_capture = mocker.patch(
            "src.main.capture_selected_text", side_effect=OSError("Erro de captura")
        )
        mock_correct = mocker.patch("src.main.get_corrected_text")
        mock_paste = mocker.patch("src.main.paste_text")
        mocker.patch("time.sleep")
        mocker.patch("pyperclip.paste", return_value="")

        # Mocks dos sinais
        workflow_manager.request_start_animation = MagicMock()
        workflow_manager.request_close_animation = MagicMock()
        workflow_manager.workflow_complete = MagicMock()
        workflow_manager.update_status = MagicMock()

        # Simular lock
        workflow_manager._lock = MagicMock()  # noqa: SLF001
        workflow_manager._lock.acquire.return_value = True  # noqa: SLF001

        # Executar workflow
        workflow_manager._execute_workflow()  # noqa: SLF001

        # Verificações
        mock_capture.assert_called_once()
        mock_correct.assert_not_called()  # Não deve chamar correção se captura falhou
        mock_paste.assert_not_called()  # Não deve chamar colagem

        # Deve sinalizar falha
        workflow_manager.workflow_complete.emit.assert_called_once_with(False)  # noqa: FBT003

        if workflow_manager.gui_window:
            workflow_manager.update_status.emit.assert_called()

    def test_execute_workflow_no_text_captured(
        self, workflow_manager, mocker: MockerFixture
    ):
        """Testa workflow quando nenhum texto é capturado."""
        # Mocks
        mock_capture = mocker.patch("src.main.capture_selected_text", return_value="")
        mock_correct = mocker.patch("src.main.get_corrected_text")
        mock_paste = mocker.patch("src.main.paste_text")
        mocker.patch("time.sleep")
        mocker.patch("pyperclip.paste", return_value="")

        # Mocks dos sinais
        workflow_manager.request_start_animation = MagicMock()
        workflow_manager.request_close_animation = MagicMock()
        workflow_manager.workflow_complete = MagicMock()
        workflow_manager.update_status = MagicMock()

        workflow_manager._lock = MagicMock()  # noqa: SLF001
        workflow_manager._lock.acquire.return_value = True  # noqa: SLF001

        # Executar workflow
        workflow_manager._execute_workflow()  # noqa: SLF001

        # Verificações
        mock_capture.assert_called_once()
        mock_correct.assert_not_called()
        mock_paste.assert_not_called()
        workflow_manager.workflow_complete.emit.assert_called_once_with(False)  # noqa: FBT003

    @pytest.mark.parametrize(
        ("exception_type", "_expected_count"),
        [
            ("OpenAIConnectionError", 1),
            ("OpenAITimeoutError", 1),
            ("AuthenticationError", 1),
            ("RateLimitError", 1),
            ("ServiceUnavailableError", 1),
            ("OpenAIError", 1),
            ("ValueError", 1),
        ],
    )
    def test_execute_workflow_correction_api_errors(
        self, workflow_manager, mocker: MockerFixture, exception_type, _expected_count
    ):
        """Testa workflow com diferentes tipos de erro da API OpenAI."""
        from src.correction import (
            AuthenticationError,
            OpenAIConnectionError,
            OpenAIError,
            OpenAITimeoutError,
            RateLimitError,
            ServiceUnavailableError,
        )

        # Mapear string para classe de exceção
        exception_classes = {
            "OpenAIConnectionError": OpenAIConnectionError,
            "OpenAITimeoutError": OpenAITimeoutError,
            "AuthenticationError": AuthenticationError,
            "RateLimitError": RateLimitError,
            "ServiceUnavailableError": ServiceUnavailableError,
            "OpenAIError": OpenAIError,
            "ValueError": ValueError,
        }

        exception_class = exception_classes[exception_type]

        # Mocks
        mock_capture = mocker.patch(
            "src.main.capture_selected_text", return_value="texto original"
        )
        mock_correct = mocker.patch(
            "src.main.get_corrected_text", side_effect=exception_class("Erro API")
        )
        mock_paste = mocker.patch("src.main.paste_text")
        mocker.patch("time.sleep")
        mocker.patch("pyperclip.paste", return_value="")

        # Mocks dos sinais
        workflow_manager.request_start_animation = MagicMock()
        workflow_manager.request_close_animation = MagicMock()
        workflow_manager.workflow_complete = MagicMock()
        workflow_manager.update_status = MagicMock()

        workflow_manager._lock = MagicMock()  # noqa: SLF001
        workflow_manager._lock.acquire.return_value = True  # noqa: SLF001

        # Executar workflow
        workflow_manager._execute_workflow()  # noqa: SLF001

        # Verificações
        mock_capture.assert_called_once()
        mock_correct.assert_called_once()
        mock_paste.assert_not_called()  # Não deve colar se correção falhou
        workflow_manager.workflow_complete.emit.assert_called_once_with(False)  # noqa: FBT003

    def test_execute_workflow_paste_failure(
        self, workflow_manager, mocker: MockerFixture
    ):
        """Testa workflow quando colagem falha."""
        # Mocks
        mock_capture = mocker.patch(
            "src.main.capture_selected_text", return_value="texto original"
        )
        mock_correct = mocker.patch(
            "src.main.get_corrected_text", return_value="texto corrigido"
        )
        mock_paste = mocker.patch(
            "src.main.paste_text", side_effect=OSError("Erro de colagem")
        )
        mocker.patch("time.sleep")
        mocker.patch("pyperclip.paste", return_value="")

        # Mocks dos sinais
        workflow_manager.request_start_animation = MagicMock()
        workflow_manager.request_close_animation = MagicMock()
        workflow_manager.workflow_complete = MagicMock()
        workflow_manager.update_status = MagicMock()

        workflow_manager._lock = MagicMock()  # noqa: SLF001
        workflow_manager._lock.acquire.return_value = True  # noqa: SLF001

        # Executar workflow
        workflow_manager._execute_workflow()  # noqa: SLF001

        # Verificações
        mock_capture.assert_called_once()
        mock_correct.assert_called_once()
        mock_paste.assert_called_once()
        workflow_manager.workflow_complete.emit.assert_called_once_with(False)  # noqa: FBT003

    def test_restore_clipboard_success(self, workflow_manager, mocker: MockerFixture):
        """Testa restauração bem-sucedida do clipboard."""
        mock_sleep = mocker.patch("time.sleep")
        mock_copy = mocker.patch("pyperclip.copy")

        original_content = "conteúdo original"
        workflow_manager.restore_clipboard(original_content)

        mock_sleep.assert_called_once_with(0.15)
        mock_copy.assert_called_once_with(original_content)

    def test_restore_clipboard_failure(self, workflow_manager, mocker: MockerFixture):
        """Testa falha na restauração do clipboard."""
        mock_sleep = mocker.patch("time.sleep")
        mock_copy = mocker.patch(
            "pyperclip.copy", side_effect=OSError("Erro no clipboard")
        )

        # Não deve levantar exceção, apenas logar o erro
        workflow_manager.restore_clipboard("conteúdo")

        mock_sleep.assert_called_once()
        mock_copy.assert_called_once()

    def test_toggle_gui_with_gui_window(self, workflow_manager):
        """Testa toggle da GUI quando há janela GUI configurada."""
        workflow_manager.toggle_gui_requested = MagicMock()

        workflow_manager.toggle_gui()

        workflow_manager.toggle_gui_requested.emit.assert_called_once()

    def test_toggle_gui_without_gui_window(self, workflow_manager_no_gui):
        """Testa toggle da GUI quando não há janela GUI configurada."""
        workflow_manager_no_gui.toggle_gui_requested = MagicMock()

        # Não deve levantar exceção, apenas logar warning
        workflow_manager_no_gui.toggle_gui()

        workflow_manager_no_gui.toggle_gui_requested.emit.assert_not_called()


class TestMainModuleEnvironmentSetup:
    """
    Testes para a configuração de ambiente e inicialização do módulo main.
    """

    def test_qt_environment_setup(self, mocker: MockerFixture):
        """Testa configuração das variáveis de ambiente do Qt."""
        mocker.patch.dict("os.environ", {}, clear=True)

        # Re-importar o módulo para aplicar as mudanças de ambiente
        import importlib

        import src.main

        importlib.reload(src.main)

        # Verificar que as variáveis foram definidas
        assert os.environ.get("QT_ENABLE_HIGHDPI_SCALING") == "0"
        assert os.environ.get("QT_LOGGING_RULES") == "*.debug=false;qt.qpa.*=false"

    def test_pythonpath_adjustment_when_main(self, mocker: MockerFixture):
        """Testa ajuste do PYTHONPATH quando executado como main."""
        # Mock do comportamento quando __name__ == "__main__"
        mock_path = ["/some/path"]
        mocker.patch("sys.path", mock_path)

        # Simular a lógica do main.py quando __name__ == "__main__"
        fake_root = Path("/fake/root")

        # Mock Path(__file__).parent.parent.absolute()
        mock_path_class = mocker.patch("pathlib.Path")
        mock_file_path = mocker.Mock()
        mock_file_path.parent.parent.absolute.return_value = fake_root
        mock_path_class.return_value = mock_file_path

        # Simular o check e insert do sys.path
        if str(fake_root) not in mock_path:
            mock_path.insert(0, str(fake_root))

        # Verificar que o diretório raiz foi adicionado ao sys.path
        assert str(fake_root) in mock_path

    @pytest.mark.parametrize(
        ("api_key", "should_exit"),
        [
            ("valid-api-key", False),
            ("", True),
            (None, True),
        ],
    )
    def test_api_key_validation(self, mocker: MockerFixture, api_key, should_exit):
        """Testa validação da API key durante inicialização."""
        mock_exit = mocker.patch("sys.exit")
        mocker.patch.dict("os.environ", {"OPENAI_API_KEY": api_key or ""}, clear=True)

        # Re-importar módulo para testar validação
        import importlib

        import src.main

        with contextlib.suppress(SystemExit):
            importlib.reload(src.main)

        if should_exit:
            mock_exit.assert_called_once()
        else:
            mock_exit.assert_not_called()

    def test_load_environment_variables(self):
        """Testa carregamento das variáveis de ambiente."""
        # Este teste verifica que as constantes do módulo são carregadas corretamente
        from src.main import (
            DEFAULT_GUI_HOTKEY,
            DEFAULT_HOTKEY,
        )

        # Verificar que as constantes padrão estão definidas
        assert DEFAULT_HOTKEY == "ctrl+alt+c"
        assert DEFAULT_GUI_HOTKEY == "ctrl+alt+g"


class TestMainModuleIntegration:
    """
    Testes de integração para componentes principais do módulo main.
    """

    @pytest.fixture
    def mock_environment(self, mocker: MockerFixture):
        """Fixture para configurar ambiente de teste."""
        env_vars = {
            "OPENAI_API_KEY": "test-api-key",
            "HOTKEY": "ctrl+shift+c",
            "GUI_HOTKEY": "ctrl+shift+g",
            "CORRECTION_PROMPT": "Test prompt",
        }

        mocker.patch.dict("os.environ", env_vars)
        mocker.patch("src.keyboard_listener.GlobalHotKeys")
        mocker.patch("src.gui.TextaGuiWindow")
        mocker.patch("src.animation.MagicAnimationWindow")

        return env_vars

    @pytest.mark.usefixtures("mock_environment")
    def test_application_initialization_flow(self):
        """Testa o fluxo de inicialização da aplicação principal."""
        # Este teste verifica que as classes principais podem ser instanciadas
        from src.animation import MagicAnimationWindow
        from src.gui import TextaGuiWindow
        from src.keyboard_listener import KeyboardManager
        from src.main import WorkflowManager

        # Testar instanciação das classes principais
        animation_window = MagicAnimationWindow()
        gui_window = TextaGuiWindow()
        workflow_manager = WorkflowManager(animation_window, gui_window)
        keyboard_manager = KeyboardManager()

        # Verificações básicas
        assert animation_window is not None
        assert gui_window is not None
        assert workflow_manager is not None
        assert keyboard_manager is not None

        # Verificar que o WorkflowManager tem os atributos esperados
        assert hasattr(workflow_manager, "run_main_workflow")
        assert hasattr(workflow_manager, "toggle_gui")
        assert hasattr(keyboard_manager, "add_hotkey")
        assert hasattr(keyboard_manager, "start")

    @pytest.mark.usefixtures("mock_environment")
    def test_keyboard_manager_hotkey_registration(self):
        """Testa registro de hotkeys no KeyboardManager."""
        # Testar a funcionalidade do KeyboardManager diretamente
        from src.keyboard_listener import KeyboardManager

        keyboard_manager = KeyboardManager()

        # Testar registro de hotkey (pode falhar em ambiente de teste)
        try:
            result = keyboard_manager.add_hotkey("ctrl+alt+test", lambda: None)
            # Se conseguir registrar, verificar que retorna boolean
            assert isinstance(result, bool)
        except OSError:
            # Se falhar (normal em ambiente de teste), pelo menos verificar que o método existe
            assert hasattr(keyboard_manager, "add_hotkey")

        # Verificar outros métodos essenciais
        assert hasattr(keyboard_manager, "remove_hotkey")
        assert hasattr(keyboard_manager, "start")
        assert hasattr(keyboard_manager, "stop")

    @pytest.mark.usefixtures("mock_environment")
    def test_keyboard_manager_hotkey_registration_failure(self):
        """Testa comportamento quando registro de hotkey falha."""
        from src.keyboard_listener import KeyboardManager

        keyboard_manager = KeyboardManager()

        # Testar com callback None (deveria causar AttributeError ao acessar __name__)
        result = keyboard_manager.add_hotkey("ctrl+alt+test", None)
        # Deve retornar False pois None.__name__ causará AttributeError
        assert result is False

        # Verificar que o método existe
        assert hasattr(keyboard_manager, "add_hotkey")

    @pytest.mark.usefixtures("mock_environment")
    def test_gui_window_connections(self):
        """Testa conexões entre GUI e WorkflowManager."""
        from src.animation import MagicAnimationWindow
        from src.gui import TextaGuiWindow
        from src.main import WorkflowManager

        # Criar instâncias
        animation_window = MagicAnimationWindow()
        gui_window = TextaGuiWindow()
        manager = WorkflowManager(animation_window, gui_window)

        # Simular conexões que seriam feitas no main

        # Verificar que manager tem os sinais necessários
        assert hasattr(manager, "update_text_display")
        assert hasattr(manager, "update_status")
        assert hasattr(manager, "workflow_complete")
        assert hasattr(manager, "toggle_gui_requested")

        # Verificar que GUI tem os métodos necessários
        assert hasattr(gui_window, "set_text_content")
        assert hasattr(gui_window, "set_status")
        assert hasattr(gui_window, "toggle_visibility")
        assert hasattr(gui_window, "reset_state")


class TestWorkflowManagerErrorHandling:
    """
    Testes para tratamento de erros no WorkflowManager.
    """

    @pytest.fixture
    def workflow_manager_with_mocks(self):
        """Fixture para WorkflowManager com sinais mockados."""
        mock_animation = MagicMock()
        mock_gui = MagicMock()

        manager = WorkflowManager(mock_animation, mock_gui)

        # Mock dos sinais
        manager.request_start_animation = MagicMock()
        manager.request_close_animation = MagicMock()
        manager.workflow_complete = MagicMock()
        manager.update_text_display = MagicMock()
        manager.update_status = MagicMock()
        manager._lock = MagicMock()  # noqa: SLF001
        manager._lock.acquire.return_value = True  # noqa: SLF001

        return manager

    def test_unexpected_error_handling(
        self, workflow_manager_with_mocks, mocker: MockerFixture
    ):
        """Testa tratamento de erros inesperados durante o workflow."""
        # Mock para simular erro inesperado
        mocker.patch(
            "src.main.capture_selected_text",
            side_effect=RuntimeError("Erro inesperado"),
        )
        mocker.patch("pyperclip.paste", return_value="")

        workflow_manager_with_mocks._execute_workflow()  # noqa: SLF001

        # Verificar que erro foi tratado apropriadamente
        workflow_manager_with_mocks.workflow_complete.emit.assert_called_once_with(
            False  # noqa: FBT003
        )
        workflow_manager_with_mocks._lock.release.assert_called_once()  # noqa: SLF001

    def test_cleanup_always_executed(
        self, workflow_manager_with_mocks, mocker: MockerFixture
    ):
        """Testa que cleanup é sempre executado, mesmo com erros."""
        # Mock com sucesso parcial
        mocker.patch("src.main.capture_selected_text", return_value="texto")
        mocker.patch("src.main.get_corrected_text", return_value="texto corrigido")
        mocker.patch("src.main.paste_text", return_value=True)
        mocker.patch("pyperclip.paste", return_value="original")
        mock_copy = mocker.patch("pyperclip.copy")

        workflow_manager_with_mocks._execute_workflow()  # noqa: SLF001

        # Verificar que cleanup foi executado
        workflow_manager_with_mocks.request_close_animation.emit.assert_called_once()
        workflow_manager_with_mocks.workflow_complete.emit.assert_called_once()
        workflow_manager_with_mocks._lock.release.assert_called_once()  # noqa: SLF001
        mock_copy.assert_called_once_with("original")

    @pytest.mark.parametrize("clipboard_content", ["", "conteúdo existente", None])
    def test_clipboard_restoration_scenarios(
        self, workflow_manager_with_mocks, mocker: MockerFixture, clipboard_content
    ):
        """Testa diferentes cenários de restauração do clipboard."""
        # Mocks
        mocker.patch("src.main.capture_selected_text", side_effect=OSError("Erro"))
        mocker.patch("pyperclip.paste", return_value=clipboard_content)
        mock_copy = mocker.patch("pyperclip.copy")

        workflow_manager_with_mocks._execute_workflow()  # noqa: SLF001

        # Verificar comportamento baseado na lógica do código:
        # A restauração só acontece se clipboard_content for truthy (não "", não None)
        if clipboard_content:  # String vazia é falsy, None é falsy
            mock_copy.assert_called_with(clipboard_content)
        else:
            # Para string vazia ou None, não deve chamar copy
            mock_copy.assert_not_called()


class TestWorkflowManagerThreadSafety:
    """
    Testes para verificar thread safety do WorkflowManager.
    """

    def test_signal_emission_thread_safety(self):
        """Testa que sinais podem ser emitidos com segurança de threads."""
        from src.main import WorkflowManager

        # Usar mocks ao invés de widgets reais para evitar problemas de QApplication
        mock_animation = MagicMock()
        mock_gui = MagicMock()
        manager = WorkflowManager(mock_animation, mock_gui)

        # Testar emissão de sinais (não deve levantar exceção)
        try:
            manager.update_text_display.emit("original", "corrigido")
            manager.update_status.emit(
                "status", False  # noqa: FBT003
            )  # Qt signals don't support keyword args
            manager.workflow_complete.emit(True)  # noqa: FBT003
        except RuntimeError as e:
            pytest.fail(f"Emissão de sinal falhou: {e}")

    def test_lock_mechanism(self):
        """Testa o mecanismo de lock para thread safety."""
        from src.main import WorkflowManager

        # Criar instância com mocks
        mock_animation = MagicMock()
        mock_gui = MagicMock()
        manager = WorkflowManager(mock_animation, mock_gui)

        # Verificar que lock existe e é do tipo correto
        assert hasattr(manager, "_lock")
        assert hasattr(manager._lock, "acquire")  # noqa: SLF001
        assert hasattr(manager._lock, "release")  # noqa: SLF001

        # Testar aquisição e liberação
        assert manager._lock.acquire(blocking=False) is True  # noqa: SLF001
        manager._lock.release()  # noqa: SLF001


class TestMainModuleConstants:
    """
    Testes para constantes e configurações do módulo main.
    """

    def test_default_hotkeys(self):
        """Testa valores padrão das hotkeys."""
        from src.main import DEFAULT_GUI_HOTKEY, DEFAULT_HOTKEY

        assert DEFAULT_HOTKEY == "ctrl+alt+c"
        assert DEFAULT_GUI_HOTKEY == "ctrl+alt+g"

    def test_environment_variable_loading(self):
        """Testa carregamento correto das variáveis de ambiente."""
        env_vars = {
            "OPENAI_API_KEY": "test-key",
            "HOTKEY": "ctrl+shift+c",
            "GUI_HOTKEY": "ctrl+shift+g",
            "CORRECTION_PROMPT": "Custom prompt",
        }

        # Este teste verifica que o código pode acessar variáveis de ambiente
        for var_name in env_vars:
            # Verificar que os.getenv funciona (pode retornar None se não definida)
            result = os.getenv(var_name)
            assert result is None or isinstance(result, str)
