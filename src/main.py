# Configuração para corrigir o erro de DPI Awareness do Qt
# Deve estar no topo, antes de qualquer importação de PySide6/Qt
import os
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"  # Desativa o scaling automático
os.environ["QT_LOGGING_RULES"] = "*.debug=false;qt.qpa.*=false"  # Suprime mensagens de log do Qt
# Alternativa que também podemos tentar:
# os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "PassThrough"

import sys
import time
import threading
from pathlib import Path
from functools import partial

# Adiciona o diretório raiz ao PYTHONPATH quando executado diretamente
if __name__ == "__main__":
    # Obter caminho absoluto para o diretório raiz (um nível acima do diretório src)
    ROOT_DIR = str(Path(__file__).parent.parent.absolute())
    # Adicionar ao PYTHONPATH se ainda não estiver
    if ROOT_DIR not in sys.path:
        sys.path.insert(0, ROOT_DIR)
        print(f"Adicionado {ROOT_DIR} ao PYTHONPATH")

# Agora que o PYTHONPATH está configurado, podemos importar o logger
from src.logger_config import logger

# Remover import keyboard
# import keyboard 
import pyperclip
from dotenv import load_dotenv
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, Signal, Slot, QMetaObject, Qt, QTimer

from src.capture import capture_selected_text
from src.correction import get_corrected_text
from src.paste import paste_text
from src.animation import MagicAnimationWindow
from src.correction import OpenAIError, ConnectionError, TimeoutError, AuthenticationError, RateLimitError, ServiceUnavailableError
# Adicionar import do novo KeyboardManager
from src.keyboard_listener import KeyboardManager
# Adicionar import da nova interface gráfica
from src.gui import TextaGuiWindow

# Assegurar que a pasta logs existe
os.makedirs('logs', exist_ok=True)

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
    print("\n🚨 ERRO DE CONFIGURAÇÃO 🚨")
    print("A chave de API da OpenAI não está configurada corretamente.")
    print("\nPara resolver:")
    print("1. Crie um arquivo .env na raiz do projeto")
    print("2. Adicione a seguinte linha:")
    print("   OPENAI_API_KEY=sua_chave_api_aqui")
    print("\nEncerrando o programa...")
    exit(1)
