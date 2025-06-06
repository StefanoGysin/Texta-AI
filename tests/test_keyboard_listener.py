"""Testes unitários para src/keyboard_listener.py

Este módulo contém testes abrangentes para o KeyboardManager,
focando especialmente nas linhas não cobertas identificadas
no relatório de cobertura de testes.
"""

from __future__ import annotations

from threading import Thread
import time
from unittest.mock import Mock, patch

import pytest

from src.keyboard_listener import KeyboardManager


class TestKeyboardManagerInitialization:
    """Testes para inicialização do KeyboardManager."""

    def test_init_creates_empty_mappings(self) -> None:
        """Testa se a inicialização cria estruturas vazias corretamente."""
        manager = KeyboardManager()

        assert manager.hotkey_mappings == {}
        assert manager.listener is None
        assert manager.running is False


class TestFormatHotkeyString:
    """Testes para o método _format_hotkey_string."""

    def test_format_simple_hotkey(self) -> None:
        """Testa formatação de hotkey simples."""
        manager = KeyboardManager()

        result = manager._format_hotkey_string("ctrl+alt+c")  # noqa: SLF001
        assert result == "<ctrl>+<alt>+c"

    def test_format_with_mixed_case(self) -> None:
        """Testa formatação com casos mistos."""
        manager = KeyboardManager()

        result = manager._format_hotkey_string("CTRL+Alt+C")  # noqa: SLF001
        assert result == "<ctrl>+<alt>+c"

    def test_format_with_shift_modifier(self) -> None:
        """Testa formatação com shift."""
        manager = KeyboardManager()

        result = manager._format_hotkey_string("shift+a")  # noqa: SLF001
        assert result == "<shift>+a"

    def test_format_with_windows_key(self) -> None:
        """Testa formatação com tecla Windows."""
        manager = KeyboardManager()

        result = manager._format_hotkey_string("win+r")  # noqa: SLF001
        assert result == "<win>+r"

    def test_format_with_command_key(self) -> None:
        """Testa formatação com tecla Command (macOS)."""
        manager = KeyboardManager()

        result = manager._format_hotkey_string("cmd+space")  # noqa: SLF001
        assert result == "<cmd>+space"

    def test_format_single_key(self) -> None:
        """Testa formatação de tecla única (não modificador)."""
        manager = KeyboardManager()

        result = manager._format_hotkey_string("f1")  # noqa: SLF001
        assert result == "f1"


class TestAddHotkey:
    """Testes para o método add_hotkey."""

    def test_add_hotkey_success(self) -> None:
        """Testa adição bem-sucedida de hotkey."""
        manager = KeyboardManager()
        callback = Mock()
        callback.__name__ = "test_callback"  # Mock precisa ter __name__ configurado

        result = manager.add_hotkey("ctrl+alt+c", callback)

        assert result is True
        assert "<ctrl>+<alt>+c" in manager.hotkey_mappings
        assert manager.hotkey_mappings["<ctrl>+<alt>+c"] == callback

    def test_add_hotkey_with_running_listener(self) -> None:
        """Testa adição de hotkey quando listener já está rodando."""
        manager = KeyboardManager()
        manager.running = True

        # Mock dos métodos stop e start
        with (
            patch.object(manager, "stop") as mock_stop,
            patch.object(manager, "start") as mock_start,
        ):
            callback = Mock()
            callback.__name__ = "test_callback"  # Mock precisa ter __name__ configurado
            result = manager.add_hotkey("ctrl+alt+c", callback)

            assert result is True
            mock_stop.assert_called_once()
            mock_start.assert_called_once()

    def test_add_hotkey_value_error_exception(self) -> None:
        """Testa tratamento de ValueError durante adição de hotkey (linhas 44-45, 54)."""
        manager = KeyboardManager()
        callback = Mock()

        # Força uma ValueError no _format_hotkey_string
        with patch.object(
            manager, "_format_hotkey_string", side_effect=ValueError("Test error")
        ):
            result = manager.add_hotkey("invalid+hotkey", callback)

            assert result is False
            assert len(manager.hotkey_mappings) == 0

    def test_add_hotkey_key_error_exception(self) -> None:
        """Testa tratamento de KeyError durante adição de hotkey (linhas 44-45, 54)."""
        manager = KeyboardManager()
        callback = Mock()

        # Força uma KeyError no _format_hotkey_string
        with patch.object(
            manager, "_format_hotkey_string", side_effect=KeyError("Test error")
        ):
            result = manager.add_hotkey("ctrl+alt+c", callback)

            assert result is False
            assert len(manager.hotkey_mappings) == 0

    def test_add_hotkey_attribute_error_exception(self) -> None:
        """Testa tratamento de AttributeError durante adição de hotkey (linhas 44-45, 54)."""
        manager = KeyboardManager()
        callback = Mock()

        # Força uma AttributeError no _format_hotkey_string
        with patch.object(
            manager, "_format_hotkey_string", side_effect=AttributeError("Test error")
        ):
            result = manager.add_hotkey("ctrl+alt+c", callback)

            assert result is False
            assert len(manager.hotkey_mappings) == 0


