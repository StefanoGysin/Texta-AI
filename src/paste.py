from __future__ import annotations

import time

import pyautogui
import pyperclip

# Usar a configuração de logger centralizada
from .logger_config import logger


def paste_text(text_to_paste: str, delay: float = 0.3) -> bool | None:
    """Coloca o texto na área de transferência e simula a colagem.

    Args:
        text_to_paste (str): O texto a ser colado.
        delay (float): Pequeno atraso em segundos para garantir que a área de
                       transferência foi atualizada antes de colar (padrão: 0.3).

    Returns:
        bool | None: True se a colagem foi bem-sucedida, False se houve erro,
                     None se não há texto para colar.
    """
    if not text_to_paste:
        logger.warning("Nenhum texto para colar.")
        return None

    try:
        logger.info("Preparando para colar texto corrigido...")

        # Coloca o novo texto na área de transferência
        pyperclip.copy(text_to_paste)

        # Pequena pausa para garantir que o clipboard foi atualizado
        time.sleep(delay)

        # Usando pyautogui para maior confiabilidade
        pyautogui.hotkey("ctrl", "v")

        logger.info("Comando de colar enviado com sucesso.")
        # Pequena pausa para garantir que a colagem foi processada
        time.sleep(
            0.1
        )  # Mantemos 0.1s, é crítico para aplicações processarem a colagem

    except (pyautogui.FailSafeException, OSError, RuntimeError) as e:
        logger.error(f"Erro ao colar texto: {e}")
        return False
    else:
        return True
