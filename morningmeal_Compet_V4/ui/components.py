import os
import sys
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QFrame, QDialog, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QTimer
from PyQt6.QtGui import QMouseEvent, QKeyEvent, QFocusEvent
from core.config_manager import config_mgr
from core.window_tracker import get_active_window_info, get_window_at_cursor, is_left_mouse_pressed
from core.i18n import I18n
from ui.theme import get_popup_menu_style


def format_time(seconds):
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


class WindowClickCaptureBridge(QObject):
    window_captured = pyqtSignal(str, bool)
    window_hovered = pyqtSignal(str)  # 커서 아래 창 실시간 미리보기용


capture_bridge = WindowClickCaptureBridge()
_capture_poll_timer: QTimer | None = None
_capture_elapsed_ms = 0
_was_mouse_down = False
_last_hovered_slot = ""


def _finish_capture(slot_str: str, is_cancelled: bool):
    global _capture_poll_timer, _capture_elapsed_ms, _was_mouse_down, _last_hovered_slot
    if _capture_poll_timer is None:
        return

    _capture_poll_timer.stop()
    _capture_poll_timer.deleteLater()
    _capture_poll_timer = None
    _capture_elapsed_ms = 0
    _was_mouse_down = False
    _last_hovered_slot = ""

    capture_bridge.window_captured.emit(slot_str, is_cancelled)


def _is_valid_target_window(win, my_pid: int) -> bool:
    if not win or win.pid == my_pid:
        return False
    title_l = (win.title or "").lower()
    app_l = (win.app_name or "").lower()
    if "morningmeal" in title_l or "morningmeal" in app_l:
        return False
    if app_l == "explorer.exe" and title_l in ("", "program manager"):
        return False
    return bool(win.format_slot_string())


def _poll_window_capture():
    global _capture_elapsed_ms, _was_mouse_down, _last_hovered_slot
    _capture_elapsed_ms += 50

    if _capture_elapsed_ms >= 15000:
        _finish_capture("", True)
        return

    # 버튼을 클릭한 직후 250ms 동안은 버튼 릴리즈 안정화 대기
    if _capture_elapsed_ms < 250:
        return

    my_pid = os.getpid()

    # 1) 커서 아래 창 실시간 감지 및 미리보기 시그널 발행
    pt_win = get_window_at_cursor()
    if _is_valid_target_window(pt_win, my_pid):
        slot = pt_win.format_slot_string()
        if slot != _last_hovered_slot:
            _last_hovered_slot = slot
            capture_bridge.window_hovered.emit(slot)

    # 2) 포그라운드 창이 다른 프로그램(VS Code, 게임 등)으로 전환되면 즉시 확정
    fg_win = get_active_window_info()
    if _is_valid_target_window(fg_win, my_pid):
        _finish_capture(fg_win.format_slot_string(), False)
        return

    # 3) 마우스 클릭(눌렀다 뗌) 시 커서 아래 창 확정
    is_down = is_left_mouse_pressed()
    if is_down:
        _was_mouse_down = True
    elif _was_mouse_down and not is_down:
        _was_mouse_down = False
        if _is_valid_target_window(pt_win, my_pid):
            _finish_capture(pt_win.format_slot_string(), False)
            return


def start_window_click_capture():
    global _capture_poll_timer, _capture_elapsed_ms, _was_mouse_down, _last_hovered_slot
    cancel_window_click_capture()

    _capture_elapsed_ms = 0
    _was_mouse_down = False
    _last_hovered_slot = ""

    _capture_poll_timer = QTimer(capture_bridge)
    _capture_poll_timer.setInterval(50)
    _capture_poll_timer.timeout.connect(_poll_window_capture)
    _capture_poll_timer.start()


def cancel_window_click_capture():
    _finish_capture("", True)

