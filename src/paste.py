import pyperclip
# Remover importação do keyboard que não é mais usado
# import keyboard
import time
import platform
import pyautogui
# Usar a configuração de logger centralizada
from .logger_config import logger

def paste_text(text_to_paste: str, paste_hotkey: str = 'ctrl+v', delay: float = 0.3):
    """Coloca o texto na área de transferência e simula a colagem.

    Args:
        text_to_paste (str): O texto a ser colado.
        paste_hotkey (str): A combinação de teclas para simular a colagem (padrão: 'ctrl+v').
        delay (float): Pequeno atraso em segundos para garantir que a área de 
                       transferência foi atualizada antes de colar (padrão: 0.3).
    """
    if not text_to_paste:
        logger.warning("Nenhum texto para colar.")
        return

    try:
        logger.info("Preparando para colar texto corrigido...")
        
        # Coloca o novo texto na área de transferência
        pyperclip.copy(text_to_paste)

        # Pequena pausa para garantir que o clipboard foi atualizado
        time.sleep(delay)

        # Usando pyautogui para maior confiabilidade
        pyautogui.hotkey('ctrl', 'v')
        
        # Código comentado: método alternativo usando keyboard (desativado e removido)
        # Este método alternativo foi removido pois migramos para pynput

        logger.info("Comando de colar enviado com sucesso.")
        # Pequena pausa para garantir que a colagem foi processada
        time.sleep(0.1)  # Mantemos 0.1s, é crítico para aplicações processarem a colagem

        return True
    except Exception as e:
        logger.error(f"Erro ao colar texto: {e}")
        return False

# --- Bloco de Teste Local (opcional) ---
# if __name__ == '__main__':
#     test_text = "Este é um texto de teste para colar."
#     logger.info("Preparando para colar o seguinte texto em 5 segundos:")
#     logger.info(test_text)
#     logger.info("Por favor, coloque o cursor onde deseja colar.")
#     time.sleep(5) 
#     paste_text(test_text)
#     logger.info("Comando de colar enviado.") 