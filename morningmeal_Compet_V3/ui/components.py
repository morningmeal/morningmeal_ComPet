# ui/components.py
import sys
import time
from pynput import mouse
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QLineEdit,
    QFrame, QDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QMouseEvent, QKeyEvent
from core.config_manager import config_mgr
from core.window_tracker import get_active_window_info
from core.i18n import I18n

def format_time(seconds):
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

class WindowClickCaptureBridge(QObject):
    window_captured = pyqtSignal(str)

capture_bridge = WindowClickCaptureBridge()
active_picker_listener = None

def start_window_click_capture():
    global active_picker_listener
    if active_picker_listener and active_picker_listener.is_alive():
        active_picker_listener.stop()

    def on_click(x, y, button, pressed):
        if not pressed:
            time.sleep(0.08)
            win = get_active_window_info()
            title = win.title.strip() if win else ""
            if title and "morningmeal" not in title.lower():
                capture_bridge.window_captured.emit(title)
                return False
        return True

    active_picker_listener = mouse.Listener(on_click=on_click)
    active_picker_listener.daemon = True
    active_picker_listener.start()

def cancel_window_click_capture():
    global active_picker_listener
    if active_picker_listener and active_picker_listener.is_alive():
        active_picker_listener.stop()
        active_picker_listener = None

class CustomTitleBar(QWidget):
    theme_toggled = pyqtSignal()

    def __init__(self, parent_window, title_key="app_title"):
        super().__init__(parent_window)
        self.parent_window = parent_window
        self.title_key = title_key
        self.setObjectName("titleBar")
        self.setFixedHeight(40)
        self.drag_start_pos = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 10, 0)
        layout.setSpacing(8)

        self.title_label = QLabel(I18n.tr(self.title_key))
        self.title_label.setObjectName("titleLabel")
        layout.addWidget(self.title_label)
        layout.addStretch()

        self.theme_btn = QPushButton("Mode")
        self.theme_btn.setObjectName("titleBtn")
        self.theme_btn.setFixedSize(54, 24)
        self.theme_btn.clicked.connect(self.theme_toggled.emit)
        layout.addWidget(self.theme_btn)

        self.min_btn = QPushButton("–")
        self.min_btn.setObjectName("titleBtn")
        self.min_btn.setFixedSize(28, 24)
        self.min_btn.clicked.connect(self.parent_window.showMinimized)
        layout.addWidget(self.min_btn)

        self.close_btn = QPushButton("✕")
        self.close_btn.setObjectName("titleCloseBtn")
        self.close_btn.setFixedSize(28, 24)
        self.close_btn.clicked.connect(self.parent_window.hide)
        layout.addWidget(self.close_btn)

        I18n.language_changed.connect(self.retranslate_ui)

    def retranslate_ui(self):
        self.title_label.setText(I18n.tr(self.title_key))

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_pos = event.globalPosition().toPoint() - self.parent_window.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.drag_start_pos and event.buttons() == Qt.MouseButton.LeftButton:
            self.parent_window.move(event.globalPosition().toPoint() - self.drag_start_pos)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.drag_start_pos = None
        event.accept()

class ConfirmDialog(QDialog):
    def __init__(self, title_text, msg_text, is_danger=False, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedWidth(320)
        is_dark = config_mgr.config.get("settings", {}).get("dark_mode", False)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        card = QFrame()
        card.setObjectName("dialogCard")

        if is_dark:
            card.setStyleSheet("QFrame#dialogCard { background-color: #18181B; border: 1px solid #3F3F46; border-radius: 10px; }")
            title_color, desc_color = "#FAFAFA", "#A1A1AA"
            cancel_btn_style = "QPushButton { background-color: #27272A; border: 1px solid #3F3F46; border-radius: 6px; color: #F4F4F5; font-weight: 500; padding: 6px 14px; } QPushButton:hover { background-color: #3F3F46; }"
        else:
            card.setStyleSheet("QFrame#dialogCard { background-color: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 10px; }")
            title_color, desc_color = "#111827", "#4B5563"
            cancel_btn_style = "QPushButton { background-color: #F3F4F6; border: 1px solid #E5E7EB; border-radius: 6px; color: #1F2937; font-weight: 500; padding: 6px 14px; } QPushButton:hover { background-color: #E5E7EB; }"

        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 18, 18, 16)
        layout.setSpacing(10)

        lbl_title = QLabel(title_text)
        lbl_title.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {title_color};")
        layout.addWidget(lbl_title)

        lbl_msg = QLabel(msg_text)
        lbl_msg.setWordWrap(True)
        lbl_msg.setStyleSheet(f"font-size: 12px; color: {desc_color}; line-height: 1.4;")
        layout.addWidget(lbl_msg)

        btn_box = QHBoxLayout()
        btn_box.setSpacing(8)
        btn_box.addStretch()

        btn_cancel = QPushButton("취소" if I18n.get_lang() == "ko" else "Cancel")
        btn_cancel.setFixedHeight(32)
        btn_cancel.setStyleSheet(cancel_btn_style)
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancel)

        btn_ok = QPushButton("실행" if is_danger else ("확인" if I18n.get_lang() == "ko" else "OK"))
        btn_ok.setFixedHeight(32)
        btn_ok.setStyleSheet("QPushButton { background-color: " + ("#DC2626" if is_danger else "#2563EB") + "; border: none; border-radius: 6px; color: #FFFFFF; font-weight: 600; padding: 6px 16px; }")
        btn_ok.clicked.connect(self.accept)
        btn_box.addWidget(btn_ok)

        layout.addLayout(btn_box)
        outer.addWidget(card)