class CustomTitleBar(QWidget):
    theme_toggled = pyqtSignal()
    language_switched = pyqtSignal(str)

    def __init__(self, parent_window, title_key="app_title"):
        super().__init__(parent_window)
        self.parent_window = parent_window
        self.title_key = title_key
        self.setObjectName("titleBar")
        self.setFixedHeight(44)
        self.drag_start_pos = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 10, 0)
        layout.setSpacing(12)

        self.title_label = QLabel(I18n.tr(self.title_key))
        self.title_label.setObjectName("titleLabel")
        layout.addWidget(self.title_label)
        layout.addStretch()

        # 우측 상단 언어 선택 버튼
        self.lang_btn = QPushButton("Ko")
        self.lang_btn.setObjectName("titleBtn")
        self.lang_btn.setFixedSize(32, 24)
        self.lang_btn.clicked.connect(self.show_language_menu)
        layout.addWidget(self.lang_btn)

        # 우측 상단 다크/라이트 토글 버튼
        is_dark = config_mgr.config.get("settings", {}).get("dark_mode", False)
        self.theme_btn = QPushButton("light" if is_dark else "dark")
        self.theme_btn.setObjectName("titleBtn")
        self.theme_btn.setFixedSize(42, 24)
        self.theme_btn.clicked.connect(self.theme_toggled.emit)
        layout.addWidget(self.theme_btn)

        # 최소화 버튼 (macOS 프레임리스 창은 hide로 안전하게 숨김)
        self.min_btn = QPushButton("—")
        self.min_btn.setObjectName("titleBtn")
        self.min_btn.setFixedSize(24, 24)
        self.min_btn.clicked.connect(self._on_minimize_clicked)
        layout.addWidget(self.min_btn)

        self.close_btn = QPushButton("✕")
        self.close_btn.setObjectName("titleCloseBtn")
        self.close_btn.setFixedSize(24, 24)
        self.close_btn.clicked.connect(self.parent_window.hide)
        layout.addWidget(self.close_btn)

        self.retranslate_ui()
        I18n.language_changed.connect(self.retranslate_ui)

    def _on_minimize_clicked(self):
        if sys.platform == "darwin":
            self.parent_window.hide()
        else:
            self.parent_window.showMinimized()

    def show_language_menu(self):
        menu = StyledMenu(self)
        cur_lang = I18n.get_lang()
        langs = [
            ("한국어 (KO)", "ko"),
            ("English (EN)", "en"),
            ("日本語 (JA)", "ja"),
            ("简体中文", "zh_CN"),
            ("繁體中文", "zh_TW"),
        ]
        for name, code in langs:
            act = menu.addAction(name)
            act.setCheckable(True)
            if code == cur_lang:
                act.setChecked(True)
            act.triggered.connect(lambda checked, c=code: self._on_lang_selected(c))
        menu.exec(self.lang_btn.mapToGlobal(self.lang_btn.rect().bottomLeft()))

    def _on_lang_selected(self, lang_code: str):
        config_mgr.config.setdefault("settings", {})["language"] = lang_code
        config_mgr.save_config()
        I18n.set_language(lang_code)

    def retranslate_ui(self):
        self.title_label.setText(I18n.tr(self.title_key))
        cur = I18n.get_lang()
        mapping = {"ko": "Ko", "en": "En", "ja": "Ja", "zh_CN": "CN", "zh_TW": "TW"}
        self.lang_btn.setText(mapping.get(cur, "Ko"))

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
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Dialog
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedWidth(320)
        is_dark = config_mgr.config.get("settings", {}).get("dark_mode", False)

        if is_dark:
            bg, border = "#18181B", "#3B82F6"
            title_color, desc_color = "#FAFAFA", "#A1A1AA"
            cancel_color, cancel_hover = "#A1A1AA", "#60A5FA"
            ok_color = "#F87171" if is_danger else "#60A5FA"
            ok_hover = "#EF4444" if is_danger else "#93C5FD"
        else:
            bg, border = "#FFFFFF", "#0F4C81"
            title_color, desc_color = "#111827", "#4B5563"
            cancel_color, cancel_hover = "#6B7280", "#0F4C81"
            ok_color = "#E5989B" if is_danger else "#0F4C81"
            ok_hover = "#EF4444" if is_danger else "#2563EB"

        self.setStyleSheet(f"""
            QFrame#dialogCard {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 8px;
            }}
            QLabel {{
                background: transparent;
                border: none;
            }}
            QPushButton {{
                background: transparent;
                border: none;
                padding: 4px 8px;
                font-size: 13px;
                font-weight: 600;
                color: {cancel_color};
            }}
            QPushButton:hover {{
                color: {cancel_hover};
            }}
            QPushButton#okBtn {{
                color: {ok_color};
            }}
            QPushButton#okBtn:hover {{
                color: {ok_hover};
            }}
        """)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        card = QFrame()
        card.setObjectName("dialogCard")

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
        btn_box.setSpacing(12)
        btn_box.addStretch()

        btn_cancel = QPushButton(I18n.tr("cancel"))
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancel)

        btn_ok = QPushButton(I18n.tr("execute") if is_danger else I18n.tr("confirm"))
        btn_ok.setObjectName("okBtn")
        btn_ok.clicked.connect(self.accept)
        btn_box.addWidget(btn_ok)

        layout.addLayout(btn_box)
        outer.addWidget(card)


