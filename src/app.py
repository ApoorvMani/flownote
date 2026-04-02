"""
FlowNote - Main application (GUI + backend daemon)
"""

import sys
import threading
from PyQt5 import QtWidgets, QtCore

from src.config import get_config
from src.utils.logger import get_logger
from src.utils.ollama_checker import OllamaChecker
from src.core import InputRouter, InputMode, HotkeyListener, get_memory
from src.gui.bubble_widget import BubbleWidget, _CaptureCompleteEvent
from src.gui.status_indicator import StatusState
from src.gui.system_tray import SystemTray


class FlowNoteApp(QtCore.QObject):
    """Main application orchestrating GUI, capture, and backend"""
    
    ui_preview_update = QtCore.pyqtSignal(str, str)
    hotkey_capture_signal = QtCore.pyqtSignal()
    hotkey_toggle_signal = QtCore.pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.ui_preview_update.connect(self._handle_ui_preview_update)
        self.hotkey_capture_signal.connect(self._handle_hotkey_capture)
        self.hotkey_toggle_signal.connect(self._handle_hotkey_toggle)
        self.config = get_config()
        self.logger = get_logger("flownote")
        self.memory = get_memory()
        self.router = InputRouter()
        self.hotkey = None
        self.toggle_hotkey = None
        self.bubble = None
        self.tray = None
        self._worker_thread = None
        self._is_initialized = False

    def initialize(self) -> bool:
        self.logger.info("Initializing FlowNote...")

        if not self._check_ollama():
            return False

        self._setup_router()
        self._is_initialized = True
        return True

    def _check_ollama(self) -> bool:
        base_url = self.config.ollama_base_url
        if not OllamaChecker.ensure_ollama_running(base_url):
            return False

        selected_model = OllamaChecker.auto_select_model(base_url, self.config.ollama_model)
        if selected_model:
            self.router.set_model(selected_model)
            self.logger.info(f"Using model: {selected_model}")

        return True

    def _setup_router(self):
        note_style = self.memory.get_note_style()
        self.router = InputRouter(note_style=note_style)
        if self.config.ollama_model:
            self.router.set_model(self.config.ollama_model)

    def create_bubble(self):
        """Create and setup the main bubble widget"""
        self.bubble = BubbleWidget()
        
        # Connect bubble signals
        self.bubble.clicked.connect(self._on_bubble_clicked)
        self.bubble.style_changed.connect(self._on_style_changed)
        
        self.bubble.show()
        self.logger.info("Bubble widget created")

    def _on_bubble_clicked(self, mode: str):
        """Handle bubble click - trigger capture"""
        # Expand bubble if collapsed to show UI
        if not self.bubble.is_expanded():
            self.bubble.expand()
        
        self._start_capture(mode)

    def _on_style_changed(self, style: str):
        """Handle style change from bubble UI"""
        self.memory.set_note_style(style)
        self.router.set_note_style(style)
        self.logger.info(f"Note style changed to: {style}")

    def _start_capture(self, mode: str):
        """Start capture process with given mode"""
        mode_map = {
            "clipboard": InputMode.CLIPBOARD,
            "screenshot": InputMode.SCREENSHOT,
            "link": InputMode.LINK,
        }
        input_mode = mode_map.get(mode, InputMode.CLIPBOARD)
        
        # Update bubble state
        if self.bubble:
            self.bubble.update_preview("Capturing", "Capturing clipboard...")
        
        # Run capture in background thread
        self._worker_thread = threading.Thread(
            target=self._capture_worker,
            args=(input_mode,),
            daemon=True
        )
        self._worker_thread.start()

    def _capture_worker(self, mode: InputMode):
        """Background worker for capture and AI processing"""
        try:
            self.ui_preview_update.emit("Processing", "Processing with AI...")
            
            success, note = self.router.capture_and_process(mode)
            
            # Update UI on main thread
            app = QtWidgets.QApplication.instance()
            if app:
                app.postEvent(self.bubble, _CaptureCompleteEvent(success, note))

        except Exception as e:
            self.logger.error(f"Capture error: {e}")
            app = QtWidgets.QApplication.instance()
            if app:
                app.postEvent(self.bubble, _CaptureCompleteEvent(False, str(e)))

    def create_tray(self):
        """Create system tray icon"""
        self.tray = SystemTray()
        self.tray.clicked.connect(self._on_tray_clicked)
        self.tray.quit_requested.connect(self._on_quit_requested)
        self.tray.show_requested.connect(self._on_show_requested)
        self.tray.capture_clipboard.connect(lambda: self._on_bubble_clicked("clipboard"))
        self.tray.capture_screenshot.connect(lambda: self._on_bubble_clicked("screenshot"))
        self.tray.show()

    def _on_tray_clicked(self):
        """Handle tray icon click - toggle bubble"""
        if self.bubble:
            if self.bubble.is_expanded():
                self.bubble.collapse()
            else:
                self.bubble.expand()

    def _on_show_requested(self):
        """Show and expand bubble"""
        if self.bubble:
            self.bubble.show()
            self.bubble.expand()

    def _on_quit_requested(self):
        """Handle quit request"""
        self.shutdown()
        QtWidgets.QApplication.quit()

    def start_hotkey_listener(self):
        """Setup hotkey listener for capture triggers"""
        self.hotkey = HotkeyListener(self.config.hotkey_capture)
        self.hotkey.register_callback(self._on_hotkey_triggered)
        self.hotkey.start()
        self.logger.info(f"Hotkey listener started: {self.config.hotkey_capture}")
        
        # Separate hotkey for toggling bubble visibility
        self.toggle_hotkey = HotkeyListener("ctrl+shift+b")
        self.toggle_hotkey.register_callback(self._on_toggle_hotkey)
        self.toggle_hotkey.start()
        self.logger.info("Toggle hotkey listener started: ctrl+shift+b")

    def _handle_ui_preview_update(self, status: str, text: str):
        if self.bubble:
            self.bubble.update_preview(status, text)

    def _on_hotkey_triggered(self):
        """Handle global hotkey trigger - capture"""
        self.logger.info("Capture hotkey triggered")
        self.hotkey_capture_signal.emit()

    def _handle_hotkey_capture(self):
        if self.bubble:
            # Show bubble if hidden
            if not self.bubble.isVisible():
                self.bubble.show()
            # Expand if collapsed
            if not self.bubble.is_expanded():
                self.bubble.expand()
        
        self._start_capture("clipboard")

    def _on_toggle_hotkey(self):
        """Handle toggle hotkey - show/hide bubble"""
        self.logger.info("Toggle hotkey triggered")
        self.hotkey_toggle_signal.emit()

    def _handle_hotkey_toggle(self):
        if self.bubble:
            if self.bubble.isVisible():
                self.bubble.hide()
            else:
                self.bubble.show()
                if not self.bubble.is_expanded():
                    self.bubble.expand()

    def shutdown(self):
        """Clean shutdown"""
        self.logger.info("Shutting down FlowNote...")
        if self.hotkey:
            self.hotkey.stop()
        if self.bubble:
            self.bubble.hide()
        if self.tray:
            self.tray.hide()

    def run(self) -> int:
        """Main application entry point"""
        app = QtWidgets.QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)

        if not self.initialize():
            error_box = QtWidgets.QMessageBox()
            error_box.setIcon(QtWidgets.QMessageBox.Critical)
            error_box.setWindowTitle("FlowNote - Ollama Error")
            error_box.setText("Ollama is not running.\n\nPlease start Ollama with: ollama serve")
            error_box.exec()
            return 1

        self.create_bubble()
        self.create_tray()
        self.start_hotkey_listener()

        app.aboutToQuit.connect(self.shutdown)

        return app.exec()

def main() -> int:
    print("\n" + "=" * 50)
    print("FlowNote - AI-Powered Note Taking")
    print("=" * 50 + "\n")

    app = FlowNoteApp()
    exit_code = app.run()

    print("\nFlowNote closed.")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())