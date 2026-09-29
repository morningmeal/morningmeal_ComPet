# ui/settings/tab_timer.py
import uuid
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QScrollArea,
    QPushButton, QLabel, QLineEdit, QCheckBox, QComboBox, QFrame,
    QSpinBox, QAbstractSpinBox, QTabWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from core.config_manager import config_mgr
from core.i18n import I18n
from core.activity_engine import activity_engine
from ui.components import (
    ConfirmDialog, AlertDialog, capture_bridge, 
    start_window_click_capture, cancel_window_click_capture, format_time
)

class TimerCardWidget(QFrame):
    changed = pyqtSignal()
    name_updated = pyqtSignal(str, str)  # (timer_id, new_name) -> 경량 실시간 이름 반영

    def __init__(self, timer_data, remove_callback, parent=None):
        super().__init__(parent)
        self.timer_data = timer_data
        self.remove_callback = remove_callback
        self.setFixedWidth(260)
        self.update_card_style()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        # 상단 이름 & 삭제 버튼
        top_layout = QHBoxLayout()
        self.name_edit = QLineEdit(self.timer_data.get("name", I18n.tr("default_timer_name")))
        self.name_edit.setFixedHeight(28)
        
        # 키 입력 중에는 가볍게 이름만 실시간 갱신, 입력 완료 시 저장 및 전체 동기화
        self.name_edit.textChanged.connect(self.on_name_text_changed)
        self.name_edit.editingFinished.connect(self.on_name_editing_finished)
        top_layout.addWidget(self.name_edit, 1)

        del_btn = QPushButton("✕")
        del_btn.setFixedSize(24, 24)
        del_btn.setStyleSheet("QPushButton { border: none; background: transparent; font-size: 11px; color: #94A3B8; } QPushButton:hover { color: #EF4444; }")
        del_btn.clicked.connect(lambda: self.remove_callback(self.timer_data))
        top_layout.addWidget(del_btn)
        layout.addLayout(top_layout)

        # 그룹 배정
        group_layout = QHBoxLayout()
        self.lbl_g = QLabel(I18n.tr("group_label"))
        self.lbl_g.setStyleSheet("color: #64748B; font-size: 11px;")
        self.group_combo = QComboBox()
        self.group_combo.setFixedHeight(28)
        self.refresh_groups()
        self.group_combo.currentTextChanged.connect(self.on_group_changed)
        group_layout.addWidget(self.lbl_g)
        group_layout.addWidget(self.group_combo, 1)
        layout.addLayout(group_layout)

        # 유휴 시간 설정
        idle_layout = QHBoxLayout()
        self.lbl_i = QLabel(I18n.tr("idle_label"))
        self.lbl_i.setStyleSheet("color: #64748B; font-size: 11px;")
        self.idle_spin = QSpinBox()
        self.idle_spin.setFixedHeight(28)
        self.idle_spin.setRange(1, 999)
        self.idle_spin.setValue(self.timer_data.get("idle_timeout", 5))
        self.idle_spin.setSuffix(f" {I18n.tr('unit_seconds')}")
        self.idle_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.idle_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.idle_spin.valueChanged.connect(self.on_idle_changed)
        idle_layout.addWidget(self.lbl_i)
        idle_layout.addWidget(self.idle_spin, 1)
        layout.addLayout(idle_layout)

        # 시간 표시 및 리셋
        time_layout = QHBoxLayout()
        self.time_label = QLabel(format_time(self.timer_data.get("elapsed_seconds", 0)))
        self.time_label.setStyleSheet("font-weight: bold; font-family: monospace; font-size: 16px; color: #2563EB;")
        time_layout.addWidget(self.time_label)
        time_layout.addStretch()

        self.btn_reset = QPushButton(I18n.tr("reset"))
        self.btn_reset.setFixedHeight(26)
        self.btn_reset.clicked.connect(self.reset_time)
        time_layout.addWidget(self.btn_reset)
        layout.addLayout(time_layout)

        I18n.language_changed.connect(self.retranslate_ui)

    def update_time_display(self, seconds: int):
        """실시간 틱 전달받아 라벨 갱신"""
        self.timer_data["elapsed_seconds"] = seconds
        self.time_label.setText(format_time(seconds))

    def refresh_groups(self):
        self.group_combo.blockSignals(True)
        self.group_combo.clear()
        groups = list(config_mgr.config.get("groups", {}).keys())
        if groups:
            self.group_combo.setEnabled(True)
            self.group_combo.addItems(groups)
            cur = self.timer_data.get("group", "")
            if cur in groups:
                self.group_combo.setCurrentText(cur)
            else:
                self.timer_data["group"] = groups[0]
                self.group_combo.setCurrentText(groups[0])
        else:
            self.group_combo.setEnabled(False)
            self.group_combo.addItem(I18n.tr("no_group_available"))
            self.timer_data["group"] = ""
        self.group_combo.blockSignals(False)

    def retranslate_ui(self):
        self.lbl_g.setText(I18n.tr("group_label"))
        self.lbl_i.setText(I18n.tr("idle_label"))
        self.idle_spin.setSuffix(f" {I18n.tr('unit_seconds')}")
        self.btn_reset.setText(I18n.tr("reset"))

    def update_card_style(self):
        is_dark = config_mgr.config.get("settings", {}).get("dark_mode", False)
        bg = "#27272A" if is_dark else "#FFFFFF"
        border = "#3F3F46" if is_dark else "#D0D7DE"
        text_color = "#FAFAFA" if is_dark else "#111827"
        self.setStyleSheet(f"""
            TimerCardWidget {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 8px;
            }}
            QLabel {{ color: {text_color}; }}
        """)

    def on_name_text_changed(self, txt):
        """타이핑 중: 데이터 업데이트 및 바탕화면 위젯 라벨 즉시 변경"""
        self.timer_data["name"] = txt
        self.name_updated.emit(self.timer_data.get("id"), txt)

    def on_name_editing_finished(self):
        """입력 종료(엔터/포커스 아웃): 영구 저장 및 전체 동기화"""
        config_mgr.save_config()
        self.changed.emit()

    def on_group_changed(self, txt):
        if txt and txt != I18n.tr("no_group_available"):
            self.timer_data["group"] = txt
        else:
            self.timer_data["group"] = ""
        config_mgr.save_config()
        self.changed.emit()

    def on_idle_changed(self, val):
        self.timer_data["idle_timeout"] = val
        config_mgr.save_config()

    def reset_time(self):
        dlg = ConfirmDialog(I18n.tr("reset_confirm_title"), I18n.tr("reset_confirm_msg"), is_danger=False, parent=self)
        if dlg.exec() == ConfirmDialog.DialogCode.Accepted:
            t_id = self.timer_data.get("id")
            self.timer_data["elapsed_seconds"] = 0
            self.time_label.setText(format_time(0))
            config_mgr.save_config()
            
            # 1. ActivityEngine 틱 시그널로 0초 즉시 브로드캐스트 (바탕화면 위젯 즉각 반영)
            activity_engine.tick.emit({t_id: 0})
            
            # 2. 설정 변경 이벤트 발행
            self.changed.emit()