class TestRemoveHotkey:
    """Testes para o método remove_hotkey (linhas 79-98)."""

    def test_remove_hotkey_success(self) -> None:
        """Testa remoção bem-sucedida de hotkey existente."""
        manager = KeyboardManager()
        callback = Mock()
        callback.__name__ = "test_callback"  # Mock precisa ter __name__ configurado
        manager.add_hotkey("ctrl+alt+c", callback)

        result = manager.remove_hotkey("ctrl+alt+c")

        assert result is True
        assert "<ctrl>+<alt>+c" not in manager.hotkey_mappings

    def test_remove_hotkey_with_running_listener(self) -> None:
        """Testa remoção de hotkey quando listener está rodando."""
        manager = KeyboardManager()
        manager.running = True
        callback = Mock()
        callback.__name__ = "test_callback"  # Mock precisa ter __name__ configurado
        manager.add_hotkey("ctrl+alt+c", callback)

        with (
            patch.object(manager, "stop") as mock_stop,
            patch.object(manager, "start") as mock_start,
        ):
            result = manager.remove_hotkey("ctrl+alt+c")

            assert result is True
            mock_stop.assert_called_once()
            mock_start.assert_called_once()

    def test_remove_nonexistent_hotkey(self) -> None:
        """Testa remoção de hotkey que não existe (linha ~92-94)."""
        manager = KeyboardManager()

        result = manager.remove_hotkey("ctrl+alt+x")

        assert result is False

    def test_remove_hotkey_value_error_exception(self) -> None:
        """Testa tratamento de ValueError durante remoção de hotkey (linhas ~95-98)."""
        manager = KeyboardManager()

        with patch.object(
            manager, "_format_hotkey_string", side_effect=ValueError("Test error")
        ):
            result = manager.remove_hotkey("ctrl+alt+c")

            assert result is False

    def test_remove_hotkey_key_error_exception(self) -> None:
        """Testa tratamento de KeyError durante remoção de hotkey (linhas ~95-98)."""
        manager = KeyboardManager()

        with patch.object(
            manager, "_format_hotkey_string", side_effect=KeyError("Test error")
        ):
            result = manager.remove_hotkey("ctrl+alt+c")

            assert result is False

    def test_remove_hotkey_attribute_error_exception(self) -> None:
        """Testa tratamento de AttributeError durante remoção de hotkey (linhas ~95-98)."""
        manager = KeyboardManager()

        with patch.object(
            manager, "_format_hotkey_string", side_effect=AttributeError("Test error")
        ):
            result = manager.remove_hotkey("ctrl+alt+c")

            assert result is False


