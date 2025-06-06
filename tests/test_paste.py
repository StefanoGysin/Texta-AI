from src.paste import paste_text


def test_paste_text_success(mocker):
    """Testa colagem bem-sucedida de texto."""
    # Mock das dependências
    mock_pyperclip_copy = mocker.patch("pyperclip.copy")
    mock_pyautogui_hotkey = mocker.patch("pyautogui.hotkey")
    mock_time_sleep = mocker.patch("time.sleep")

    # Texto a ser colado
    test_text = "Texto para colar"

    # Executar a função
    result = paste_text(test_text)

    # Verificações
    assert result is True  # Deve retornar True no sucesso
    mock_pyperclip_copy.assert_called_once_with(test_text)
    mock_pyautogui_hotkey.assert_called_once_with("ctrl", "v")
    assert (
        mock_time_sleep.call_count == 2
    )  # Uma chamada para delay antes de colar e outra depois

    # Removido verificações de keyboard que não é mais usado


def test_paste_text_empty_text(mocker):
    """Testa o comportamento quando o texto a ser colado é vazio ou None."""
    # Mock das dependências
    mock_pyperclip_copy = mocker.patch("pyperclip.copy")
    mock_pyautogui_hotkey = mocker.patch("pyautogui.hotkey")
    mock_time_sleep = mocker.patch("time.sleep")

    # Caso 1: texto vazio
    result1 = paste_text("")

    # Caso 2: texto None
    result2 = paste_text(None)

    # Verificações
    assert result1 is None  # Deve retornar None para texto vazio
    assert result2 is None  # Deve retornar None para texto None
    mock_pyperclip_copy.assert_not_called()
    mock_pyautogui_hotkey.assert_not_called()
    mock_time_sleep.assert_not_called()


def test_paste_text_exception_handling(mocker):
    """Testa o tratamento de exceções durante a colagem."""
    # Mock das dependências com exceção no pyperclip
    mock_pyperclip_copy = mocker.patch(
        "pyperclip.copy", side_effect=OSError("Erro simulado no clipboard")
    )
    mock_pyautogui_hotkey = mocker.patch("pyautogui.hotkey")
    mock_time_sleep = mocker.patch("time.sleep")

    # Executar a função - deve capturar a exceção e retornar False
    result = paste_text("Texto para colar")

    # Verificações
    assert result is False  # Deve retornar False quando há exceção
    mock_pyperclip_copy.assert_called_once_with("Texto para colar")
    mock_pyautogui_hotkey.assert_not_called()  # Não deve ter sido chamado após a exceção
    mock_time_sleep.assert_not_called()  # Não deve ter sido chamado após a exceção


def test_paste_text_custom_delay(mocker):
    """Testa a função com delay personalizado."""
    # Mock das dependências
    mock_pyperclip_copy = mocker.patch("pyperclip.copy")
    mock_pyautogui_hotkey = mocker.patch("pyautogui.hotkey")
    mock_time_sleep = mocker.patch("time.sleep")

    # Parâmetros personalizados
    test_text = "Texto para colar"
    custom_delay = 1.0

    # Executar a função
    result = paste_text(test_text, delay=custom_delay)

    # Verificações
    assert result is True  # Deve retornar True no sucesso
    mock_pyperclip_copy.assert_called_once_with(test_text)
    mock_pyautogui_hotkey.assert_called_once_with("ctrl", "v")

    # Verificar que o delay personalizado foi usado
    assert mock_time_sleep.call_count == 2
    mock_time_sleep.assert_any_call(custom_delay)  # Delay antes da colagem
    mock_time_sleep.assert_any_call(0.1)  # Delay fixo após a colagem


# Todos os casos de teste do plano foram implementados:
# ✓ Caso de sucesso: Texto é colocado no clipboard e Ctrl+V simulado
# ✓ Caso de entrada inválida: O que acontece com texto vazio ou None
# ✓ Caso de falha: Exceção é levantada por pyperclip ou pyautogui
# + Adicional: Teste com parâmetros personalizados
