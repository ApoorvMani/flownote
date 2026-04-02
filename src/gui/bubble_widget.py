"""
FlowNote - BubbleWidget with modern UI and smooth animations
"""

import sys
from PyQt5 import QtWidgets, QtCore, QtGui
from threading import Thread
import time

from .status_indicator import StatusState
from src.processors.ai_processor import NoteStyles

class _CaptureCompleteEvent(QtCore.QEvent):
    """Custom event for capture completion"""
    EVENT_TYPE = QtCore.QEvent.User + 1
    
    def __init__(self, success: bool, note: str):
        super().__init__(self.EVENT_TYPE)
        self.success = success
        self.note = note

class BubbleWidget(QtWidgets.QWidget):
    """Floating bubble widget - draggable, expandable, beautifully animated"""
    
    # Signals
    clicked = QtCore.pyqtSignal(str)
    style_changed = QtCore.pyqtSignal(str)
    
    _STATE_COLORS = {
        "Idle": "#585B70",        # Subdued gray/blue
        "Capturing": "#89B4FA",   # Vibrant Blue
        "Processing": "#CBA6F7",  # Vibrant Purple
        "Saved": "#A6E3A1",       # Vibrant Green
        "Error": "#F38BA8",       # Vibrant Red
    }
    
    # Total widget sizes (including the 15px shadows on all sides)
    _COLLAPSED_SIZE = QtCore.QSize(80, 80)
    _EXPANDED_SIZE = QtCore.QSize(380, 260)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.expanded = False
        self.preview_text = ""
        self.status = "Idle"
        self._current_style = "concise"
        self._drag_start_pos = None
        self.offset = None
        
        self.setWindowFlags(
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.Tool
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setFixedSize(self._COLLAPSED_SIZE)
        
        self._setup_ui()
        self._setup_animations()
        self._move_to_bottom_right()
        self.installEventFilter(self)
        
    def _get_container_style(self, theme_color, is_expanded=False):
        radius = "14px" if is_expanded else "25px"
        return f"""
            #container {{
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1E1E2E, stop:1 #181825);
                border: 2px solid {theme_color};
                border-radius: {radius};
            }}
        """

    def _setup_ui(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15) # Room for shadows
        
        self.container = QtWidgets.QFrame(self)
        self.container.setObjectName("container")
        self.container.setStyleSheet(self._get_container_style(self._STATE_COLORS["Idle"]))
        
        shadow = QtWidgets.QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QtGui.QColor(0, 0, 0, 150))
        shadow.setOffset(0, 6)
        self.container.setGraphicsEffect(shadow)
        
        main_layout.addWidget(self.container)
        
        self.stack = QtWidgets.QStackedWidget(self.container)
        container_layout = QtWidgets.QVBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(self.stack)
        
        # --- 1. Collapsed View ---
        self.collapsed_widget = QtWidgets.QWidget()
        self.collapsed_widget.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        col_layout = QtWidgets.QVBoxLayout(self.collapsed_widget)
        col_layout.setContentsMargins(0, 0, 0, 0)
        
        self.logo_label = QtWidgets.QLabel("✦")
        self.logo_label.setAlignment(QtCore.Qt.AlignCenter)
        self.logo_label.setStyleSheet(f"color: {self._STATE_COLORS['Idle']}; font-size: 28px; font-weight: bold;")
        col_layout.addWidget(self.logo_label)
        self.stack.addWidget(self.collapsed_widget)
        
        # --- 2. Expanded View ---
        self.expanded_widget = QtWidgets.QWidget()
        exp_layout = QtWidgets.QVBoxLayout(self.expanded_widget)
        exp_layout.setContentsMargins(16, 16, 16, 16)
        exp_layout.setSpacing(12)
        
        # Header
        header_layout = QtWidgets.QHBoxLayout()
        header_layout.setContentsMargins(0,0,0,0)
        
        self.status_indicator = QtWidgets.QWidget()
        self.status_indicator.setFixedSize(10, 10)
        self.status_indicator.setStyleSheet(f"background-color: {self._STATE_COLORS['Idle']}; border-radius: 5px;")
        
        self.status_label = QtWidgets.QLabel("Ready")
        self.status_label.setStyleSheet(f"color: {self._STATE_COLORS['Idle']}; font-size: 13px; font-weight: bold; font-family: 'Segoe UI', Arial;")
        
        self.style_combo = QtWidgets.QComboBox()
        self.style_combo.addItems(NoteStyles.get_available_styles())
        self.style_combo.setCurrentText(self._current_style)
        self.style_combo.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.style_combo.setStyleSheet("""
            QComboBox {
                background-color: #313244;
                color: #CDD6F4;
                border: 1px solid #45475A;
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 11px;
                font-family: 'Segoe UI', Arial;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background-color: #1E1E2E;
                color: #CDD6F4;
                selection-background-color: #45475A;
            }
        """)
        self.style_combo.currentTextChanged.connect(self._on_style_changed)
        
        collapse_btn = QtWidgets.QPushButton("-")
        collapse_btn.setFixedSize(24, 24)
        collapse_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        collapse_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #A6ADC8;
                font-size: 18px;
                font-weight: bold;
                border-radius: 12px;
            }
            QPushButton:hover { background-color: #313244; color: #CDD6F4; }
        """)
        collapse_btn.clicked.connect(self.toggle_expand)
        
        header_layout.addWidget(self.status_indicator)
        header_layout.addWidget(self.status_label)
        header_layout.addStretch()
        header_layout.addWidget(self.style_combo)
        header_layout.addSpacing(5)
        header_layout.addWidget(collapse_btn)
        
        # Preview Text
        self.preview = QtWidgets.QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setStyleSheet("""
            QTextEdit {
                background-color: #11111B;
                color: #CDD6F4;
                border: 1px solid #313244;
                border-radius: 8px;
                padding: 10px;
                font-size: 13px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QScrollBar:vertical {
                background: #1E1E2E;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #45475A;
                border-radius: 4px;
            }
        """)
        
        # Actions
        actions_layout = QtWidgets.QHBoxLayout()
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(10)
        
        self.capture_btn = self._create_action_button("📋 Capture Clipboard", "#89B4FA", "#B4BEFE", "#11111B")
        self.capture_btn.clicked.connect(lambda: self.clicked.emit("clipboard"))
        
        self.screenshot_btn = self._create_action_button("📷 Screenshot OCR", "#45475A", "#585B70", "#CDD6F4")
        self.screenshot_btn.clicked.connect(lambda: self.clicked.emit("screenshot"))
        
        actions_layout.addWidget(self.capture_btn)
        actions_layout.addWidget(self.screenshot_btn)
        
        exp_layout.addLayout(header_layout)
        exp_layout.addWidget(self.preview)
        exp_layout.addLayout(actions_layout)
        
        self.stack.addWidget(self.expanded_widget)
        self.stack.setCurrentIndex(0)

    def _create_action_button(self, text, bg_color, hover_color, text_color):
        btn = QtWidgets.QPushButton(text)
        btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        btn.setFixedHeight(34)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color};
                color: {text_color};
                border: none;
                border-radius: 8px;
                font-size: 12px;
                font-family: 'Segoe UI', Arial;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {hover_color}; }}
            QPushButton:pressed {{ background-color: #CDD6F4; color: #11111B; }}
        """)
        return btn

    def _setup_animations(self):
        self.anim = QtCore.QPropertyAnimation(self, b"geometry")
        self.anim.setEasingCurve(QtCore.QEasingCurve.InOutQuart)
        self.anim.setDuration(350)
        self.anim.finished.connect(self._on_animation_finished)

    def eventFilter(self, obj, event):
        if event.type() == _CaptureCompleteEvent.EVENT_TYPE:
            self._on_capture_complete(event.success, event.note)
            return True
        return super().eventFilter(obj, event)

    def _on_capture_complete(self, success: bool, note: str):
        if success:
            preview = note[:120] + "..." if len(note) > 120 else note
            self.update_preview("Saved", preview)
        else:
            self.update_preview("Error", note)
            
    def _move_to_bottom_right(self):
        screen = QtWidgets.QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = geo.right() - self._COLLAPSED_SIZE.width() - 20
            y = geo.bottom() - self._COLLAPSED_SIZE.height() - 20
            self.move(x, y)

    def _on_style_changed(self, style):
        self._current_style = style
        self.style_changed.emit(style)

    # Mouse Events for dragging / clicking
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self._drag_start_pos = event.globalPos()
            self.offset = event.pos()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.offset is not None and event.buttons() == QtCore.Qt.LeftButton:
            delta = (event.globalPos() - self._drag_start_pos).manhattanLength()
            if delta > 5:
                # Disable animation during drag
                self.move(self.mapToGlobal(event.pos() - self.offset))
                self._ensure_on_screen()
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            delta = (event.globalPos() - self._drag_start_pos).manhattanLength() if self._drag_start_pos else 0
            if delta < 10 and not self.expanded:
                # If collapsed and lightly clicked, expand
                self.toggle_expand()
            self.offset = None
            self._drag_start_pos = None
            event.accept()

    def _ensure_on_screen(self):
        screen = QtWidgets.QApplication.screenAt(self.geometry().center())
        if not screen:
            screen = QtWidgets.QApplication.primaryScreen()
        geo = screen.availableGeometry()
        x = max(geo.left(), min(self.x(), geo.right() - self.width()))
        y = max(geo.top(), min(self.y(), geo.bottom() - self.height()))
        self.move(x, y)

    def _get_target_geometry(self, target_size):
        screen = QtWidgets.QApplication.screenAt(self.geometry().center())
        if not screen:
            screen = QtWidgets.QApplication.primaryScreen()
        screen_geo = screen.availableGeometry()
        c = self.geometry().center()
        
        tw = target_size.width()
        th = target_size.height()
        
        right_anchored = c.x() > screen_geo.center().x()
        bottom_anchored = c.y() > screen_geo.center().y()
        
        start_geo = self.geometry()
        
        new_x = start_geo.right() - tw + 1 if right_anchored else start_geo.left()
        new_y = start_geo.bottom() - th + 1 if bottom_anchored else start_geo.top()
        
        return QtCore.QRect(new_x, new_y, tw, th)

    def toggle_expand(self):
        if self.expanded:
            self._collapse()
        else:
            self._expand()
        self.expanded = not self.expanded

    def _expand(self):
        self.stack.setCurrentIndex(1)
        self.setFixedSize(self._EXPANDED_SIZE) # Needs to accommodate the new animated sizes
        self.setMinimumSize(self._COLLAPSED_SIZE)
        self.setMaximumSize(10000, 10000)
        
        start_geo = self.geometry()
        end_geo = self._get_target_geometry(self._EXPANDED_SIZE)
        
        self.anim.setStartValue(start_geo)
        self.anim.setEndValue(end_geo)
        
        color = self._STATE_COLORS.get(self.status, self._STATE_COLORS["Idle"])
        self.container.setStyleSheet(self._get_container_style(color, True))
        
        self.anim.start()

    def _collapse(self):
        self.stack.setCurrentIndex(0)
        self.setMinimumSize(self._COLLAPSED_SIZE)
        self.setMaximumSize(10000, 10000)
        
        start_geo = self.geometry()
        end_geo = self._get_target_geometry(self._COLLAPSED_SIZE)
        
        self.anim.setStartValue(start_geo)
        self.anim.setEndValue(end_geo)
        
        color = self._STATE_COLORS.get(self.status, self._STATE_COLORS["Idle"])
        self.container.setStyleSheet(self._get_container_style(color, False))
        
        self.anim.start()

    def _on_animation_finished(self):
        target_size = self._EXPANDED_SIZE if self.expanded else self._COLLAPSED_SIZE
        self.setFixedSize(target_size)
        self._ensure_on_screen()

    def update_preview(self, status, text=""):
        self.status = status
        color = self._STATE_COLORS.get(status, self._STATE_COLORS["Idle"])
        
        self.logo_label.setStyleSheet(f"color: {color}; font-size: 28px; font-weight: bold;")
        self.status_indicator.setStyleSheet(f"background-color: {color}; border-radius: 5px;")
        
        if text:
            self.preview_text = text
            
        is_exp = self.expanded
        self.container.setStyleSheet(self._get_container_style(color, is_exp))
        
        # In expanded text area, format cleanly not redundantly showing Status
        self.preview.setText(self.preview_text if self.preview_text else "No content yet.")
        self.status_label.setText(status.upper())
        self.status_label.setStyleSheet(f"color: {color}; font-size: 11px; font-weight: bold; font-family: 'Segoe UI', Arial;")

    def expand(self):
        if not self.expanded:
            self.toggle_expand()

    def collapse(self):
        if self.expanded:
            self.toggle_expand()

    def is_expanded(self):
        return self.expanded

    def set_status(self, status):
        status_str = status.value if hasattr(status, 'value') else str(status)
        self.update_preview(status_str, self.preview_text)
        
    def set_preview(self, text):
        self.preview_text = text
        self.update_preview(self.status, text)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    bubble = BubbleWidget()
    bubble.show()
    sys.exit(app.exec_())