from __future__ import annotations

import asyncio
import os

os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"  # Desativa o scaling automático
os.environ["QT_LOGGING_RULES"] = (
    "*.debug=false;qt.qpa.*=false"  # Suprime mensagens de log do Qt
)

from pathlib import Path
import signal
import sys
import threading
import time

# Adiciona o diretório raiz ao PYTHONPATH quando executado diretamente
if __name__ == "__main__":
    # Obter caminho absoluto para o diretório raiz (um nível acima do diretório src)
    ROOT_DIR = str(Path(__file__).parent.parent.absolute())
    # Adicionar ao PYTHONPATH se ainda não estiver
    if ROOT_DIR not in sys.path:
        sys.path.insert(0, ROOT_DIR)

# Agora que o PYTHONPATH está configurado, podemos importar o logger
from dotenv import load_dotenv
import pyperclip
from PySide6.QtCore import QObject, Qt, QTimer, Signal, Slot
from PySide6.QtWidgets import QApplication

from src.animation import MagicAnimationWindow
from src.capture import capture_selected_text
from src.correction import (
    AuthenticationError,
    OpenAIConnectionError,
    OpenAIError,
    OpenAITimeoutError,
    RateLimitError,
    ServiceUnavailableError,
    get_corrected_text,
)

# Adicionar import da nova interface gráfica
from src.gui import TextaGuiWindow

# Adicionar import do novo KeyboardManager
from src.keyboard_listener import KeyboardManager
from src.logger_config import logger
from src.paste import paste_text

# Assegurar que a pasta logs existe
Path("logs").mkdir(exist_ok=True)

# Carregar variáveis de ambiente do arquivo .env
logger.info("Carregando variáveis de ambiente...")
load_dotenv()
logger.info("Variáveis de ambiente carregadas.")

# Configurações carregadas do .env
DEFAULT_HOTKEY = "ctrl+alt+c"
DEFAULT_GUI_HOTKEY = "ctrl+alt+g"
HOTKEY = os.getenv("HOTKEY", DEFAULT_HOTKEY)
GUI_HOTKEY = os.getenv("GUI_HOTKEY", DEFAULT_GUI_HOTKEY)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Validação inicial da API Key
if not OPENAI_API_KEY:
    logger.error("Chave API da OpenAI não configurada no ambiente")
    logger.error("🚨 ERRO DE CONFIGURAÇÃO 🚨")
    logger.error("A chave de API da OpenAI não está configurada corretamente.")
    logger.error("Para resolver:")
    logger.error("1. Crie um arquivo .env na raiz do projeto")
    logger.error("2. Adicione a seguinte linha:")
    logger.error("   OPENAI_API_KEY=sua_chave_api_aqui")
    logger.error("Encerrando o programa...")
    sys.exit(1)
else:
    logger.info(
        "Chave OPENAI_API_KEY encontrada, habilitando funcionalidades da API OpenAI."
    )


