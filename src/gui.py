import logging
import pyperclip
import time
from functools import partial

from PySide6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QLabel, QApplication, QFrame
from PySide6.QtCore import Qt, Signal, Slot, QSize, QTimer, QPoint
from PySide6.QtGui import QColor, QPalette, QFont, QIcon, QCursor, QLinearGradient, QBrush

from src.capture import capture_selected_text
from src.correction import get_corrected_text
from src.paste import paste_text

# Configuração de logging para o módulo
logger = logging.getLogger(__name__)

class TextaGuiWindow(QWidget):
    """
    Simple GUI window with a 'Corrigir' button that performs the same 
    function as Ctrl+Alt+C but in a graphical interface.
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
        """)
        
        # Set fixed size for the window
        self.setFixedSize(220, 260)
        
        # Create layout
        self._init_ui()
        
        # Initialize variables for dragging window
        self.dragging = False
        self.offset = QPoint()
        
        # For tracking button state
        self.is_processing = False
        
        logger.info("TextaGuiWindow initialized.")

    def _init_ui(self):
        """Initialize user interface components."""
        # Create main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(10)
        
        # Create title label
        self.title_label = QLabel("Texta AI", self)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #C0C0E0;
        """)
        self.layout.addWidget(self.title_label)
        
        # Add instruction label
        self.instruction_label = QLabel("Selecione texto em outro aplicativo\nantes de clicar em Corrigir", self)
        self.instruction_label.setAlignment(Qt.AlignCenter)
        self.instruction_label.setStyleSheet("""
            font-size: 11px;
            color: #A0A0C0;
        """)
        self.layout.addWidget(self.instruction_label)
        
        # Create the correction button
        self.correct_button = QPushButton("Corrigir", self)
        self.correct_button.clicked.connect(self._on_button_clicked)
        self.correct_button.setCursor(Qt.PointingHandCursor)
        self.layout.addWidget(self.correct_button)
        
        # Status message label
        self.status_label = QLabel("", self)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("""
            font-size: 11px;
            color: #E0E0A0;
        """)
        self.layout.addWidget(self.status_label)
        
        # Create version label at the bottom right
        self.version_label = QLabel("v1.0", self)
        self.version_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        self.version_label.setStyleSheet("""
            font-size: 10px;
            color: #5F5F70;
        """)
        self.layout.addWidget(self.version_label)
        
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
            self.set_status("Texto corrigido e colado!")
            QTimer.singleShot(2500, lambda: self.set_status("")) # Clear success message after 2.5s
        elif not success and not self.status_label.text(): # If workflow failed but no specific error was set
            self.set_status("Ocorreu um erro no fluxo.", error=True)
        # Error messages set previously via set_status will persist

    def set_status(self, message, error=False):
        """Set the status message with optional error styling."""
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
            QApplication.processEvents()
        else:
            # If window is hidden, just log the status
             log_level = logging.ERROR if error else logging.INFO
             logger.log(log_level, f"Status update (GUI hidden): {message}")

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
            # Status is now set explicitly in reset_state or during error handling
            # self.set_status("Corrigindo texto...") 
    
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