class GroupCardWidget(QFrame):
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
        self.title_label = QLabel(self.group_name)
        self.title_label.setStyleSheet("font-weight: 600; font-size: 13px;")
        header.addWidget(self.title_label)
        header.addStretch()

        self.del_btn = QPushButton(I18n.tr("del_group"))
        self.del_btn.setFixedHeight(24)
        self.del_btn.setStyleSheet("QPushButton { font-size: 11px; padding: 2px 8px; color: #EF4444; } QPushButton:hover { background-color: #EF4444; color: white; }")
        self.del_btn.clicked.connect(lambda: self.remove_group_callback(self.group_name))
        header.addWidget(self.del_btn)
        layout.addLayout(header)

        self.slot_labels = []
        self.slot_edits = []
        self.slot_pick_btns = []
        self.slot_clear_btns = []

        for i in range(3):
            slot_h = QHBoxLayout()
            slot_label = QLabel(f"{I18n.tr('slot')} {i+1}:")
            slot_label.setFixedWidth(46)
            slot_label.setStyleSheet("color: #64748B; font-size: 11px;")
            self.slot_labels.append(slot_label)

            le = QLineEdit(self.windows[i])
            le.setFixedHeight(28)
            le.setPlaceholderText(I18n.tr("slot_placeholder"))
            le.textChanged.connect(lambda txt, idx=i: self.on_text_changed(idx, txt))
            self.slot_edits.append(le)

            btn_p = QPushButton(I18n.tr("pick_window"))
            btn_p.setFixedHeight(28)
            btn_p.setFixedWidth(106)
            btn_p.clicked.connect(lambda _, b=btn_p, edit=le, idx=i: self.start_capture(b, edit, idx))
            self.slot_pick_btns.append(btn_p)

            btn_c = QPushButton(I18n.tr("clear"))
            btn_c.setFixedHeight(28)
            btn_c.setFixedWidth(54)
            btn_c.clicked.connect(lambda _, edit=le, idx=i: self.clear_slot(edit, idx))
            self.slot_clear_btns.append(btn_c)

            slot_h.addWidget(slot_label)
            slot_h.addWidget(le, 1)
            slot_h.addWidget(btn_p)
            slot_h.addWidget(btn_c)
            layout.addLayout(slot_h)

        capture_bridge.window_captured.connect(self.on_window_captured)

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
        bg = "#27272A" if is_dark else "#FFFFFF"
        border = "#3F3F46" if is_dark else "#D0D7DE"
        text_color = "#FAFAFA" if is_dark else "#111827"
        self.setStyleSheet(f"""
            GroupCardWidget {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 8px;
            }}
            QLabel {{ color: {text_color}; }}
        """)

    def on_text_changed(self, idx, txt):
        self.windows[idx] = txt.strip()
        config_mgr.config.setdefault("groups", {})[self.group_name] = [w for w in self.windows if w]
        config_mgr.save_config()

    def clear_slot(self, le, idx):
        le.clear()
        self.on_text_changed(idx, "")

    def start_capture(self, btn, le, idx):
        if getattr(btn, 'is_capturing', False):
            self.reset_btn(btn)
            cancel_window_click_capture()
            return

        if self.current_capturing_btn:
            self.reset_btn(self.current_capturing_btn)

        self.current_capturing_btn = btn
        self.current_target = (le, idx)
        btn.is_capturing = True
        btn.setText(I18n.tr("waiting_click"))
        btn.setProperty("activeCapture", True)
        btn.style().unpolish(btn)
        btn.style().polish(btn)
        start_window_click_capture()

    def on_window_captured(self, title):
        if self.current_capturing_btn and hasattr(self, 'current_target'):
            le, idx = self.current_target
            le.setText(title)
            self.on_text_changed(idx, title)
            self.reset_btn(self.current_capturing_btn)
            self.current_capturing_btn = None

    def reset_btn(self, btn):
        btn.is_capturing = False
        btn.setText(I18n.tr("pick_window"))
        btn.setProperty("activeCapture", False)
        btn.style().unpolish(btn)
        btn.style().polish(btn)


