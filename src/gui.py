import os
import sys
# Usar a configuração de logger centralizada
from .logger_config import logger
from pathlib import Path
from typing import Callable, List, Optional
import pyperclip
import time
from functools import partial

from PySide6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QLabel, QApplication, QFrame, QHBoxLayout, QScrollArea, QTextEdit, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, Signal, Slot, QSize, QTimer, QPoint, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor, QPalette, QFont, QIcon, QCursor, QLinearGradient, QBrush, QPixmap, QFontDatabase, QPainter, QRadialGradient, QPainterPath

from src.capture import capture_selected_text
from src.correction import get_corrected_text
from src.paste import paste_text

# Configuração de logging para o módulo
logger.info("Initializing TextaGuiWindow with enhanced styling...")

class TextaGuiWindow(QWidget):
    """
    GUI window with a 'Corrigir' button that displays original and corrected text.
    """
    
    # Signal for the button click
    button_clicked = Signal()
    
    def __init__(self, parent=None):
        """
        Initialize the GUI window.
        """
        super().__init__(parent)
        logger.info("Initializing TextaGuiWindow with enhanced styling...")
        
        self.setWindowTitle("Texta AI")
        # Prioritize FramelessWindowHint and WindowStaysOnTopHint. Qt.Tool can be problematic with custom rendering.
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        # WA_TranslucentBackground is key for custom shapes and shadows.
        self.setAttribute(Qt.WA_TranslucentBackground, True) 
        
        self._load_fonts()
        self._set_app_icon()
        
        self.setStyleSheet("""
            TextaGuiWindow { /* Target the class itself */
                background-color: transparent; /* Fully transparent for custom paint */
                border-radius: 18px; /* Slightly more rounded */
            }
            QPushButton#CorrectButton { /* Specific ID for main button */
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #3A86FF, stop:1 #2575FC);
                color: white;
                border-radius: 12px;
                padding: 12px 20px;
                font-size: 17px;
                font-weight: bold;
                font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
                border: 1px solid #4A90FF; /* Subtle border for definition */
                min-height: 30px; /* Ensure button height */
            }
            QPushButton#CorrectButton:hover {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #4E94FF, stop:1 #3A86FF);
                border: 1px solid #5A9FFF;
            }
            QPushButton#CorrectButton:pressed {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2A70F0, stop:1 #1A60E0);
                border: 1px solid #3A70F0;
            }
            QPushButton#CorrectButton:disabled {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #5A6883, stop:1 #4A5873);
                color: #A0A0B0;
                border: 1px solid #6A7893;
            }
            QLabel#TitleLabel {
                color: #ECECF1;
                font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
                font-size: 20px;
                font-weight: bold;
            }
            QLabel#InstructionLabel {
                color: #B0B0C0;
                font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
                font-size: 11px; /* Slightly smaller for less emphasis */
                line-height: 1.4;
            }
            QLabel#StatusLabel {
                color: #D0D0E0;
                font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
                font-size: 12px;
            }
            QLabel#VersionLabel {
                color: #606070;
                font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
                font-size: 10px;
            }
             QLabel#TextTitleLabel { /* For "Texto para corrigir" and "Texto corrigido" */
                color: #D0D0D5;
                font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
                font-size: 15px;
                font-weight: 500; /* Medium weight */
                padding-left: 2px;
            }
            QTextEdit {
                background-color: #161A22; /* Darker background for text areas */
                color: #E0E0E5;
                border-radius: 10px;
                border: 1px solid #2A2E3A;
                font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
                padding: 10px;
                selection-background-color: #3A86FF;
                selection-color: #FFFFFF;
            }
            QTextEdit:focus {
                border: 1px solid #3A86FF; /* Highlight border on focus */
            }
            /* Styling for Close and Settings buttons */
            QPushButton#SettingsButton, QPushButton#CloseButton {
                background-color: transparent;
                color: #9090A0;
                border: none;
                border-radius: 15px; /* Circular hover */
                font-size: 18px; /* Larger icon */
                font-weight: bold;
            }
            QPushButton#SettingsButton:hover, QPushButton#CloseButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                color: #E0E0E0;
            }
            QPushButton#SettingsButton:pressed, QPushButton#CloseButton:pressed {
                background-color: rgba(255, 255, 255, 0.15);
            }
            QFrame#windowFrame {
                background-color: transparent;
                border-radius: 18px;
            }
        """)
        
        # Em vez de aplicar a sombra à janela principal, vamos usar uma abordagem diferente
        # que não causa o erro de UpdateLayeredWindowIndirect
        
        # Criar frame interno que conterá todo o conteúdo
        self.windowFrame = QFrame(self)
        self.windowFrame.setObjectName("windowFrame")
        
        # Configurar layout principal para conter apenas o windowFrame
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.windowFrame)
        
        # Usar _init_ui para configurar o restante da interface
        self._init_ui()
        
        # Configurar tamanho fixo
        self.setFixedSize(830, 520)
        
        self.dragging = False
        self.offset = QPoint()
        self.is_processing = False
        self.original_text = ""
        self.corrected_text = ""
        
        logger.info("TextaGuiWindow initialized with new styles.")

    def _load_fonts(self):
        """Load modern fonts for the application."""
        try:
            font_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src', 'resources', 'fonts')
            fonts_to_load = {
                "Inter-Regular.otf": False,
                "Inter-Medium.otf": False,
                "Inter-Bold.otf": False
            }
            loaded_count = 0

            for font_file in fonts_to_load.keys():
                font_path = os.path.join(font_dir, font_file)
                if os.path.exists(font_path):
                    font_id = QFontDatabase.addApplicationFont(font_path)
                    if font_id != -1:
                        font_families = QFontDatabase.applicationFontFamilies(font_id)
                        if font_families:
                            logger.info(f"Successfully loaded font: {font_file} (Family: {font_families[0]})")
                            fonts_to_load[font_file] = True
                            loaded_count += 1
                        else:
                            logger.warning(f"Loaded font {font_file} but no families found.")
                    else:
                        logger.warning(f"Failed to load font: {font_file} (addApplicationFont returned -1)")
                else:
                    logger.warning(f"Font file not found: {font_path}")
            
            if loaded_count > 0:
                logger.info(f"Successfully loaded {loaded_count} Inter font variants.")
            else:
                logger.warning("Could not load any Inter fonts from resources. System fallbacks will be used.")

        except Exception as e:
            logger.warning(f"Error loading fonts: {e}")

    def _set_app_icon(self):
        """Configura o ícone da aplicação a partir de resources."""
        resources_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src', 'resources', 'images')
        logo_path = os.path.join(resources_dir, 'logo.png')
        
        if os.path.exists(logo_path):
            logger.info(f"Using logo from: {logo_path}")
            self.app_icon = QIcon(logo_path)
            self.setWindowIcon(self.app_icon)
            if QApplication.instance():
                QApplication.instance().setWindowIcon(self.app_icon)
        else:
            logger.warning(f"Logo not found at: {logo_path}")
            self.app_icon = None

    def _init_ui(self):
        """Initialize user interface components."""
        # Agora o layout principal será aplicado ao windowFrame
        self.frame_layout = QHBoxLayout(self.windowFrame)
        self.frame_layout.setContentsMargins(20, 20, 20, 20) 
        self.frame_layout.setSpacing(18)
        
        # Side Panel
        self.side_panel = QFrame(self.windowFrame) 
        self.side_panel.setObjectName("SidePanel")
        self.side_panel.setFixedWidth(240) 
        self.side_panel.setStyleSheet("""
            QFrame#SidePanel {
                background-color: #1A1E28; 
                border-radius: 16px;
                border: 1px solid #2A2E3A;
            }
        """)
        self.side_panel_layout = QVBoxLayout(self.side_panel)
        self.side_panel_layout.setContentsMargins(20, 20, 20, 20)
        self.side_panel_layout.setSpacing(18)
        
        self.header_layout = QHBoxLayout()
        self.header_layout.setSpacing(10)
        self.logo_label = QLabel(self.side_panel)
        self.logo_label.setFixedSize(36, 36) 
        resources_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src', 'resources', 'images')
        logo_path = os.path.join(resources_dir, 'logo.png')
        if os.path.exists(logo_path):
            logo_pixmap = QPixmap(logo_path)
            self.logo_label.setPixmap(logo_pixmap.scaled(36, 36, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.logo_label.setText("🤖") 
            self.logo_label.setStyleSheet("font-size: 28px; color: #3A86FF;")

        self.header_layout.addWidget(self.logo_label)
        self.title_label = QLabel("Texta AI", self.side_panel)
        self.title_label.setObjectName("TitleLabel") 
        self.header_layout.addWidget(self.title_label)
        self.side_panel_layout.addLayout(self.header_layout)
        
        self.instruction_label = QLabel("Selecione texto em outro aplicativo\nantes de clicar em Corrigir", self.side_panel)
        self.instruction_label.setObjectName("InstructionLabel")
        self.instruction_label.setAlignment(Qt.AlignCenter)
        self.instruction_label.setWordWrap(True)
        self.side_panel_layout.addWidget(self.instruction_label)
        
        self.correct_button = QPushButton("Corrigir", self.side_panel)
        self.correct_button.setObjectName("CorrectButton") 
        self.correct_button.setCursor(Qt.PointingHandCursor)
        button_shadow = QGraphicsDropShadowEffect(self.correct_button)
        button_shadow.setBlurRadius(15)
        button_shadow.setColor(QColor(0, 0, 0, 70))
        button_shadow.setOffset(0, 3)
        self.correct_button.setGraphicsEffect(button_shadow)
        self.correct_button.clicked.connect(self._on_button_clicked)
        self.side_panel_layout.addWidget(self.correct_button)
        
        self.status_label = QLabel("", self.side_panel)
        self.status_label.setObjectName("StatusLabel")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        self.side_panel_layout.addWidget(self.status_label)
        
        self.side_panel_layout.addStretch(1)
        
        self.version_label = QLabel("v1.0", self.side_panel)
        self.version_label.setObjectName("VersionLabel")
        self.version_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        self.side_panel_layout.addWidget(self.version_label)
        
        self.frame_layout.addWidget(self.side_panel)
        
        # Content Area
        self.content_area = QFrame(self.windowFrame) 
        self.content_area.setObjectName("ContentArea")
        self.content_area.setStyleSheet("""
            QFrame#ContentArea {
                background-color: #1A1E28; 
                border-radius: 16px;
                border: 1px solid #2A2E3A;
            }
        """)
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(10, 20, 10, 20) 
        self.content_layout.setSpacing(12)
        
        self.original_text_label = QLabel("Texto para corrigir", self.content_area)
        self.original_text_label.setObjectName("TextTitleLabel")
        self.content_layout.addWidget(self.original_text_label)
        
        self.original_text_edit = QTextEdit(self.content_area)
        self.original_text_edit.setReadOnly(True)
        self.original_text_edit.setMinimumHeight(190) 
        self.content_layout.addWidget(self.original_text_edit)
        
        self.corrected_text_label = QLabel("Texto corrigido", self.content_area)
        self.corrected_text_label.setObjectName("TextTitleLabel")
        self.content_layout.addWidget(self.corrected_text_label)
        
        self.corrected_text_edit = QTextEdit(self.content_area)
        self.corrected_text_edit.setReadOnly(True)
        self.corrected_text_edit.setMinimumHeight(190) 
        self.content_layout.addWidget(self.corrected_text_edit)
        
        self.frame_layout.addWidget(self.content_area, 1)
        
        # Close Button
        self.close_button = QPushButton("✕", self.windowFrame)
        self.close_button.setObjectName("CloseButton")
        self.close_button.setFixedSize(32, 32)
        self.close_button.setCursor(Qt.PointingHandCursor)
        self.close_button.clicked.connect(self.hide)
        
        # Settings Button
        self.settings_button = QPushButton("⚙", self.windowFrame)
        self.settings_button.setObjectName("SettingsButton")
        self.settings_button.setFixedSize(32, 32)
        self.settings_button.setCursor(Qt.PointingHandCursor)
        
        self.close_button.move(self.width() - self.close_button.width() - 24, 24)
        self.settings_button.move(24, 24)

    def _on_button_clicked(self):
        """Handle button click: update UI, hide window, and signal WorkflowManager."""
        if self.is_processing:
            return
        
        logger.info("Correction button clicked. Hiding GUI and signaling workflow.")
        self._set_processing_state(True)
        
        self.original_text_edit.clear()
        self.corrected_text_edit.clear()
        
        self.hide() 
        QApplication.processEvents() 
        time.sleep(0.05) 
        self.button_clicked.emit()

    @Slot(bool)
    def reset_state(self, success):
        """Resets the button and status after workflow completion, and reshows the window."""
        logger.info(f"Resetting GUI state after workflow (Success: {success}).")
        self._set_processing_state(False)
        
        # Não mostrar automaticamente a janela após a correção
        # O código abaixo foi comentado para não forçar a exibição da GUI após cada correção
        # if not self.isVisible():
        #     logger.info("Reshowing GUI window.")
        #     self.toggle_visibility() 
        
        # Apenas atualizar o status se a GUI estiver visível
        if self.isVisible():
            if success and "Erro" not in self.status_label.text():
                self.set_status("Texto corrigido!")
                QTimer.singleShot(3000, lambda: self.set_status("")) 
            elif not success and not self.status_label.text(): 
                self.set_status("Ocorreu um erro no fluxo.", error=True)
        else:
            # Registra o resultado no log mesmo se a janela não estiver visível
            if success:
                logger.info("Texto corrigido com sucesso! (GUI oculta)")
            else:
                logger.warning("Ocorreu um erro no fluxo. (GUI oculta)")

    @Slot(str, bool)
    def set_status(self, message, error=False):
        """Set the status message with optional error styling."""
        logger.info(f"Setting status: {message} (error={error})")
        if self.isVisible():
            self.status_label.setText(message)
            if error:
                self.status_label.setStyleSheet("color: #FF7070; font-size: 12px; font-family: 'Inter', 'Segoe UI', Arial, sans-serif;")
            else:
                self.status_label.setStyleSheet("color: #A0FFA0; font-size: 12px; font-family: 'Inter', 'Segoe UI', Arial, sans-serif;") 
            self.update()
        else:
            if error:
                logger.error(f"Status (GUI hidden): {message}")
            else:
                logger.info(f"Status (GUI hidden): {message}")

    @Slot(str, str)
    def set_text_content(self, original_text, corrected_text):
        """Update the text areas with original and corrected text."""
        logger.info("Updating text content in GUI")
        self.original_text = original_text
        self.corrected_text = corrected_text
        self.original_text_edit.setText(original_text)
        self.corrected_text_edit.setText(corrected_text)
        # Ensure the text areas are repainted, especially if the window was hidden
        if self.isVisible():
            self.original_text_edit.repaint()
            self.corrected_text_edit.repaint()
        self.update() # General update for the window

    def _set_processing_state(self, is_processing):
        """Update the UI to reflect the processing state."""
        self.is_processing = is_processing
        self.correct_button.setEnabled(not is_processing)
        if is_processing:
            self.correct_button.setText("Processando...")
            self.set_status("Corrigindo texto...")
        else:
            self.correct_button.setText("Corrigir")
    
    def paintEvent(self, event):
        """Override to create custom painting for the window background."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Pinta o fundo da janela com transparência para evitar artefatos
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0)) 
        
        # Desenha um fundo com bordas arredondadas para o windowFrame
        path = QPainterPath()
        path.addRoundedRect(self.windowFrame.geometry(), 18, 18)
        
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(32, 36, 48))    
        gradient.setColorAt(0.5, QColor(28, 31, 42))  
        gradient.setColorAt(1, QColor(22, 25, 34))
        
        painter.fillPath(path, gradient)
    
    def mousePressEvent(self, event):
        """Handle mouse press events for window dragging."""
        if event.button() == Qt.LeftButton:
            if (event.position().y() < 50 and 
                event.position().x() > self.settings_button.width() + 15 and
                event.position().x() < self.width() - self.close_button.width() - 15):
                self.dragging = True
                self.offset = event.position().toPoint()
        super().mousePressEvent(event)
                
    def mouseMoveEvent(self, event):
        """Handle mouse move events for window dragging."""
        if self.dragging and event.buttons() & Qt.LeftButton:
            new_pos = self.mapToGlobal(event.position().toPoint()) - self.offset
            self.move(new_pos)
        super().mouseMoveEvent(event)
                
    def mouseReleaseEvent(self, event):
        """Handle mouse release events for window dragging."""
        if event.button() == Qt.LeftButton:
            self.dragging = False
        super().mouseReleaseEvent(event)

    def resizeEvent(self, event):
        """ Ensure buttons are repositioned on resize (though window is fixed size now) """
        super().resizeEvent(event)
        # Ensure buttons are correctly placed even if size changes (e.g. due to system scaling)
        if hasattr(self, 'close_button') and self.close_button:
             self.close_button.move(self.width() - self.close_button.width() - 24, 24)
        if hasattr(self, 'settings_button') and self.settings_button:
             self.settings_button.move(24, 24)


    def toggle_visibility(self):
        """Toggle the visibility of the window."""
        logger.info(f"Toggle visibility. Is visible: {self.isVisible()}")
        try:
            if self.isVisible():
                self.hide()
            else:
                cursor_pos = QCursor.pos()
                screen = QApplication.screenAt(cursor_pos) 
                if not screen: screen = QApplication.primaryScreen()
                
                screen_geometry = screen.availableGeometry()
                x = max(screen_geometry.left(), min(cursor_pos.x() - self.width() // 2, screen_geometry.right() - self.width()))
                y = max(screen_geometry.top(), min(cursor_pos.y() - self.height() // 2, screen_geometry.bottom() - self.height()))
                
                self.move(x, y)
                self.setWindowState((self.windowState() & ~Qt.WindowMinimized) | Qt.WindowActive)
                self.show()
                self.raise_()
                self.activateWindow()
                
                # Use QTimer.singleShot para garantir que atualizações de texto 
                # ocorram na thread da GUI após a janela ser exibida
                if self.original_text or self.corrected_text:
                    QTimer.singleShot(0, self._update_text_content_safely)
                
                logger.info("Window shown and activated.")
        except Exception as e:
            logger.error(f"Error in toggle_visibility: {e}")
            
    def _update_text_content_safely(self):
        """Atualiza o conteúdo dos campos de texto de forma thread-safe."""
        try:
            self.original_text_edit.setText(self.original_text)
            self.corrected_text_edit.setText(self.corrected_text)
            self.update()  # Solicita repintura da janela
            logger.debug("Text content updated safely in GUI thread")
        except Exception as e:
            logger.error(f"Error updating text content safely: {e}") 