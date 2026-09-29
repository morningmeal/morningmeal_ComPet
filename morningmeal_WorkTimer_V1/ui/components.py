from pynput import mouse
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QLineEdit,
    QSpinBox, QComboBox, QFrame, QMessageBox, QAbstractSpinBox, QDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QMouseEvent
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
            import time
            time.sleep(0.08)
            win = get_active_window_info()
            title = win.title.strip() if win else ""
            if title and "Morningmeal" not in title:
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


class TimerCardWidget(QFrame):
    changed = pyqtSignal()

    def __init__(self, timer_data, remove_callback, parent=None):
        super().__init__(parent)
        self.timer_data = timer_data
        self.remove_callback = remove_callback
        self.setFixedWidth(240)
        self.update_card_style()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        # 상단 이름 & 삭제 버튼
        top_layout = QHBoxLayout()
        self.name_edit = QLineEdit(self.timer_data.get("name", I18n.tr("default_timer_name")))
        self.name_edit.setFixedHeight(28)
        self.name_edit.textChanged.connect(self.on_name_changed)
        top_layout.addWidget(self.name_edit, 1)

        del_btn = QPushButton("✕")
        del_btn.setFixedSize(24, 24)
        del_btn.setStyleSheet("""
            QPushButton { border: none; background: transparent; font-size: 11px; color: #94A3B8; padding: 0; }
            QPushButton:hover { color: #EF4444; }
        """)
        del_btn.clicked.connect(lambda: self.remove_callback(self.timer_data))
        top_layout.addWidget(del_btn)
        layout.addLayout(top_layout)

    # 그룹 배정 영역 (그룹 0개 대응)
        group_layout = QHBoxLayout()
        self.lbl_g = QLabel(I18n.tr("group_label"))
        self.lbl_g.setStyleSheet("color: #64748B; font-size: 11px;")
        
        self.group_combo = QComboBox()
        self.group_combo.setFixedHeight(28)
        
        groups = list(config_mgr.config.get("groups", {}).keys())
        if groups:
            self.group_combo.setEnabled(True)
            self.group_combo.addItems(groups)
            cur_group = self.timer_data.get("group", "")
            if cur_group in groups:
                self.group_combo.setCurrentText(cur_group)
            else:
                self.timer_data["group"] = groups[0]
                self.group_combo.setCurrentText(groups[0])
        else:
            # 등록된 그룹이 0개인 경우
            self.group_combo.setEnabled(False)
            self.group_combo.addItem(I18n.tr("no_group_available"))
            self.timer_data["group"] = ""

        self.group_combo.currentTextChanged.connect(self.on_group_changed)
        group_layout.addWidget(self.lbl_g)
        group_layout.addWidget(self.group_combo, 1)
        layout.addLayout(group_layout)

        # ★ 유휴시간 설정: 버튼(화살표) 없이 숫자만 입력받는 컴팩트 인풋 형태[cite: 5]
        idle_layout = QHBoxLayout()
        self.lbl_i = QLabel(I18n.tr("idle_label"))
        self.lbl_i.setStyleSheet("color: #64748B; font-size: 11px;")
        
        self.idle_spin = QSpinBox()
        self.idle_spin.setFixedHeight(28)
        self.idle_spin.setRange(1, 999)
        self.idle_spin.setValue(self.timer_data.get("idle_timeout", 5))
        self.idle_spin.setSuffix(f" {I18n.tr('unit_seconds')}")
        self.idle_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.idle_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)  # 화살표 버튼 제거[cite: 5]
        self.idle_spin.setStyleSheet("""
            QSpinBox {
                font-weight: 600;
                padding: 2px 6px;
            }
        """)
        self.idle_spin.valueChanged.connect(self.on_idle_changed)
        
        idle_layout.addWidget(self.lbl_i)
        idle_layout.addWidget(self.idle_spin, 1)
        layout.addLayout(idle_layout)

        # 시간 표시 및 리셋
        time_layout = QHBoxLayout()
        self.time_label = QLabel(format_time(self.timer_data.get("elapsed_seconds", 0)))
        self.time_label.setStyleSheet("font-weight: bold; font-family: monospace; font-size: 15px; color: #2563EB;")
        time_layout.addWidget(self.time_label)

        time_layout.addStretch()
        self.btn_reset = QPushButton(I18n.tr("reset"))
        self.btn_reset.setFixedHeight(26)
        self.btn_reset.clicked.connect(self.reset_time)
        time_layout.addWidget(self.btn_reset)
        layout.addLayout(time_layout)

        I18n.language_changed.connect(self.retranslate_ui)

    def retranslate_ui(self):
        self.lbl_g.setText(I18n.tr("group_label"))
        self.lbl_i.setText(I18n.tr("idle_label"))
        self.idle_spin.setSuffix(f" {I18n.tr('unit_seconds')}")
        self.btn_reset.setText(I18n.tr("reset"))

    def update_card_style(self):
        is_dark = config_mgr.config.get("settings", {}).get("dark_mode", False)
        if is_dark:
            self.setStyleSheet("""
                TimerCardWidget { background-color: #27272A; border: 1px solid #3F3F46; border-radius: 8px; }
                TimerCardWidget:hover { border-color: #3B82F6; }
            """)
        else:
            self.setStyleSheet("""
                TimerCardWidget { background-color: #FFFFFF; border: 1px solid #D0D7DE; border-radius: 8px; }
                TimerCardWidget:hover { border-color: #93C5FD; }
            """)

    def on_name_changed(self, txt):
        self.timer_data["name"] = txt
        config_mgr.save_config()
        self.changed.emit()

    def on_group_changed(self, txt):
        # 안내 문구이거나 비어있으면 저장하지 않음
        if not txt or txt == I18n.tr("no_group_available"):
            self.timer_data["group"] = ""
        else:
            self.timer_data["group"] = txt
        config_mgr.save_config()
        self.changed.emit()

    def on_idle_changed(self, val):
        self.timer_data["idle_timeout"] = val
        config_mgr.save_config()

    def reset_time(self):
        reply = QMessageBox.question(
            self,
            I18n.tr("reset_confirm_title"),
            I18n.tr("reset_confirm_msg"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.timer_data["elapsed_seconds"] = 0
            self.time_label.setText(format_time(0))
            config_mgr.save_config()
            self.changed.emit()


class GroupCardWidget(QFrame):
    changed = pyqtSignal()

    def __init__(self, group_name, windows, remove_group_callback, parent=None):
        super().__init__(parent)
        self.group_name = group_name
        self.windows = (windows + ["", "", ""])[:3]
        self.remove_group_callback = remove_group_callback
        self.current_capturing_btn = None

        self.update_card_style()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        header = QHBoxLayout()
        self.title_label = QLabel(f"{self.group_name}")
        self.title_label.setStyleSheet("font-weight: 600; font-size: 13px;")
        header.addWidget(self.title_label)
        header.addStretch()

        self.del_btn = QPushButton(I18n.tr("del_group"))
        self.del_btn.setFixedHeight(24)
        self.del_btn.setStyleSheet("""
            QPushButton { font-size: 11px; padding: 2px 8px; color: #EF4444; }
            QPushButton:hover { background-color: #EF4444; color: white; }
        """)
        self.del_btn.clicked.connect(lambda: self.remove_group_callback(self.group_name))
        header.addWidget(self.del_btn)
        layout.addLayout(header)

        self.slot_labels = []
        self.slot_edits = []
        self.slot_pick_btns = []
        self.slot_clear_btns = []

        for i in range(3):
            slot_h = QHBoxLayout()
            slot_h.setSpacing(6)
            slot_label = QLabel(f"{I18n.tr('slot')} {i+1}:")
            slot_label.setFixedWidth(46)
            slot_label.setStyleSheet("color: #64748B; font-size: 11px;")
            self.slot_labels.append(slot_label)

            line_edit = QLineEdit(self.windows[i])
            line_edit.setFixedHeight(28)
            line_edit.setPlaceholderText(I18n.tr("slot_placeholder"))
            line_edit.textChanged.connect(lambda txt, idx=i: self.on_slot_text_changed(idx, txt))
            self.slot_edits.append(line_edit)

            btn_pick = QPushButton(I18n.tr("pick_window"))
            btn_pick.setFixedHeight(28)
            btn_pick.setFixedWidth(106)
            btn_pick.clicked.connect(lambda _, b=btn_pick, le=line_edit, idx=i: self.start_capture(b, le, idx))
            self.slot_pick_btns.append(btn_pick)

            btn_clear = QPushButton(I18n.tr("clear"))
            btn_clear.setFixedHeight(28)
            btn_clear.setFixedWidth(54)
            btn_clear.clicked.connect(lambda _, le=line_edit, idx=i: self.clear_slot(le, idx))
            self.slot_clear_btns.append(btn_clear)

            slot_h.addWidget(slot_label)
            slot_h.addWidget(line_edit, 1)
            slot_h.addWidget(btn_pick)
            slot_h.addWidget(btn_clear)
            layout.addLayout(slot_h)

        capture_bridge.window_captured.connect(self.on_window_captured)
        I18n.language_changed.connect(self.retranslate_ui)

    def retranslate_ui(self):
        self.del_btn.setText(I18n.tr("del_group"))
        for i, lbl in enumerate(self.slot_labels):
            lbl.setText(f"{I18n.tr('slot')} {i+1}:")
        for le in self.slot_edits:
            le.setPlaceholderText(I18n.tr("slot_placeholder"))
        for btn in self.slot_pick_btns:
            if not getattr(btn, 'is_capturing', False):
                btn.setText(I18n.tr("pick_window"))
            else:
                btn.setText(I18n.tr("waiting_click"))
        for btn in self.slot_clear_btns:
            btn.setText(I18n.tr("clear"))

    def update_card_style(self):
        is_dark = config_mgr.config.get("settings", {}).get("dark_mode", False)
        if is_dark:
            self.setStyleSheet("""
                GroupCardWidget { background-color: #27272A; border: 1px solid #3F3F46; border-radius: 8px; }
                GroupCardWidget:hover { border-color: #3B82F6; }
            """)
        else:
            self.setStyleSheet("""
                GroupCardWidget { background-color: #FFFFFF; border: 1px solid #D0D7DE; border-radius: 8px; }
                GroupCardWidget:hover { border-color: #93C5FD; }
            """)

    def on_slot_text_changed(self, idx, txt):
        self.windows[idx] = txt.strip()
        config_mgr.config["groups"][self.group_name] = [w for w in self.windows if w]
        config_mgr.save_config()

    def start_capture(self, btn, line_edit, idx):
        if getattr(btn, 'is_capturing', False):
            self.reset_capture_btn(btn)
            cancel_window_click_capture()
            return

        if self.current_capturing_btn:
            self.reset_capture_btn(self.current_capturing_btn)

        self.current_capturing_btn = btn
        self.current_capturing_target = (line_edit, idx)
        btn.is_capturing = True
        btn.setText(I18n.tr("waiting_click"))
        btn.setProperty("activeCapture", True)
        btn.style().unpolish(btn)
        btn.style().polish(btn)

        start_window_click_capture()

    def on_window_captured(self, title):
        if self.current_capturing_btn and hasattr(self, 'current_capturing_target'):
            le, idx = self.current_capturing_target
            le.setText(title)
            self.on_slot_text_changed(idx, title)
            self.reset_capture_btn(self.current_capturing_btn)
            self.current_capturing_btn = None

    def reset_capture_btn(self, btn):
        btn.is_capturing = False
        btn.setText(I18n.tr("pick_window"))
        btn.setProperty("activeCapture", False)
        btn.style().unpolish(btn)
        btn.style().polish(btn)

    def clear_slot(self, line_edit, idx):
        line_edit.clear()
        self.on_slot_text_changed(idx, "")

class ConfirmDialog(QDialog):
    """컴펫 스타일의 커스텀 모던 확인 팝업창"""
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
            card.setStyleSheet("""
                QFrame#dialogCard {
                    background-color: #18181B;
                    border: 1px solid #3F3F46;
                    border-radius: 10px;
                }
            """)
            title_color = "#FAFAFA"
            desc_color = "#A1A1AA"
            cancel_btn_style = """
                QPushButton {
                    background-color: #27272A;
                    border: 1px solid #3F3F46;
                    border-radius: 6px;
                    color: #F4F4F5;
                    font-weight: 500;
                    padding: 6px 14px;
                }
                QPushButton:hover { background-color: #3F3F46; }
            """
        else:
            card.setStyleSheet("""
                QFrame#dialogCard {
                    background-color: #FFFFFF;
                    border: 1px solid #E5E7EB;
                    border-radius: 10px;
                }
            """)
            title_color = "#111827"
            desc_color = "#4B5563"
            cancel_btn_style = """
                QPushButton {
                    background-color: #F3F4F6;
                    border: 1px solid #E5E7EB;
                    border-radius: 6px;
                    color: #1F2937;
                    font-weight: 500;
                    padding: 6px 14px;
                }
                QPushButton:hover { background-color: #E5E7EB; }
            """

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
        btn_box.setSpacing(8)
        btn_box.addStretch()

        # 취소 버튼
        btn_cancel = QPushButton("취소" if I18n.get_lang() == "ko" else "Cancel")
        btn_cancel.setFixedHeight(32)
        btn_cancel.setStyleSheet(cancel_btn_style)
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancel)

        # 확인/실행 버튼
        btn_ok = QPushButton("종료" if is_danger else ("확인" if I18n.get_lang() == "ko" else "OK"))
        btn_ok.setFixedHeight(32)
        if is_danger:
            btn_ok.setStyleSheet("""
                QPushButton {
                    background-color: #DC2626;
                    border: none;
                    border-radius: 6px;
                    color: #FFFFFF;
                    font-weight: 600;
                    padding: 6px 16px;
                }
                QPushButton:hover { background-color: #B91C1C; }
                QPushButton:pressed { background-color: #991B1B; }
            """)
        else:
            btn_ok.setStyleSheet("""
                QPushButton {
                    background-color: #2563EB;
                    border: none;
                    border-radius: 6px;
                    color: #FFFFFF;
                    font-weight: 600;
                    padding: 6px 16px;
                }
                QPushButton:hover { background-color: #1D4ED8; }
            """)
        btn_ok.clicked.connect(self.accept)
        btn_box.addWidget(btn_ok)

        layout.addLayout(btn_box)
        outer.addWidget(card)

class AlertDialog(QDialog):
    """컴펫 스타일의 커스텀 경고/오류 팝업창 (확인 버튼 단일 구성)"""
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

        btn_ok = QPushButton("확인" if I18n.get_lang() == "ko" else "OK")
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