# Classe para gerenciar a comunicação entre threads e a GUI
class WorkflowManager(QObject):
    # Sinais para invocar métodos da GUI a partir de outras threads
    request_start_animation = Signal()
    request_close_animation = Signal()
    # Sinal para indicar que o fluxo terminou (bool indica sucesso)
    workflow_complete = Signal(bool)
    # Sinal para atualizar os textos na GUI (original, corrigido)
    update_text_display = Signal(str, str)
    # Sinal para atualizar o status na GUI (mensagem, é_erro)
    update_status = Signal(str, bool)
    # Sinal para solicitar toggle da visibilidade da GUI
    toggle_gui_requested = Signal()

    def __init__(
        self,
        animation_window: MagicAnimationWindow,
        gui_window: TextaGuiWindow | None = None,
    ) -> None:
        super().__init__()
        self.animation_window = animation_window
        self.gui_window = gui_window
        self._lock = threading.Lock()  # Para evitar execuções simultâneas do workflow

        # Conecta os sinais aos slots da janela de animação
        # Assegura que os slots serão executados na thread da animation_window (GUI thread)
        self.request_start_animation.connect(
            self.animation_window.start_effect, Qt.QueuedConnection
        )
        self.request_close_animation.connect(
            self.animation_window.force_close, Qt.QueuedConnection
        )

        # Conecta os sinais aos slots da GUI (se existir)
        if self.gui_window:
            self.update_text_display.connect(
                self.gui_window.set_text_content, Qt.QueuedConnection
            )
            self.update_status.connect(self.gui_window.set_status, Qt.QueuedConnection)

    @Slot()
    def run_main_workflow(self) -> None:
        """Inicia o fluxo principal em uma thread separada para não bloquear o chamador."""
        # Verifica se já há um fluxo em andamento
        if not self._lock.acquire(blocking=False):
            logger.warning("Workflow já em andamento. Ignorando nova chamada.")
            return

        logger.info("Iniciando thread para main_workflow...")
        workflow_thread = threading.Thread(target=self._execute_workflow, daemon=True)
        workflow_thread.start()

    def _execute_workflow(self) -> None:
        """Wrapper síncrono para executar o workflow assíncrono."""
        asyncio.run(self._execute_workflow_async())

    async def _execute_workflow_async(self) -> None:
        """Executa o fluxo principal de captura, correção e colagem.

        Esta função roda em sua própria thread.
        """
        logger.info("Workflow iniciado (thread do workflow). Iniciando fluxo...")

        state = self._initialize_workflow_state()

        try:
            self._start_animation(state)
            selected_text = self._capture_text(state)
            if not selected_text:
                return

            corrected_text = await self._correct_text_async(selected_text, state)
            if not corrected_text:
                return

            self._paste_corrected_text(corrected_text, state)

        except (OSError, RuntimeError, ValueError) as e:
            self._handle_unexpected_error(e, state)
        finally:
            self._cleanup_workflow(state)

    def _initialize_workflow_state(self) -> dict:
        """Inicializa o estado do workflow."""
        return {
            "error_occurred": False,
            "animation_started": False,
            "original_clipboard": "",
        }

    def _start_animation(self, state: dict) -> None:
        """Inicia a animação visual."""
        logger.debug("Emitindo sinal request_start_animation...")
        self.request_start_animation.emit()
        state["animation_started"] = True
        time.sleep(0.1)  # Pequena pausa para a janela aparecer

    def _capture_text(self, state: dict) -> str | None:
        """Captura o texto selecionado."""
        logger.info("Etapa 1: Captura de Texto")
        state["original_clipboard"] = pyperclip.paste()
        logger.debug("Conteúdo original do clipboard salvo.")

        try:
            selected_text = capture_selected_text()
        except (OSError, RuntimeError, ValueError) as e:
            self._handle_capture_error(e, state)
            return None

        if not selected_text:
            self._handle_no_text_captured(state)
            return None

        logger.info("Texto capturado: '%s...'", selected_text[:70])

        # Atualiza a GUI com o texto original capturado
        if self.gui_window:
            self.update_text_display.emit(selected_text, "")

        return selected_text

    def _handle_capture_error(self, error: Exception, state: dict) -> None:
        """Trata erros durante a captura de texto."""
        logger.error("Erro durante a captura de texto: %s", error)
        state["error_occurred"] = True
        error_message = "Erro ao capturar o texto selecionado."
        logger.error(
            "%s Verifique se há texto selecionado e tente novamente.", error_message
        )
        if self.gui_window:
            self.update_status.emit(error_message, is_error=True)

    def _handle_no_text_captured(self, state: dict) -> None:
        """Trata caso onde nenhum texto foi capturado."""
        logger.warning("Nenhum texto selecionado ou capturado.")
        state["error_occurred"] = True
        error_message = "Nenhum texto foi detectado."
        logger.warning(
            "%s Certifique-se de que o texto está selecionado...", error_message
        )
        if self.gui_window:
            self.update_status.emit(error_message, is_error=True)

    async def _correct_text_async(self, selected_text: str, state: dict) -> str | None:
        """Executa a correção do texto via OpenAI."""
        logger.info("Etapa 2: Correção do Texto (Chamando Agente OpenAI)")

        try:
            corrected_text = await get_corrected_text(selected_text, api_key=OPENAI_API_KEY)
            if not corrected_text:
                self._raise_correction_error()

            logger.info("Texto corrigido: '%s...'", corrected_text[:70])
            logger.info("Correção concluída com sucesso.")

            # Atualiza a GUI com o texto corrigido
            if self.gui_window:
                self.update_text_display.emit(selected_text, corrected_text)

        except (
            OpenAIConnectionError,
            OpenAITimeoutError,
            AuthenticationError,
            RateLimitError,
            ServiceUnavailableError,
            OpenAIError,
            ValueError,
        ) as e:
            self._handle_correction_api_error(e, state)
            return None
        except (OSError, RuntimeError) as e:
            self._handle_correction_unexpected_error(e, state)
            return None
        else:
            return corrected_text

    def _raise_correction_error(self) -> None:
        """Levanta erro quando a correção falha."""
        msg = "Falha ao obter texto corrigido da LLM (retorno vazio)."
        raise ValueError(msg)

    def _handle_correction_api_error(self, error: Exception, state: dict) -> None:
        """Trata erros específicos da API OpenAI."""
        logger.error("Erro durante a correção: %s", error)
        state["error_occurred"] = True

        # Mapear tipos de erro para mensagens específicas
        error_messages = {
            OpenAIConnectionError: "Erro: Falha na conexão com OpenAI.",
            OpenAITimeoutError: "Erro: Timeout na conexão OpenAI.",
            AuthenticationError: "Erro: Chave API OpenAI inválida.",
            RateLimitError: "Erro: Limite de uso OpenAI excedido.",
            ServiceUnavailableError: "Erro: Serviço OpenAI indisponível.",
            ValueError: "Erro: Falha ao obter correção da IA.",
        }

        error_message = error_messages.get(type(error), "Erro na API OpenAI.")
        logger.error(error_message)

        if self.gui_window:
            self.update_status.emit(error_message, is_error=True)

    def _handle_correction_unexpected_error(
        self, error: Exception, state: dict
    ) -> None:
        """Trata erros inesperados durante a correção."""
        logger.error("Erro inesperado durante a correção: %s", error)
        state["error_occurred"] = True
        error_message = "Erro inesperado na correção."
        logger.error(error_message)
        if self.gui_window:
            self.update_status.emit(error_message, is_error=True)

    def _paste_corrected_text(self, corrected_text: str, state: dict) -> None:
        """Cola o texto corrigido."""
        logger.info("Etapa 3: Colagem do Texto Corrigido")
        try:
            paste_text(corrected_text)
            logger.info("Texto corrigido colado com sucesso.")
        except (OSError, RuntimeError) as e:
            self._handle_paste_error(e, state)

    def _handle_paste_error(self, error: Exception, state: dict) -> None:
        """Trata erros durante a colagem."""
        logger.error("Erro durante a colagem do texto: %s", error)
        state["error_occurred"] = True
        error_message = "Erro ao colar o texto."
        logger.error("%s O texto foi corrigido mas não pôde ser colado.", error_message)
        if self.gui_window:
            self.update_status.emit(error_message, is_error=True)

    def _handle_unexpected_error(self, error: Exception, state: dict) -> None:
        """Trata erros inesperados no workflow principal."""
        logger.error("Erro inesperado no workflow: %s", error)
        state["error_occurred"] = True
        error_message = "Erro inesperado no processamento."
        logger.error(error_message)
        if self.gui_window:
            self.update_status.emit(error_message, is_error=True)

    def _cleanup_workflow(self, state: dict) -> None:
        """Executa a limpeza final do workflow."""
        # Garante que a animação feche
        if state["animation_started"]:
            logger.debug("Assegurando fechamento da animação no finally...")
            self.request_close_animation.emit()
            time.sleep(0.1)  # Pequena pausa para garantir que o sinal seja processado

        # Restauração do clipboard
        if state["original_clipboard"]:
            logger.info("Etapa 4: Restauração do Clipboard Original")
            self.restore_clipboard(state["original_clipboard"])

        logger.info(
            "Fim do fluxo (Workflow Thread) - Sucesso: %s", not state["error_occurred"]
        )
        self.workflow_complete.emit(not state["error_occurred"])
        self._lock.release()  # Libera o lock para permitir próxima execução

    def restore_clipboard(self, original_content: str) -> None:
        """Restaura o conteúdo original da área de transferência."""
        time.sleep(0.15)
        try:
            pyperclip.copy(original_content)
            logger.debug("Conteúdo original do clipboard restaurado.")
        except (OSError, RuntimeError) as e:
            logger.error("Erro ao restaurar clipboard: %s", e)

    @Slot()
    def toggle_gui(self) -> None:
        """Alterna a visibilidade da janela da GUI."""
        if self.gui_window:
            logger.info("Alternando visibilidade da janela da GUI.")
            self.toggle_gui_requested.emit()
        else:
            logger.warning(
                "Tentativa de alternar GUI, mas nenhuma janela GUI foi configurada."
            )