class AlertDialog(QDialog):
    def __init__(self, title_text, msg_text, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Dialog
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedWidth(320)

        is_dark = config_mgr.config.get("settings", {}).get("dark_mode", False)
        if is_dark:
            bg, border = "#18181B", "#3B82F6"
            title_color, desc_color = "#FAFAFA", "#A1A1AA"
            ok_color, ok_hover = "#60A5FA", "#93C5FD"
        else:
            bg, border = "#FFFFFF", "#0F4C81"
            title_color, desc_color = "#111827", "#4B5563"
            ok_color, ok_hover = "#0F4C81", "#2563EB"

        self.setStyleSheet(f"""
            QFrame#alertDialogCard {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 8px;
            }}
            QLabel {{
                background: transparent;
                border: none;
            }}
            QPushButton#okBtn {{
                background: transparent;
                border: none;
                padding: 4px 8px;
                font-size: 13px;
                font-weight: 600;
                color: {ok_color};
            }}
            QPushButton#okBtn:hover {{
                color: {ok_hover};
            }}
        """)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        card = QFrame()
        card.setObjectName("alertDialogCard")

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
        btn_box.addStretch()
        btn_ok = QPushButton(I18n.tr("confirm"))
        btn_ok.setObjectName("okBtn")
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

    def _stop_capture_ui(self):
        self.capturing = False
        self.setProperty("activeCapture", False)
        self.setText(self.raw_key if self.raw_key else I18n.tr("input_waiting"))
        self.style().unpolish(self)
        self.style().polish(self)

    def focusOutEvent(self, event: QFocusEvent):
        if self.capturing:
            self._stop_capture_ui()
        super().focusOutEvent(event)

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
        self._stop_capture_ui()
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
        self._stop_capture_ui()
        self.keyCaptured.emit(final_key)
        event.accept()

class StyledMenu(QMenu):
    """앱 전체(언어 선택, 위젯 우클릭, 트레이)에서 공통으로 사용하는 팝업 메뉴"""
    def __init__(self, title="", parent=None):
        if isinstance(title, QWidget) and parent is None:
            super().__init__(title)
        else:
            super().__init__(title, parent)
        self.setWindowFlags(
            self.windowFlags()
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.apply_theme()

    def apply_theme(self):
        is_dark = config_mgr.config.get("settings", {}).get("dark_mode", False)
        self.setStyleSheet(get_popup_menu_style(is_dark))

    def addStyledMenu(self, title: str):
        sub = StyledMenu(title, self)
        self.addMenu(sub)
        return sub