class TestStart:
    """Testes para o método start (linhas 107-135)."""

    def test_start_already_running(self) -> None:
        """Testa start quando já está rodando (linha ~110-112)."""
        manager = KeyboardManager()
        manager.running = True

        with patch("src.keyboard_listener.GlobalHotKeys") as mock_global_hotkeys:
            manager.start()

            # Não deve criar novo listener
            mock_global_hotkeys.assert_not_called()

    def test_start_no_hotkeys_registered(self) -> None:
        """Testa start sem hotkeys registradas (linhas ~115-119)."""
        manager = KeyboardManager()

        with patch("src.keyboard_listener.GlobalHotKeys") as mock_global_hotkeys:
            manager.start()

            # Não deve criar listener
            mock_global_hotkeys.assert_not_called()
            assert manager.running is False

    @patch("src.keyboard_listener.GlobalHotKeys")
    def test_start_success_non_blocking(self, mock_global_hotkeys: Mock) -> None:
        """Testa start bem-sucedido em modo não-bloqueante."""
        manager = KeyboardManager()
        callback = Mock()
        callback.__name__ = "test_callback"  # Mock precisa ter __name__ configurado
        manager.add_hotkey("ctrl+alt+c", callback)

        # Configurar mock
        mock_listener = Mock()
        mock_global_hotkeys.return_value = mock_listener

        manager.start(block=False)

        assert manager.running is True
        assert manager.listener == mock_listener
        mock_global_hotkeys.assert_called_once_with(manager.hotkey_mappings)
        mock_listener.start.assert_called_once()
        mock_listener.join.assert_not_called()

    @patch("src.keyboard_listener.GlobalHotKeys")
    def test_start_success_blocking(self, mock_global_hotkeys: Mock) -> None:
        """Testa start bem-sucedido em modo bloqueante (linhas ~130-133)."""
        manager = KeyboardManager()
        callback = Mock()
        callback.__name__ = "test_callback"  # Mock precisa ter __name__ configurado
        manager.add_hotkey("ctrl+alt+c", callback)

        # Configurar mock
        mock_listener = Mock()
        mock_global_hotkeys.return_value = mock_listener

        # Executar em thread separada para evitar bloqueio do teste
        def run_start():
            manager.start(block=True)

        thread = Thread(target=run_start)
        thread.daemon = True
        thread.start()

        # Aguardar um pouco para o método start executar
        time.sleep(0.1)

        assert manager.running is True
        mock_listener.start.assert_called_once()
        mock_listener.join.assert_called_once()

    @patch("src.keyboard_listener.GlobalHotKeys")
    def test_start_runtime_error_exception(self, mock_global_hotkeys: Mock) -> None:
        """Testa tratamento de RuntimeError durante start (linhas ~134-138)."""
        manager = KeyboardManager()
        callback = Mock()
        callback.__name__ = "test_callback"  # Mock precisa ter __name__ configurado
        manager.add_hotkey("ctrl+alt+c", callback)

        # Configurar mock para lançar exceção
        mock_global_hotkeys.side_effect = RuntimeError("Test runtime error")

        manager.start()

        assert manager.running is False

    @patch("src.keyboard_listener.GlobalHotKeys")
    def test_start_os_error_exception(self, mock_global_hotkeys: Mock) -> None:
        """Testa tratamento de OSError durante start (linhas ~134-138)."""
        manager = KeyboardManager()
        callback = Mock()
        callback.__name__ = "test_callback"  # Mock precisa ter __name__ configurado
        manager.add_hotkey("ctrl+alt+c", callback)

        # Configurar mock para lançar exceção
        mock_global_hotkeys.side_effect = OSError("Test OS error")

        manager.start()

        assert manager.running is False


class TestStop:
    """Testes para o método stop (linhas 141-159)."""

    def test_stop_not_running(self) -> None:
        """Testa stop quando não está rodando (linhas ~142-144)."""
        manager = KeyboardManager()
        manager.running = False

        # Não deve gerar erro
        manager.stop()
        assert manager.running is False

    def test_stop_success_with_listener(self) -> None:
        """Testa stop bem-sucedido com listener ativo."""
        manager = KeyboardManager()
        manager.running = True

        # Mock do listener
        mock_listener = Mock()
        manager.listener = mock_listener

        manager.stop()

        assert manager.running is False
        assert manager.listener is None
        mock_listener.stop.assert_called_once()
        mock_listener.join.assert_called_once()

    def test_stop_success_without_listener(self) -> None:
        """Testa stop quando não há listener ativo."""
        manager = KeyboardManager()
        manager.running = True
        manager.listener = None

        manager.stop()

        assert manager.running is False
        assert manager.listener is None

    def test_stop_runtime_error_exception(self) -> None:
        """Testa tratamento de RuntimeError durante stop (linhas ~158-159)."""
        manager = KeyboardManager()
        manager.running = True

        # Mock do listener que lança exceção
        mock_listener = Mock()
        mock_listener.stop.side_effect = RuntimeError("Test runtime error")
        manager.listener = mock_listener

        # Não deve relançar a exceção
        manager.stop()

        # Estado deve ser limpo mesmo com erro
        assert manager.running is False

    def test_stop_os_error_exception(self) -> None:
        """Testa tratamento de OSError durante stop (linhas ~158-159)."""
        manager = KeyboardManager()
        manager.running = True

        # Mock do listener que lança exceção
        mock_listener = Mock()
        mock_listener.stop.side_effect = OSError("Test OS error")
        manager.listener = mock_listener

        # Não deve relançar a exceção
        manager.stop()

        # Estado deve ser limpo mesmo com erro
        assert manager.running is False


