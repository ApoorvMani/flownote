"""
FlowNote - System tray integration
"""

from PyQt5 import QtWidgets, QtCore, QtGui


class SystemTray(QtWidgets.QSystemTrayIcon):
    """System tray icon for FlowNote"""
    
    clicked = QtCore.pyqtSignal()
    quit_requested = QtCore.pyqtSignal()
    show_requested = QtCore.pyqtSignal()
    capture_clipboard = QtCore.pyqtSignal()
    capture_screenshot = QtCore.pyqtSignal()
    
    _colors = {
        "idle": "#6B7280",
        "capturing": "#3B82F6",
        "processing": "#F59E0B",
        "saved": "#10B981",
        "error": "#EF4444",
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_status = "idle"
        self._create_icon("idle")
        self._create_menu()
        self.setToolTip("FlowNote - Ready")
        self.activated.connect(self._on_activated)
    
    def _create_icon(self, status: str):
        size = 24
        pixmap = QtGui.QPixmap(size, size)
        pixmap.fill(QtCore.Qt.transparent)
        
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        color = QtGui.QColor(self._colors.get(status, self._colors["idle"]))
        painter.setBrush(color)
        painter.drawEllipse(4, 4, 16, 16)
        
        painter.end()
        self.setIcon(QtGui.QIcon(pixmap))
    
    def _create_menu(self):
        menu = QtWidgets.QMenu()
        
        capture_clipboard_action = QtWidgets.QAction("📋 Capture Clipboard", menu)
        capture_clipboard_action.triggered.connect(self.capture_clipboard.emit)
        menu.addAction(capture_clipboard_action)
        
        capture_screenshot_action = QtWidgets.QAction("📷 Capture Screenshot", menu)
        capture_screenshot_action.triggered.connect(self.capture_screenshot.emit)
        menu.addSeparator()
        
        show_action = QtWidgets.QAction("Show Window", menu)
        show_action.triggered.connect(self.show_requested.emit)
        menu.addAction(show_action)
        
        menu.addSeparator()
        
        quit_action = QtWidgets.QAction("Quit", menu)
        quit_action.triggered.connect(self.quit_requested.emit)
        menu.addAction(quit_action)
        
        self.setContextMenu(menu)
    
    def _on_activated(self, reason):
        if reason == QtWidgets.QSystemTrayIcon.Trigger:
            self.clicked.emit()
        elif reason == QtWidgets.QSystemTrayIcon.DoubleClick:
            self.show_requested.emit()
    
    def set_status(self, status: str):
        status_lower = status.lower()
        self._current_status = status_lower
        self._create_icon(status_lower)
        
        tooltips = {
            "idle": "FlowNote - Ready",
            "capturing": "FlowNote - Capturing...",
            "processing": "FlowNote - Processing...",
            "saved": "FlowNote - Note Saved!",
            "error": "FlowNote - Error",
        }
        self.setToolTip(tooltips.get(status_lower, "FlowNote"))