if __name__ == "__main__":
    logger.info("Iniciando Texta AI...")

    # 1. Inicializa QApplication na thread principal
    app = QApplication(sys.argv)

    # 2. Cria a janela de animação (associada à thread principal)
    #    Mantê-la viva durante toda a execução da aplicação
    animation_win = MagicAnimationWindow()

    # 2.1 Cria a janela da GUI com botão
    logger.info("Criando a janela da GUI...")
    gui_win = TextaGuiWindow()

    # Teste de visibilidade - mostra a janela e depois esconde
    # para verificar se a janela pode ser exibida corretamente
    logger.info("Testando visibilidade da GUI...")
    gui_win.show()
    app.processEvents()  # Processa eventos pendentes
    QTimer.singleShot(500, gui_win.hide)  # Esconde após 500ms

    # 3. Cria o gerenciador de workflow
    manager = WorkflowManager(animation_win, gui_win)

    # 3.1 Conecta o botão da GUI ao workflow
    gui_win.button_clicked.connect(manager.run_main_workflow)

    # 3.2 Conecta o sinal de conclusão do workflow ao reset da GUI
    manager.workflow_complete.connect(gui_win.reset_state, Qt.QueuedConnection)

    # 3.3 Conecta o sinal de toggle_gui diretamente na GUI usando QueuedConnection
    # para garantir que a chamada seja feita na thread correta da GUI
    manager.toggle_gui_requested.connect(gui_win.toggle_visibility, Qt.QueuedConnection)

    # 4. Inicia o novo KeyboardManager (baseado em pynput)
    keyboard_manager = KeyboardManager()

    # 4.1 Registra o hotkey para o workflow principal (Ctrl+Alt+C)
    if not keyboard_manager.add_hotkey(HOTKEY, manager.run_main_workflow):
        logger.error(
            "Falha ao registrar a hotkey global '%s'. Verifique as permissões ou conflitos.",
            HOTKEY,
        )
        logger.critical("!!! ERRO CRÍTICO !!!")
        logger.critical("Não foi possível registrar a hotkey global '%s'.", HOTKEY)
        logger.critical("Possíveis causas:")
        logger.critical("- Outro aplicativo já está usando esta combinação de teclas.")
        logger.critical(
            "- O programa não tem as permissões necessárias (tente executar como administrador/sudo, se aplicável e seguro)."
        )
        logger.critical("Saindo do programa...")
        # Garante que a GUI saia corretamente se já foi iniciada
        app.quit()
        sys.exit(1)

    # 4.2 Registra o hotkey para alternar a janela da GUI (Ctrl+Alt+G)
    if not keyboard_manager.add_hotkey(GUI_HOTKEY, manager.toggle_gui):
        logger.error(
            "Falha ao registrar a hotkey da GUI '%s'. Continuando sem esta funcionalidade.",
            GUI_HOTKEY,
        )
        logger.warning(
            "Atenção: Não foi possível registrar a hotkey da GUI '%s'.", GUI_HOTKEY
        )
        logger.warning("A correção via hotkey principal ainda funcionará normalmente.")
    else:
        logger.info("Hotkey da GUI '%s' registrada com sucesso.", GUI_HOTKEY)

    # 4.3 Inicia o listener em modo não-bloqueante
    keyboard_manager.start(block=False)

    # 5. Mensagens de inicialização para o usuário
    logger.info(
        "Serviço iniciado. Pressione %s para corrigir texto selecionado diretamente.",
        HOTKEY,
    )
    logger.info("Pressione %s para abrir a interface gráfica com botão.", GUI_HOTKEY)
    logger.info("(Pressione Ctrl+C no terminal para encerrar)")
    logger.info(
        "Serviço iniciado com GlobalHotKeys. Hotkeys registrados: %s, %s",
        HOTKEY,
        GUI_HOTKEY,
    )

    # 6. Executa o loop de eventos do Qt na thread principal
    #    E configura o tratamento de sinal para Ctrl+C
    #    Referência: https://doc.qt.io/qt-6/qcoreapplication.html#exec
    
    # Define o manipulador de sinal para chamar app.quit() ao receber SIGINT
    def sigint_handler(*_):
        logger.info("SIGINT recebido. Encerrando a aplicação...")
        QApplication.instance().quit()

    signal.signal(signal.SIGINT, sigint_handler)

    # Usa um QTimer para permitir que o interpretador Python processe sinais.
    # Sem isso, o loop de eventos do Qt pode bloquear o processamento de SIGINT.
    timer = QTimer()
    timer.start(500)  # Executa a cada 500ms
    timer.timeout.connect(lambda: None)  # Apenas para manter o loop de eventos ativo

    try:
        logger.info("Iniciando o loop de eventos principal da aplicação...")
        exit_code = app.exec()
        logger.info(f"Loop de eventos encerrado com código: {exit_code}")

    finally:
        # 7. Cleanup ao sair do loop de eventos
        logger.info("Iniciando cleanup final...")

        # Para o KeyboardManager
        if 'keyboard_manager' in locals() and keyboard_manager.running:
            logger.info("Parando KeyboardManager...")
            keyboard_manager.stop()
            logger.info("KeyboardManager parado.")

        logger.info("Encerrando o serviço Texta AI.")
        # sys.exit(exit_code) # O exit_code pode não estar definido se houve exceção
        sys.exit(0) # Sai com código de sucesso

