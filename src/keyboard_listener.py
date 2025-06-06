from __future__ import annotations

from typing import Callable

from pynput.keyboard import GlobalHotKeys

# Usar a configuração de logger centralizada
from .logger_config import logger


# Classe principal para gerenciar atalhos de teclado globais
class KeyboardManager:
    """Gerenciador de listeners de teclado usando pynput.keyboard.GlobalHotKeys para suporte global e multi-plataforma de hotkeys.

    Este gerenciador permite registrar e desregistrar hotkeys dinamicamente,
    mantendo um mapeamento interno e recriando o listener conforme necessário.
    """

    def __init__(self) -> None:
        self.hotkey_mappings: dict[str, Callable] = {}  # Mapeamento hotkey -> callback
        self.listener: GlobalHotKeys | None = None
        self.running = False

    def add_hotkey(self, hotkey: str, callback: Callable) -> bool:
        """Registra uma nova hotkey e seu callback associado.

        Args:
            hotkey (str): Combinação de teclas no formato "ctrl+alt+c" (lowercase).
            callback (Callable): Função a ser chamada quando a hotkey for pressionada.

        Returns:
            bool: True se registrado com sucesso, False caso contrário.
        """
        try:
            # Converte a string de hotkey para o formato que o pynput.keyboard.GlobalHotKeys espera
            # Ex: "ctrl+alt+c" -> "<ctrl>+<alt>+c"
            formatted_hotkey = self._format_hotkey_string(hotkey)

            # Registra a hotkey
            self.hotkey_mappings[formatted_hotkey] = callback

            # Se o listener já estiver ativo, recriá-lo com a nova hotkey
            if self.running:
                self.stop()
                self.start()

            logger.info(
                f"Hotkey '{hotkey}' registrada com sucesso para o callback {callback.__name__}."
            )
        except (ValueError, KeyError, AttributeError) as e:
            logger.error(f"Erro ao registrar hotkey '{hotkey}': {e}")
            return False
        else:
            return True

    def _format_hotkey_string(self, hotkey: str) -> str:
        """Converte uma string de hotkey no formato "ctrl+alt+c" para o formato "<ctrl>+<alt>+c".

        Este método é usado internamente para converter strings de hotkey legíveis
        para o formato que é esperado pela classe GlobalHotKeys.
        """
        parts = hotkey.lower().split("+")
        formatted_parts = []

        # Modificadores conhecidos que precisam ser formatados com <>
        modifiers = {"ctrl", "alt", "shift", "cmd", "command", "win", "windows"}

        for part in parts:
            if part in modifiers:
                formatted_parts.append(f"<{part}>")
            else:
                # Teclas não-modificadoras são mantidas como estão
                formatted_parts.append(part)

        return "+".join(formatted_parts)

    def remove_hotkey(self, hotkey: str) -> bool:
        """Remove uma hotkey registrada."""
        try:
            formatted_hotkey = self._format_hotkey_string(hotkey)

            if formatted_hotkey in self.hotkey_mappings:
                del self.hotkey_mappings[formatted_hotkey]
                logger.info(f"Hotkey '{hotkey}' removida.")

                # Recria o listener para refletir a mudança
                if self.running:
                    self.stop()
                    self.start()
            else:
                logger.warning(f"Hotkey '{hotkey}' não encontrada para remoção.")
                return False

        except (ValueError, KeyError, AttributeError) as e:
            logger.error(f"Erro ao remover hotkey '{hotkey}': {e}")
            return False
        else:
            return True

    def start(self, *, block: bool = False) -> None:
        """Inicia o listener de teclado.

        Args:
            block (bool): Se True, bloqueia a thread atual (útil para scripts simples).
                          Se False (padrão), executa em background (útil para GUIs).
        """
        if self.running:
            logger.warning("Keyboard manager já está em execução.")
            return

        try:
            # Verifica se temos hotkeys registradas
            if not self.hotkey_mappings:
                logger.warning(
                    "Não há hotkeys registradas. O listener não será iniciado."
                )
                return

            # Cria o GlobalHotKeys com o dicionário de hotkeys
            self.listener = GlobalHotKeys(self.hotkey_mappings)

            self.running = True
            self.listener.start()
            logger.info(
                f"Iniciando keyboard manager com {len(self.hotkey_mappings)} hotkeys registradas."
            )

            if block:
                # Modo bloqueante
                logger.info("Aguardando em modo bloqueante...")
                self.listener.join()

        except (RuntimeError, OSError) as e:
            self.running = False
            logger.error(f"Erro crítico ao iniciar keyboard manager: {e}")
            # Opcionalmente, podemos relançar a exceção
            # raise e

    def stop(self) -> None:
        """Para o listener de teclado e libera recursos."""
        if not self.running:
            logger.info("Keyboard manager já estava parado.")
            return

        try:
            logger.info("Parando keyboard manager...")
            self.running = False

            # Para o listener se estiver rodando
            if self.listener:
                self.listener.stop()
                # Espera a thread do listener terminar
                self.listener.join()
                logger.debug("Thread do listener finalizada.")
                self.listener = None

            logger.info("Keyboard manager parado com sucesso.")
        except (RuntimeError, OSError) as e:
            logger.error(f"Erro ao parar keyboard manager: {e}")


# Exemplo de uso básico (para teste local se necessário)
if __name__ == "__main__":
    logger.info("Testando KeyboardManager...")

    def my_callback_1() -> None:
        pass

    def my_callback_2() -> None:
        pass

    manager = KeyboardManager()

    # Registra hotkeys
    manager.add_hotkey("ctrl+alt+c", my_callback_1)
    manager.add_hotkey("shift+a", my_callback_2)

    # Inicia em modo bloqueante para este teste simples
    try:
        manager.start(block=True)
    except KeyboardInterrupt:
        logger.info("Interrupção de teclado recebida.")
    finally:
        logger.info("Encerrando teste...")
        manager.stop()
        logger.info("Teste finalizado.")