else:
    logger.info("Chave OPENAI_API_KEY encontrada, habilitando funcionalidades da API OpenAI.")

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

    def __init__(self, animation_window, gui_window=None):
        super().__init__()
        self.animation_window = animation_window
        self.gui_window = gui_window
        self._lock = threading.Lock() # Para evitar execuções simultâneas do workflow

        # Conecta os sinais aos slots da janela de animação
        # Assegura que os slots serão executados na thread da animation_window (GUI thread)
        self.request_start_animation.connect(self.animation_window.start_effect, Qt.QueuedConnection)
        self.request_close_animation.connect(self.animation_window.force_close, Qt.QueuedConnection)
        
        # Conecta os sinais aos slots da GUI (se existir)
        if self.gui_window:
            self.update_text_display.connect(self.gui_window.set_text_content, Qt.QueuedConnection)
            self.update_status.connect(self.gui_window.set_status, Qt.QueuedConnection)

    @Slot()
    def run_main_workflow(self):
        """Inicia o fluxo principal em uma thread separada para não bloquear o chamador."""
        # Verifica se já há um fluxo em andamento
        if not self._lock.acquire(blocking=False):
            logger.warning("Workflow já em andamento. Ignorando nova chamada.")
            return
        
        logger.info("Iniciando thread para main_workflow...")
        workflow_thread = threading.Thread(target=self._execute_workflow, daemon=True)
        workflow_thread.start()

    def _execute_workflow(self):
        """
        Executa o fluxo principal de captura, correção e colagem.
        Esta função roda em sua própria thread.
        """
        # Ajustando a mensagem de log para ser mais genérica
        logger.info("Workflow iniciado (thread do workflow). Iniciando fluxo...")
        
        selected_text = None # Inicializa
        corrected_text = None
        original_clipboard = "" # Inicializa
        error_occurred = False
        animation_started = False
        
        try:
            # 1. Inicia a Animação (antes da captura)
            logger.debug("Emitindo sinal request_start_animation...")
            self.request_start_animation.emit()
            animation_started = True
            # Pequena pausa para a janela aparecer
            time.sleep(0.1)
            
            # 2. Captura de Texto
            logger.info("Etapa 1: Captura de Texto")
            original_clipboard = pyperclip.paste() # Salva o conteúdo atual
            logger.debug("Conteúdo original do clipboard salvo.")
            
            try:
                selected_text = capture_selected_text()
            except Exception as e:
                logger.error(f"Erro durante a captura de texto: {e}")
                error_occurred = True
                error_message = "Erro ao capturar o texto selecionado."
                print(error_message + " Verifique se há texto selecionado e tente novamente.")
                if self.gui_window: self.update_status.emit(error_message, True)
                return # Sai da thread do workflow
            
            if not selected_text:
                logger.warning("Nenhum texto selecionado ou capturado.")
                error_occurred = True
                error_message = "Nenhum texto foi detectado."
                print(error_message + " Certifique-se de que o texto está selecionado...")
                if self.gui_window: self.update_status.emit(error_message, True)
                return # Sai da thread do workflow

            logger.info(f"Texto capturado: '{selected_text[:70]}...'")
            
            # Atualiza a GUI com o texto original capturado - usando sinal
            if self.gui_window:
                self.update_text_display.emit(selected_text, "")
            
            # 3. Correção (Bloqueante nesta thread)
            logger.info("Etapa 2: Correção do Texto (Chamando Agente OpenAI)")
            try:
                corrected_text = get_corrected_text(selected_text, api_key=OPENAI_API_KEY)
                if not corrected_text:
                     raise ValueError("Falha ao obter texto corrigido da LLM (retorno vazio).")
                logger.info(f"Texto corrigido: '{corrected_text[:70]}...'")
                logger.info("Correção concluída com sucesso.")
                
                # Atualiza a GUI com o texto corrigido - usando sinal
                if self.gui_window:
                    self.update_text_display.emit(selected_text, corrected_text)
                
            except (ConnectionError, TimeoutError, AuthenticationError, RateLimitError, ServiceUnavailableError, OpenAIError, ValueError) as e:
                logger.error(f"Erro durante a correção: {e}")
                error_occurred = True
                # Definir mensagem de erro específica
                if isinstance(e, ConnectionError): error_message = "Erro: Falha na conexão com OpenAI."
                elif isinstance(e, TimeoutError): error_message = "Erro: Timeout na conexão OpenAI."
                elif isinstance(e, AuthenticationError): error_message = "Erro: Chave API OpenAI inválida."
                elif isinstance(e, RateLimitError): error_message = "Erro: Limite de uso OpenAI excedido."
                elif isinstance(e, ServiceUnavailableError): error_message = "Erro: Serviço OpenAI indisponível."
                elif isinstance(e, ValueError): error_message = "Erro: Falha ao obter correção da IA."
                else: error_message = "Erro na API OpenAI."
                print(error_message)
                if self.gui_window: self.update_status.emit(error_message, True)
                return # Sai da thread do workflow
            except Exception as e:
                 logger.error(f"Erro inesperado durante a correção: {e}")
                 error_occurred = True
                 error_message = "Erro inesperado na correção."
                 print(error_message)
                 if self.gui_window: self.update_status.emit(error_message, True)
                 return # Sai da thread do workflow

            # Se chegamos aqui, a correção foi bem-sucedida
            
            # 4. Colagem (Antes de fechar a animação)
            logger.info("Etapa 3: Colagem do Texto Corrigido")
            try:
                paste_text(corrected_text)
                logger.info("Texto corrigido colado com sucesso.")
            except Exception as e:
                logger.error(f"Erro durante a colagem do texto: {e}")
                error_occurred = True
                error_message = "Erro ao colar o texto."
                print(error_message + " O texto foi corrigido mas não pôde ser colado.")
                if self.gui_window: self.update_status.emit(error_message, True)
                # Não retornamos aqui, pois ainda precisamos fechar a animação e restaurar o clipboard

        except Exception as e:
            logger.error(f"Erro inesperado no workflow: {e}")
            error_occurred = True
            error_message = "Erro inesperado no processamento."
            print(error_message)
            if self.gui_window: self.update_status.emit(error_message, True)
        finally:
            # Garante que a animação feche, caso ainda não tenha sido fechada
            if animation_started:
                logger.debug("Assegurando fechamento da animação no finally...")
                self.request_close_animation.emit()
                # Pequena pausa para garantir que o sinal de fechamento seja processado
                time.sleep(0.1)
            
            # Restauração (sempre tentar restaurar se algo foi capturado)
            if original_clipboard: # Verifica se original_clipboard foi definido
                logger.info("Etapa 4: Restauração do Clipboard Original")
                self.restore_clipboard(original_clipboard)
            
            logger.info(f"Fim do fluxo (Workflow Thread) - Sucesso: {not error_occurred}")
            self.workflow_complete.emit(not error_occurred)
            self._lock.release() # Libera o lock para permitir próxima execução
            
    def restore_clipboard(self, original_content):
        """Restaura o conteúdo original da área de transferência."""
        time.sleep(0.15)
        try:
            pyperclip.copy(original_content)
            logger.debug("Conteúdo original do clipboard restaurado.")
        except Exception as e:
            logger.error(f"Erro ao restaurar clipboard: {e}")
            
    @Slot()
    def toggle_gui(self):
        """Alterna a visibilidade da janela da GUI."""
        if self.gui_window:
            logger.info("Alternando visibilidade da janela da GUI.")
            self.gui_window.toggle_visibility()
        else:
            logger.warning("Tentativa de alternar GUI, mas nenhuma janela GUI foi configurada.")