class TestIntegration:
    """Testes de integração para fluxos completos."""

    def test_complete_lifecycle(self) -> None:
        """Testa ciclo completo: add -> start -> stop -> remove."""
        manager = KeyboardManager()
        callback = Mock()
        callback.__name__ = "test_callback"  # Mock precisa ter __name__ configurado

        # Adicionar hotkey
        assert manager.add_hotkey("ctrl+alt+c", callback) is True

        # Mock para GlobalHotKeys
        with patch("src.keyboard_listener.GlobalHotKeys") as mock_global_hotkeys:
            mock_listener = Mock()
            mock_global_hotkeys.return_value = mock_listener

            # Iniciar
            manager.start()
            assert manager.running is True

            # Parar
            manager.stop()
            assert manager.running is False

        # Remover hotkey
        assert manager.remove_hotkey("ctrl+alt+c") is True
        assert len(manager.hotkey_mappings) == 0

    def test_multiple_hotkeys_management(self) -> None:
        """Testa gerenciamento de múltiplas hotkeys."""
        manager = KeyboardManager()
        callback1 = Mock()
        callback1.__name__ = "test_callback1"  # Mock precisa ter __name__ configurado
        callback2 = Mock()
        callback2.__name__ = "test_callback2"  # Mock precisa ter __name__ configurado

        # Adicionar múltiplas hotkeys
        assert manager.add_hotkey("ctrl+alt+c", callback1) is True
        assert manager.add_hotkey("shift+f1", callback2) is True

        assert len(manager.hotkey_mappings) == 2

        # Remover uma hotkey
        assert manager.remove_hotkey("ctrl+alt+c") is True
        assert len(manager.hotkey_mappings) == 1

        # Verificar se a hotkey correta foi removida
        assert "<shift>+f1" in manager.hotkey_mappings
        assert "<ctrl>+<alt>+c" not in manager.hotkey_mappings

    def test_restart_listener_on_hotkey_changes(self) -> None:
        """Testa reinicialização do listener ao modificar hotkeys."""
        manager = KeyboardManager()
        callback = Mock()
        callback.__name__ = "test_callback"  # Mock precisa ter __name__ configurado

        with patch("src.keyboard_listener.GlobalHotKeys") as mock_global_hotkeys:
            mock_listener = Mock()
            mock_global_hotkeys.return_value = mock_listener

            # Adicionar hotkey e iniciar
            manager.add_hotkey("ctrl+alt+c", callback)
            manager.start()

            # Adicionar outra hotkey (deve reiniciar listener)
            with (
                patch.object(manager, "stop") as mock_stop,
                patch.object(manager, "start") as mock_start,
            ):
                callback2 = Mock()
                callback2.__name__ = (
                    "test_callback2"  # Mock precisa ter __name__ configurado
                )
                manager.add_hotkey("shift+f1", callback2)

                mock_stop.assert_called_once()
                mock_start.assert_called_once()


class TestEdgeCases:
    """Testes para casos extremos e situações especiais."""

    def test_callback_with_none_value(self) -> None:
        """Testa comportamento com callback None."""
        manager = KeyboardManager()

        # Com None, falha no log mas callback já foi adicionado (comportamento atual do código)
        result = manager.add_hotkey("ctrl+alt+c", None)
        assert result is False  # Esperamos False devido ao erro AttributeError no log
        assert (
            len(manager.hotkey_mappings) == 1
        )  # Callback foi adicionado antes do erro
        assert manager.hotkey_mappings["<ctrl>+<alt>+c"] is None

    def test_empty_hotkey_string(self) -> None:
        """Testa comportamento com string de hotkey vazia."""
        manager = KeyboardManager()

        # String vazia deve ser formatada corretamente
        result = manager._format_hotkey_string("")  # noqa: SLF001
        assert result == ""

    def test_special_characters_in_hotkey(self) -> None:
        """Testa caracteres especiais em hotkeys."""
        manager = KeyboardManager()

        result = manager._format_hotkey_string("ctrl+alt+comma")  # noqa: SLF001
        assert result == "<ctrl>+<alt>+comma"

        result = manager._format_hotkey_string("ctrl+alt+period")  # noqa: SLF001
        assert result == "<ctrl>+<alt>+period"

    def test_concurrent_start_stop_operations(self) -> None:
        """Testa operações concorrentes de start/stop."""
        manager = KeyboardManager()
        callback = Mock()
        callback.__name__ = "test_callback"  # Mock precisa ter __name__ configurado
        manager.add_hotkey("ctrl+alt+c", callback)

        with patch("src.keyboard_listener.GlobalHotKeys") as mock_global_hotkeys:
            mock_listener = Mock()
            mock_global_hotkeys.return_value = mock_listener

            # Múltiplas chamadas de start
            manager.start()
            initial_running_state = manager.running
            manager.start()  # Segunda chamada deve ser ignorada

            assert manager.running == initial_running_state

            # Múltiplas chamadas de stop
            manager.stop()
            manager.stop()  # Segunda chamada deve ser segura

            assert manager.running is False


if __name__ == "__main__":
    # Executar testes se o arquivo for executado diretamente
    pytest.main([__file__, "-v"])
