"""
FlowNote - Status indicator widget and state management
"""

from enum import Enum
from PyQt5 import QtWidgets, QtCore, QtGui


class StatusState(Enum):
    IDLE = "Idle"
    CAPTURING = "Capturing"
    PROCESSING = "Processing"
    SAVED = "Saved"
    ERROR = "Error"


class StatusIndicator(QtWidgets.QWidget):
    """Status indicator showing current state with color"""
    
    state_changed = QtCore.pyqtSignal(str)
    
    _state_colors = {
        StatusState.IDLE: "#6B7280",
        StatusState.CAPTURING: "#3B82F6",
        StatusState.PROCESSING: "#F59E0B",
        StatusState.SAVED: "#10B981",
        StatusState.ERROR: "#EF4444",
    }
    
    _state_messages = {
        StatusState.IDLE: "Ready",
        StatusState.CAPTURING: "Capturing...",
        StatusState.PROCESSING: "Processing...",
        StatusState.SAVED: "Note saved!",
        StatusState.ERROR: "Error",
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._state = StatusState.IDLE
        self._error_message = ""
        self.setMinimumHeight(32)
        
        # Default styling
        self.setStyleSheet("""
            QWidget {
                background-color: #111827;
            }
        """)
    
    def set_state(self, state: StatusState, error_message: str = ""):
        if self._state != state:
            self._state = state
            self._error_message = error_message
            self.state_changed.emit(state.value)
            self.update()
    
    def get_state(self) -> StatusState:
        return self._state
    
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        color = QtGui.QColor(self._state_colors.get(self._state, "#6B7280"))
        painter.setBrush(color)
        
        h = self.height()
        circle_radius = min(h // 3, 10)
        circle_x = 16
        circle_y = h // 2
        
        painter.drawEllipse(circle_x - circle_radius, circle_y - circle_radius,
                           circle_radius * 2, circle_radius * 2)
        
        text = self._state_messages.get(self._state, "Unknown")
        if self._state == StatusState.ERROR and self._error_message:
            text = self._error_message[:30]
        
        font = QtGui.QFont("Segoe UI", 10)
        painter.setFont(font)
        painter.setPen(QtCore.Qt.white)
        painter.drawText(circle_x + circle_radius * 2 + 8, circle_y + 4, text)
    
    def minimumSizeHint(self):
        return QtCore.QSize(150, 32)
    
    def sizeHint(self):
        return QtCore.QSize(150, 32)