if __name__ == "__main__":
    print("Iniciando Texta AI...")
    logger.info("Iniciando Texta AI...")

    # 1. Inicializa QApplication na thread principal
    app = QApplication(sys.argv)

    # 2. Cria a janela de animação (associada à thread principal)
    #    Mantê-la viva durante toda a execução da aplicação
    animation_win = MagicAnimationWindow()
    # animation_win.show() # Não mostrar ainda, será mostrado pelo start_effect
    
    # 2.1 Cria a janela da GUI com botão
    logger.info("Criando a janela da GUI...")
    gui_win = TextaGuiWindow()
    
    # Teste de visibilidade - mostra a janela e depois esconde
    # para verificar se a janela pode ser exibida corretamente
    logger.info("Testando visibilidade da GUI...")
    gui_win.show()
    app.processEvents() # Processa eventos pendentes
    QTimer.singleShot(500, gui_win.hide) # Esconde após 500ms
    
    # 3. Cria o gerenciador de workflow
    manager = WorkflowManager(animation_win, gui_win)
    
    # 3.1 Conecta o botão da GUI ao workflow
    gui_win.button_clicked.connect(manager.run_main_workflow)
    
    # 3.2 Conecta o sinal de conclusão do workflow ao reset da GUI
    manager.workflow_complete.connect(gui_win.reset_state, Qt.QueuedConnection)

    # 4. Inicia o novo KeyboardManager (baseado em pynput)
    keyboard_manager = KeyboardManager()
    
    # 4.1 Registra o hotkey para o workflow principal (Ctrl+Alt+C)
    if not keyboard_manager.add_hotkey(HOTKEY, manager.run_main_workflow):
        logger.error(f"Falha ao registrar a hotkey global '{HOTKEY}'. Verifique as permissões ou conflitos.")
        print(f"\n!!! ERRO CRÍTICO !!!")
        print(f"Não foi possível registrar a hotkey global '{HOTKEY}'.")
        print("Possíveis causas:")
        print("- Outro aplicativo já está usando esta combinação de teclas.")
        print("- O programa não tem as permissões necessárias (tente executar como administrador/sudo, se aplicável e seguro).")
        print("Saindo do programa...")
        # Garante que a GUI saia corretamente se já foi iniciada
        app.quit()
        exit(1)
    
    # 4.2 Registra o hotkey para alternar a janela da GUI (Ctrl+Alt+G)
    if not keyboard_manager.add_hotkey(GUI_HOTKEY, manager.toggle_gui):
        logger.error(f"Falha ao registrar a hotkey da GUI '{GUI_HOTKEY}'. Continuando sem esta funcionalidade.")
        print(f"Atenção: Não foi possível registrar a hotkey da GUI '{GUI_HOTKEY}'.")
        print("A correção via hotkey principal ainda funcionará normalmente.")
    else:
        logger.info(f"Hotkey da GUI '{GUI_HOTKEY}' registrada com sucesso.")
    
    # 4.3 Inicia o listener em modo não-bloqueante
    keyboard_manager.start(block=False)

    # 5. Mensagens de inicialização para o usuário
    print(f"Serviço iniciado. Pressione {HOTKEY} para corrigir texto selecionado diretamente.")
    print(f"Pressione {GUI_HOTKEY} para abrir a interface gráfica com botão.")
    print("(Pressione Ctrl+C no terminal para encerrar)")
    logger.info(f"Serviço iniciado com GlobalHotKeys. Hotkeys registrados: {HOTKEY}, {GUI_HOTKEY}")

    # 6. Executa o loop de eventos do Qt na thread principal
    exit_code = app.exec()

    # 7. Cleanup ao sair do loop de eventos
    logger.info("Loop de eventos Qt encerrado. Iniciando cleanup...")
    
    # Para o KeyboardManager
    logger.info("Parando KeyboardManager...")
    keyboard_manager.stop()
    logger.info("KeyboardManager parado.")
    
    logger.info("Encerrando o serviço Texta AI...")
    print("Encerrando Texta AI...")
    sys.exit(exit_code) 