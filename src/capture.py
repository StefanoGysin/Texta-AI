from __future__ import annotations

import platform
import time

import pyautogui
import pyperclip

# Usar a configuração de logger centralizada
from .logger_config import logger


def capture_selected_text(
    copy_hotkey: str = "ctrl+c", delay: float = 0.3
) -> str | None:
    """Simula a cópia do texto selecionado e lê da área de transferência.

    Args:
        copy_hotkey (str): A combinação de teclas para simular a cópia (padrão: 'ctrl+c').
        delay (float): Pequeno atraso em segundos para permitir que a área de transferência
                       seja atualizada (padrão: 0.3).

    Returns:
        str | None: O texto lido da área de transferência, ou None se ocorrer um erro ou
                    a área de transferência estiver vazia.
    """
    try:
        logger.info("Tentando capturar texto selecionado...")

        # Guarda o conteúdo atual para restaurar depois
        original_clipboard_content = pyperclip.paste()

        # Limpa a área de transferência para garantir que estamos pegando o novo texto
        pyperclip.copy("")

        # Usando pyautogui para maior confiabilidade
        # Simula Ctrl+C
        pyautogui.hotkey("ctrl", "c")

        # Tempo de espera para dar tempo ao sistema operacional
        time.sleep(delay)

        # Tenta ler o clipboard
        selected_text = pyperclip.paste()

        # Se falhou, tenta mais duas vezes com maior tempo de espera
        if not selected_text:
            logger.debug("Primeira tentativa falhou, tentando novamente...")
            time.sleep(0.3)
            # Segunda tentativa com pyautogui
            pyautogui.hotkey("ctrl", "c")
            time.sleep(0.3)
            selected_text = pyperclip.paste()

            if not selected_text:
                logger.debug("Segunda tentativa falhou, tentando método alternativo...")
                # Terceira tentativa, também com pyautogui mas com método diferente
                if platform.system() == "Windows":
                    # Usando keyDown/Up em vez de hotkey para maior controle
                    pyautogui.keyDown("ctrl")
                    time.sleep(
                        0.05
                    )  # Este delay pequeno é importante, mantemos como está
                    pyautogui.press("c")
                    pyautogui.keyUp("ctrl")
                else:
                    # Separar o hotkey em teclas individuais para o pyautogui
                    keys = copy_hotkey.split("+")
                    pyautogui.hotkey(*keys)
                time.sleep(0.3)
                selected_text = pyperclip.paste()

        if selected_text:
            logger.info(
                f"Texto capturado com sucesso! ({len(selected_text)} caracteres)"
            )
            return selected_text
        logger.warning("Área de transferência vazia após todas as tentativas.")
        logger.warning("Dicas para resolver:")
        logger.warning("1. Certifique-se de selecionar o texto antes de usar a hotkey.")
        logger.warning(
            "2. Algumas aplicações podem restringir a funcionalidade de Ctrl+C."
        )
        logger.warning("3. Tente executar o script sem privilégios administrativos.")
        return None  # noqa: TRY300

    except (pyperclip.PyperclipException, pyautogui.FailSafeException) as e:
        logger.error(f"Erro ao capturar texto da área de transferência: {e}")
        try:
            pyperclip.copy(original_clipboard_content)
        except NameError:
            pass
        except (pyperclip.PyperclipException, OSError) as restore_e:
            logger.error(f"Erro ao restaurar área de transferência: {restore_e}")
        return None
    except (OSError, ValueError, TypeError, AttributeError, NameError) as e:
        logger.error(f"Erro inesperado ao capturar texto: {e}")
        try:
            pyperclip.copy(original_clipboard_content)
        except NameError:
            pass
        except (pyperclip.PyperclipException, OSError) as restore_e:
            logger.error(f"Erro ao restaurar área de transferência: {restore_e}")
        return None
