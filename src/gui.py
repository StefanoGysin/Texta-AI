import logging
import pyperclip
import time
import os
from functools import partial

from PySide6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QLabel, QApplication, QFrame, QHBoxLayout, QScrollArea, QTextEdit
from PySide6.QtCore import Qt, Signal, Slot, QSize, QTimer, QPoint
from PySide6.QtGui import QColor, QPalette, QFont, QIcon, QCursor, QLinearGradient, QBrush, QPixmap

from src.capture import capture_selected_text
from src.correction import get_corrected_text
from src.paste import paste_text

# Configuração de logging para o módulo
logger = logging.getLogger(__name__)

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
        logger.info("Initializing TextaGuiWindow...")
        
        self.setWindowTitle("Texta AI")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        
        # Configurar ícone da aplicação se disponível
        self._set_app_icon()
        
        # Enable custom styling
        self.setStyleSheet("""
            QWidget {
                background-color: #2A2A3A;
                border-radius: 14px;
                border: 1px solid #3D3D5C;
            }
            QPushButton {
                background-color: #428BFA;
                color: white;
                border-radius: 10px;
                padding: 10px;
                font-size: 16px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton:hover {
                background-color: #529BFF;
            }
            QPushButton:pressed {
                background-color: #3272D9;
            }
            QLabel {
                color: #E0E0E0;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
            }
            QTextEdit {
                background-color: #1E1E2A;
                color: #FFFFFF;
                border-radius: 8px;
                border: 1px solid #3D3D5C;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
                padding: 8px;
            }
        """)
        
        # Set fixed size for the window (increased size to fit text areas)
        self.setFixedSize(820, 500)
        
        # Create layout
        self._init_ui()
        
        # Initialize variables for dragging window
        self.dragging = False
        self.offset = QPoint()
        
        # For tracking button state
        self.is_processing = False
        
        # For storing original and corrected text
        self.original_text = ""
        self.corrected_text = ""
        
        logger.info("TextaGuiWindow initialized.")

    def _set_app_icon(self):
        """Configura o ícone da aplicação a partir de resources."""
        # Verificar se o diretório de recursos existe
        resources_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src', 'resources', 'images')
        logo_path = os.path.join(resources_dir, 'logo.png')
        
        # Verificar se o arquivo de logo existe
        if os.path.exists(logo_path):
            logger.info(f"Usando logo em: {logo_path}")
            self.app_icon = QIcon(logo_path)
            self.setWindowIcon(self.app_icon)
            # Também definir como ícone para toda a aplicação
            if QApplication.instance():
                QApplication.instance().setWindowIcon(self.app_icon)
        else:
            logger.warning(f"Logo não encontrado em: {logo_path}")
            self.app_icon = None

    def _init_ui(self):
        """Initialize user interface components."""
        # Create main layout
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)
        
        # Create side panel for controls
        self.side_panel = QWidget(self)
        self.side_panel.setFixedWidth(220)
        self.side_panel_layout = QVBoxLayout(self.side_panel)
        self.side_panel_layout.setContentsMargins(10, 10, 10, 10)
        self.side_panel_layout.setSpacing(10)
        
        # Adicionar layout para o logo e título
        self.header_layout = QHBoxLayout()
        
        # Adicionar logo (se disponível)
        self.logo_label = QLabel(self.side_panel)
        self.logo_label.setFixedSize(40, 40)
        resources_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src', 'resources', 'images')
        logo_path = os.path.join(resources_dir, 'logo.png')
        
        if os.path.exists(logo_path):
            logo_pixmap = QPixmap(logo_path)
            self.logo_label.setPixmap(logo_pixmap.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            logger.info(f"Logo carregado da imagem em: {logo_path}")
        else:
            self.logo_label.setText("🤖")
            self.logo_label.setStyleSheet("font-size: 24px; color: #428BFA;")
            logger.warning(f"Logo não encontrado, usando emoji padrão")
        
        self.header_layout.addWidget(self.logo_label)
        
        # Create title label
        self.title_label = QLabel("Texta AI", self.side_panel)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #C0C0E0;
        """)
        self.header_layout.addWidget(self.title_label)
        
        # Adicionar header ao layout principal
        self.side_panel_layout.addLayout(self.header_layout)
        
        # Add instruction label
        self.instruction_label = QLabel("Selecione texto em outro aplicativo\nantes de clicar em Corrigir", self.side_panel)
        self.instruction_label.setAlignment(Qt.AlignCenter)
        self.instruction_label.setStyleSheet("""
            font-size: 11px;
            color: #A0A0C0;
        """)
        self.side_panel_layout.addWidget(self.instruction_label)
        
        # Create the correction button
        self.correct_button = QPushButton("Corrigir", self.side_panel)
        self.correct_button.clicked.connect(self._on_button_clicked)
        self.correct_button.setCursor(Qt.PointingHandCursor)
        self.side_panel_layout.addWidget(self.correct_button)
        
        # Status message label
        self.status_label = QLabel("", self.side_panel)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("""
            font-size: 11px;
            color: #E0E0A0;
        """)
        self.side_panel_layout.addWidget(self.status_label)
        
        # Add spacer to push version label to bottom
        self.side_panel_layout.addStretch(1)
        
        # Create version label at the bottom
        self.version_label = QLabel("v1.0", self.side_panel)
        self.version_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        self.version_label.setStyleSheet("""
            font-size: 10px;
            color: #5F5F70;
        """)
        self.side_panel_layout.addWidget(self.version_label)
        
        # Add side panel to main layout
        self.layout.addWidget(self.side_panel)
        
        # Create content area for text displays
        self.content_area = QWidget(self)
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(15)
        
        # Create widgets for original text
        self.original_text_label = QLabel("Texto para corrigir", self.content_area)
        self.original_text_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #E0E0E0;
        """)
        self.content_layout.addWidget(self.original_text_label)
        
        # Original text area
        self.original_text_edit = QTextEdit(self.content_area)
        self.original_text_edit.setReadOnly(True)
        self.original_text_edit.setMinimumHeight(180)
        self.content_layout.addWidget(self.original_text_edit)
        
        # Create widgets for corrected text
        self.corrected_text_label = QLabel("Texto corrigido", self.content_area)
        self.corrected_text_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #E0E0E0;
        """)
        self.content_layout.addWidget(self.corrected_text_label)
        
        # Corrected text area
        self.corrected_text_edit = QTextEdit(self.content_area)
        self.corrected_text_edit.setReadOnly(True)
        self.corrected_text_edit.setMinimumHeight(180)
        self.content_layout.addWidget(self.corrected_text_edit)
        
        # Add content area to main layout
        self.layout.addWidget(self.content_area, 1)
        
        # Create close button (X) in the top right corner
        self.close_button = QPushButton("✕", self)
        self.close_button.setFixedSize(24, 24)
        self.close_button.move(self.width() - 30, 8)
        self.close_button.clicked.connect(self.hide)
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #808090;
                font-size: 16px;
                padding: 0px;
            }
            QPushButton:hover {
                color: #C0C0C0;
            }
        """)
        
        # Create settings button (gear icon) in the top left corner
        self.settings_button = QPushButton("⚙", self)
        self.settings_button.setFixedSize(24, 24)
        self.settings_button.move(8, 8)
        self.settings_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #808090;
                font-size: 16px;
                padding: 0px;
            }
            QPushButton:hover {
                color: #C0C0C0;
            }
        """)
        # Settings button is not connected to any action yet
        # Will be implemented in a future update

    def _on_button_clicked(self):
        """Handle button click: update UI, hide window, and signal WorkflowManager."""
        if self.is_processing:
            logger.info("Button clicked while processing - ignoring")
            return
        
        logger.info("Correction button clicked. Hiding GUI and signaling workflow.")
        self._set_processing_state(True) # Disable button, set status
        
        # Clear text areas when starting new correction
        self.original_text_edit.clear()
        self.corrected_text_edit.clear()
        
        self.hide() # Hide the GUI window to return focus
        QApplication.processEvents() # Ensure hide event is processed
        time.sleep(0.05) # Small delay to ensure focus shifts
        self.button_clicked.emit() # Signal the manager to start the actual workflow

    @Slot(bool) # Accept boolean argument for success status
    def reset_state(self, success):
        """Resets the button and status after workflow completion, and reshows the window."""
        logger.info(f"Resetting GUI state after workflow completion (Success: {success}).")
        
        # Re-enable the button first
        self._set_processing_state(False)
        
        # Reshow the window if it was hidden by the button click
        if not self.isVisible():
            logger.info("Reshowing GUI window after workflow completion.")
            self.toggle_visibility() # Make it visible again, near the cursor
        
        # Update status message based on success (the message might have been set during error handling)
        if success and "Erro" not in self.status_label.text(): # Only overwrite if no error was explicitly set
            self.set_status("Texto corrigido!")
            QTimer.singleShot(2500, lambda: self.set_status("")) # Clear success message after 2.5s
        elif not success and not self.status_label.text(): # If workflow failed but no specific error was set
            self.set_status("Ocorreu um erro no fluxo.", error=True)
        # Error messages set previously via set_status will persist

    @Slot(str, bool)
    def set_status(self, message, error=False):
        """Set the status message with optional error styling."""
        logger.info(f"Definindo status: {message} (erro={error})")
        # Update status immediately if window is visible
        if self.isVisible():
            self.status_label.setText(message)
            if error:
                self.status_label.setStyleSheet("""
                    font-size: 11px;
                    color: #FF9090; /* Reddish for errors */
                """)
            else:
                 # Yellowish for success/info
                self.status_label.setStyleSheet("""
                    font-size: 11px;
                    color: #E0E0A0;
                """)
            # Make sure the message is immediately visible
            self.update()
        else:
            # If window is hidden, just log the status
             log_level = logging.ERROR if error else logging.INFO
             logger.log(log_level, f"Status update (GUI hidden): {message}")

    @Slot(str, str)
    def set_text_content(self, original_text, corrected_text):
        """Update the text areas with original and corrected text.
        
        Args:
            original_text (str): The original, uncorrected text
            corrected_text (str): The corrected text (can be empty)
        """
        logger.info("Atualizando conteúdo de texto na GUI")
        self.original_text = original_text
        self.corrected_text = corrected_text
        
        # Update UI text areas
        self.original_text_edit.setText(original_text)
        self.corrected_text_edit.setText(corrected_text)
        
        # Update the display
        self.update()

    def _set_processing_state(self, is_processing):
        """Update the UI to reflect the processing state."""
        self.is_processing = is_processing
        
        if is_processing:
            self.correct_button.setText("Processando...")
            self.correct_button.setEnabled(False)
            self.correct_button.setStyleSheet("""
                background-color: #3272D9;
                color: #CCCCCC;
                border-radius: 10px;
                padding: 10px;
                font-size: 16px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial, sans-serif;
            """)
            self.set_status("Corrigindo texto...") # Status shown when processing starts
        else:
            self.correct_button.setText("Corrigir")
            self.correct_button.setEnabled(True)
            self.correct_button.setStyleSheet("")  # Reset to default style
    
    def mousePressEvent(self, event):
        """Handle mouse press events for window dragging."""
        if event.button() == Qt.LeftButton:
            # Check if click is in the title bar area (excluding buttons)
            if (event.position().y() < 40 and
                event.position().x() > 30 and
                event.position().x() < self.width() - 30):
                self.dragging = True
                self.offset = event.position().toPoint()
        super().mousePressEvent(event)
                
    def mouseMoveEvent(self, event):
        """Handle mouse move events for window dragging."""
        if self.dragging and event.buttons() & Qt.LeftButton:
            self.move(self.mapToGlobal(event.position().toPoint()) - self.offset)
        super().mouseMoveEvent(event)
                
    def mouseReleaseEvent(self, event):
        """Handle mouse release events for window dragging."""
        if event.button() == Qt.LeftButton:
            self.dragging = False
        super().mouseReleaseEvent(event)

    def toggle_visibility(self):
        """Toggle the visibility of the window."""
        logger.info(f"Toggle visibility called. Current visibility: {self.isVisible()}")
        
        try:
            if self.isVisible():
                logger.info("Window is visible, hiding now")
                self.hide()
            else:
                logger.info("Window is hidden, showing now")
                
                # Get cursor position for positioning the window
                cursor_pos = QCursor.pos()
                logger.info(f"Cursor position: {cursor_pos.x()}, {cursor_pos.y()}")
                
                # Get screen where cursor is located
                screen = QApplication.primaryScreen()
                screens = QApplication.screens()
                logger.info(f"Number of screens: {len(screens)}")
                
                # Try to get the screen at cursor position
                for s in screens:
                    geometry = s.geometry()
                    logger.info(f"Screen geometry: {geometry.left()}, {geometry.top()}, {geometry.width()}, {geometry.height()}")
                    if geometry.contains(cursor_pos):
                        screen = s
                        logger.info(f"Found screen containing cursor: {s.name()}")
                        break
                
                if screen:
                    # Get screen geometry and calculate center position
                    screen_geometry = screen.availableGeometry()
                    window_width = self.width()
                    window_height = self.height()
                    
                    # Position near cursor but keep within screen bounds
                    pos_x = max(screen_geometry.left(), 
                               min(cursor_pos.x() - window_width // 2,
                                   screen_geometry.right() - window_width))
                    pos_y = max(screen_geometry.top(), 
                               min(cursor_pos.y() - window_height // 2,
                                   screen_geometry.bottom() - window_height))
                    
                    logger.info(f"Moving window to position: {pos_x}, {pos_y} on screen: {screen.name()}")
                    self.move(pos_x, pos_y)
                else:
                    # Fallback to center of primary screen
                    logger.warning("Could not determine screen, centering on primary screen")
                    center = QApplication.primaryScreen().availableGeometry().center()
                    self.move(center.x() - self.width() // 2, center.y() - self.height() // 2)
                
                # Ensure window is visible, active and on top using multiple approaches
                logger.info("Making window visible using multiple techniques")
                self.setWindowState(self.windowState() & ~Qt.WindowMinimized)
                
                # Make the window visible
                self.show()
                QApplication.processEvents()  # Process pending events immediately
                
                self.raise_()
                QApplication.processEvents()
                
                self.activateWindow()
                QApplication.processEvents()
                
                # Force update/repaint
                self.update()
                self.repaint()
                
                logger.info("Window should now be visible and active")
        except Exception as e:
            logger.error(f"Error in toggle_visibility: {e}", exc_info=True) 