class TabTimerSettings(QWidget):
    settings_changed = pyqtSignal()
    timer_name_changed = pyqtSignal(str, str)  # (timer_id, new_name)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.card_map = {}  # {timer_id: TimerCardWidget}
        self.init_ui()
        
        # 엔진의 실시간 초 틱 시그널 연결 (설정 화면 초 연동)
        activity_engine.tick.connect(self.on_activity_tick)
        I18n.language_changed.connect(self.retranslate_ui)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 8, 4, 4)

        self.sub_tabs = QTabWidget()
        self.sub_tabs.setObjectName("subTabWidget")

        # 1. 타이머 목록 탭
        self.sub_page_timers = QWidget()
        layout_timers = QVBoxLayout(self.sub_page_timers)
        layout_timers.setContentsMargins(10, 10, 10, 10)
        layout_timers.setSpacing(10)

        top_bar = QHBoxLayout()
        self.snap_cb = QCheckBox(I18n.tr("magnetic_snap"))
        self.snap_cb.setChecked(config_mgr.config.get("settings", {}).get("magnetic_snap", True))
        self.snap_cb.toggled.connect(self.on_snap_toggled)
        self.btn_add_timer = QPushButton(I18n.tr("add_timer"))
        self.btn_add_timer.clicked.connect(self.add_timer)
        top_bar.addWidget(self.snap_cb)
        top_bar.addStretch()
        top_bar.addWidget(self.btn_add_timer)
        layout_timers.addLayout(top_bar)

        scroll_t = QScrollArea()
        scroll_t.setWidgetResizable(True)
        t_content = QWidget()
        self.timer_grid = QGridLayout(t_content)
        self.timer_grid.setContentsMargins(4, 4, 4, 4)
        self.timer_grid.setSpacing(10)
        self.timer_grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        scroll_t.setWidget(t_content)
        layout_timers.addWidget(scroll_t)

        # 2. 창 그룹 관리 탭
        self.sub_page_groups = QWidget()
        layout_groups = QVBoxLayout(self.sub_page_groups)
        layout_groups.setContentsMargins(10, 10, 10, 10)
        layout_groups.setSpacing(10)

        g_header = QHBoxLayout()
        self.new_g_edit = QLineEdit()
        self.new_g_edit.setPlaceholderText(I18n.tr("new_group_placeholder"))
        self.new_g_edit.returnPressed.connect(self.create_group)
        self.btn_create_g = QPushButton(I18n.tr("create_group"))
        self.btn_create_g.clicked.connect(self.create_group)
        g_header.addWidget(self.new_g_edit, 1)
        g_header.addWidget(self.btn_create_g)
        layout_groups.addLayout(g_header)

        scroll_g = QScrollArea()
        scroll_g.setWidgetResizable(True)
        g_content = QWidget()
        self.group_list_layout = QVBoxLayout(g_content)
        self.group_list_layout.setContentsMargins(4, 4, 4, 4)
        self.group_list_layout.setSpacing(10)
        self.group_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_g.setWidget(g_content)
        layout_groups.addWidget(scroll_g)

        self.sub_tabs.addTab(self.sub_page_timers, "타이머 목록")
        self.sub_tabs.addTab(self.sub_page_groups, "창 매칭 그룹")

        main_layout.addWidget(self.sub_tabs)

        self.refresh_timer_list()
        self.refresh_group_list()

    def on_activity_tick(self, updated_dict: dict):
        """엔진에서 1초마다 보내주는 초 데이터를 카드 위젯에 즉시 전달"""
        for t_id, secs in updated_dict.items():
            if t_id in self.card_map:
                self.card_map[t_id].update_time_display(secs)

    def on_snap_toggled(self, checked):
        config_mgr.config.setdefault("settings", {})["magnetic_snap"] = checked
        config_mgr.save_config()

    def add_timer(self):
        groups = list(config_mgr.config.get("groups", {}).keys())
        first_g = groups[0] if groups else ""
        new_t = {
            "id": str(uuid.uuid4()),
            "name": f"{I18n.tr('default_timer_name')} {len(config_mgr.config.get('timers', [])) + 1}",
            "group": first_g,
            "idle_timeout": 5,
            "elapsed_seconds": 0,
            "x": 200, "y": 300,
            "paused": False
        }
        config_mgr.config.setdefault("timers", []).append(new_t)
        config_mgr.save_config()
        self.refresh_timer_list()
        self.settings_changed.emit()

    def remove_timer(self, timer_data):
        dlg = ConfirmDialog(I18n.tr("del_timer_title"), I18n.tr("del_timer_msg").format(name=timer_data.get('name')), is_danger=True, parent=self)
        if dlg.exec() == ConfirmDialog.DialogCode.Accepted:
            t_id = timer_data.get("id")
            for p in config_mgr.config.get("pets", []):
                if p.get("bound_timer_id") == t_id:
                    p["bound_timer_id"] = ""
            if timer_data in config_mgr.config.get("timers", []):
                config_mgr.config["timers"].remove(timer_data)
            config_mgr.save_config()
            self.refresh_timer_list()
            self.settings_changed.emit()

    def create_group(self):
        name = self.new_g_edit.text().strip()
        groups = config_mgr.config.setdefault("groups", {})
        if not name:
            idx = 1
            while f"{I18n.tr('default_group_name')} {idx}" in groups: idx += 1
            name = f"{I18n.tr('default_group_name')} {idx}"
        elif name in groups:
            AlertDialog(I18n.tr("error"), I18n.tr("group_exists_warn"), self).exec()
            return

        groups[name] = ["", "", ""]
        config_mgr.save_config()
        self.new_g_edit.clear()
        self.refresh_group_list()
        self.refresh_timer_list()
        self.settings_changed.emit()

    def remove_group(self, name):
        dlg = ConfirmDialog(I18n.tr("del_group"), f"'{name}' 그룹을 삭제하시겠습니까?", is_danger=True, parent=self)
        if dlg.exec() != ConfirmDialog.DialogCode.Accepted: return
        groups = config_mgr.config.get("groups", {})
        if name in groups: del groups[name]
        fallback = list(groups.keys())[0] if groups else ""
        for t in config_mgr.config.get("timers", []):
            if t.get("group") == name: t["group"] = fallback
        config_mgr.save_config()
        self.refresh_group_list()
        self.refresh_timer_list()
        self.settings_changed.emit()

    def refresh_timer_list(self):
        self.card_map.clear()
        while self.timer_grid.count():
            item = self.timer_grid.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        for idx, t in enumerate(config_mgr.config.get("timers", [])):
            card = TimerCardWidget(t, self.remove_timer)
            card.changed.connect(self.settings_changed.emit)
            card.name_updated.connect(self.timer_name_changed.emit)
            self.card_map[t.get("id")] = card
            self.timer_grid.addWidget(card, idx // 2, idx % 2)

    def refresh_group_list(self):
        while self.group_list_layout.count():
            item = self.group_list_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        for g_name, wins in config_mgr.config.get("groups", {}).items():
            card = GroupCardWidget(g_name, wins, self.remove_group)
            self.group_list_layout.addWidget(card)

    def retranslate_ui(self):
        self.sub_tabs.setTabText(0, I18n.tr("subtab_timer_list"))
        self.sub_tabs.setTabText(1, I18n.tr("subtab_window_groups"))
        
        self.snap_cb.setText(I18n.tr("magnetic_snap"))
        self.btn_add_timer.setText(I18n.tr("add_timer"))
        self.new_g_edit.setPlaceholderText(I18n.tr("new_group_placeholder"))
        self.btn_create_g.setText(I18n.tr("create_group"))

        for card in self.card_map.values():
            card.retranslate_ui()

        for i in range(self.group_list_layout.count()):
            w = self.group_list_layout.itemAt(i).widget()
            if isinstance(w, GroupCardWidget):
                w.retranslate_ui()

    def apply_theme(self):
        for card in self.card_map.values():
            card.update_card_style()

        for i in range(self.group_list_layout.count()):
            w = self.group_list_layout.itemAt(i).widget()
            if isinstance(w, GroupCardWidget):
                w.update_card_style()