class AlertDialog(QDialog):
    """확인 버튼만 단일 배치된 모던 경고/안내 팝업창"""
    def __init__(self, title_text, msg_text, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedWidth(320)

        is_dark = config_mgr.config.get("settings", {}).get("dark_mode", False)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        card = QFrame()
        card.setObjectName("alertDialogCard")
        
        if is_dark:
            card.setStyleSheet("""
                QFrame#alertDialogCard {
                    background-color: #18181B;
                    border: 1px solid #3F3F46;
                    border-radius: 10px;
                }
            """)
            title_color = "#FAFAFA"
            desc_color = "#A1A1AA"
        else:
            card.setStyleSheet("""
                QFrame#alertDialogCard {
                    background-color: #FFFFFF;
                    border: 1px solid #E5E7EB;
                    border-radius: 10px;
                }
            """)
            title_color = "#111827"
            desc_color = "#4B5563"

        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 18, 18, 16)
        layout.setSpacing(10)

        lbl_title = QLabel(title_text)
        lbl_title.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {title_color};")
        layout.addWidget(lbl_title)

        lbl_msg = QLabel(msg_text)
        lbl_msg.setWordWrap(True)
        lbl_msg.setStyleSheet(f"font-size: 12px; color: {desc_color}; line-height: 1.4;")
        layout.addWidget(lbl_msg)

        layout.addSpacing(6)

        btn_box = QHBoxLayout()
        btn_box.addStretch()

        btn_ok = QPushButton(I18n.tr("complete") if hasattr(I18n, 'tr') else "OK")
        btn_ok.setFixedHeight(32)
        btn_ok.setStyleSheet("""
            QPushButton {
                background-color: #2563EB;
                border: none;
                border-radius: 6px;
                color: #FFFFFF;
                font-weight: 600;
                padding: 6px 18px;
            }
            QPushButton:hover { background-color: #1D4ED8; }
            QPushButton:pressed { background-color: #1E40AF; }
        """)
        btn_ok.clicked.connect(self.accept)
        btn_box.addWidget(btn_ok)

        layout.addLayout(btn_box)
        outer.addWidget(card)

class KeyCaptureButton(QPushButton):
    keyCaptured = pyqtSignal(str)

    def __init__(self, text="", parent=None):
        waiting_text = I18n.tr("input_waiting")
        self.raw_key = text if (text and text != waiting_text) else ""
        super().__init__(self.raw_key or waiting_text, parent)
        self.capturing = False
        I18n.language_changed.connect(self.retranslate_ui)

    def retranslate_ui(self):
        if not self.raw_key:
            self.setText(I18n.tr("input_detecting") if self.capturing else I18n.tr("input_waiting"))

    def mousePressEvent(self, event: QMouseEvent):
        if not self.capturing:
            self.capturing = True
            self.setText(I18n.tr("input_detecting"))
            self.setProperty("activeCapture", True)
            self.style().unpolish(self)
            self.style().polish(self)
            self.setFocus()
            event.accept()
            return

        btn = event.button()
        k_name = "mouse_left" if btn == Qt.MouseButton.LeftButton else ("mouse_right" if btn == Qt.MouseButton.RightButton else "mouse_middle")
        self.raw_key = k_name
        self.setText(k_name)
        self.capturing = False
        self.setProperty("activeCapture", False)
        self.style().unpolish(self)
        self.style().polish(self)
        self.keyCaptured.emit(k_name)
        event.accept()

    def keyPressEvent(self, event: QKeyEvent):
        if not self.capturing:
            super().keyPressEvent(event)
            return

        key = event.key()
        modifiers = event.modifiers()
        if key in (Qt.Key.Key_Shift, Qt.Key.Key_Control, Qt.Key.Key_Alt, Qt.Key.Key_Meta):
            event.accept()
            return

        text = event.text().strip()
        is_shift = bool(modifiers & Qt.KeyboardModifier.ShiftModifier)
        is_ctrl = bool(modifiers & Qt.KeyboardModifier.ControlModifier)
        is_alt = bool(modifiers & Qt.KeyboardModifier.AltModifier)

        key_names = {
            Qt.Key.Key_Space: "space", Qt.Key.Key_Return: "enter", Qt.Key.Key_Enter: "enter",
            Qt.Key.Key_Tab: "tab", Qt.Key.Key_Backspace: "backspace", Qt.Key.Key_Escape: "esc",
            Qt.Key.Key_Left: "left", Qt.Key.Key_Right: "right", Qt.Key.Key_Up: "up", Qt.Key.Key_Down: "down"
        }
        base = key_names.get(key, text.lower() if text else f"key_{key}")

        mod_parts = []
        if modifiers & Qt.KeyboardModifier.MetaModifier:
            mod_parts.append("cmd" if sys.platform == "darwin" else "win")
        if is_ctrl: mod_parts.append("ctrl")
        if is_alt: mod_parts.append("alt")
        if is_shift: mod_parts.append("shift")

        final_key = "+".join(mod_parts) + "+" + base if mod_parts else base
        self.raw_key = final_key
        self.setText(final_key)
        self.capturing = False
        self.setProperty("activeCapture", False)
        self.style().unpolish(self)
        self.style().polish(self)
        self.keyCaptured.emit(final_key)
        event.accept()