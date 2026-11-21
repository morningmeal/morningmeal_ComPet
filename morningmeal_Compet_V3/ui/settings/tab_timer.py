# ui/settings/tab_timer.py
import uuid
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QPushButton, QLabel, QLineEdit, QCheckBox, QComboBox,
    QSpinBox, QTabWidget, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from core.config_manager import config_mgr
from core.i18n import I18n
from core.activity_engine import activity_engine
from ui.components import (
    ConfirmDialog, capture_bridge,
    start_window_click_capture, cancel_window_click_capture, format_time
)

_active_capture_session = None


def _clear_active_capture_session():
    global _active_capture_session
    if _active_capture_session is not None:
        card, btn, _, _ = _active_capture_session
        try:
            card.reset_btn(btn)
        except RuntimeError:
            pass
        _active_capture_session = None


class TimerRowWidget(QWidget):
    changed = pyqtSignal()
    name_updated = pyqtSignal(str, str)

    def __init__(self, timer_data, remove_callback, parent=None):
        super().__init__(parent)
        self.timer_data = timer_data
        self.remove_callback = remove_callback

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 6, 0, 6)
        layout.setSpacing(6)

        # 타이머 이름 (인라인 편집)
        self.name_edit = QLineEdit(self.timer_data.get("name", I18n.tr("default_timer_name")))
        self.name_edit.setFixedWidth(130)
        self.name_edit.textChanged.connect(self.on_name_text_changed)
        self.name_edit.editingFinished.connect(self.on_name_editing_finished)
        layout.addWidget(self.name_edit)

        # 그룹 선택 드롭다운
        self.group_combo = QComboBox()
        self.group_combo.setFixedWidth(95)
        self.group_combo.view().setMinimumWidth(130)
        self.group_combo.view().setTextElideMode(Qt.TextElideMode.ElideRight)
        self.refresh_groups()
        self.group_combo.currentTextChanged.connect(self.on_group_changed)
        layout.addWidget(self.group_combo)

        # 유휴 시간 (초 스핀박스)
        self.idle_spin = QSpinBox()
        self.idle_spin.setFixedWidth(50)
        self.idle_spin.setRange(1, 999)
        self.idle_spin.setValue(self.timer_data.get("idle_timeout", 5))
        self.idle_spin.setSuffix(I18n.tr('unit_seconds'))
        self.idle_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.idle_spin.valueChanged.connect(self.on_idle_changed)
        layout.addWidget(self.idle_spin)

        # 누적 시간 표시
        self.time_label = QLabel(format_time(self.timer_data.get("elapsed_seconds", 0)))
        self.time_label.setFixedWidth(74)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setStyleSheet("font-family: monospace; font-weight: bold;")
        layout.addWidget(self.time_label)

        layout.addStretch()

        # 정지/재개 토글 버튼
        is_paused = self.timer_data.get("paused", False)
        self.btn_pause = QPushButton(I18n.tr("resume") if is_paused else I18n.tr("pause"))
        self.btn_pause.setProperty("actionType", "primary")
        self.btn_pause.setFixedWidth(38)
        self.btn_pause.clicked.connect(self.toggle_pause)
        layout.addWidget(self.btn_pause)

        # 초기화 버튼
        self.btn_reset = QPushButton(I18n.tr("reset"))
        self.btn_reset.setProperty("actionType", "danger")
        self.btn_reset.setFixedWidth(44)
        self.btn_reset.clicked.connect(self.reset_time)
        layout.addWidget(self.btn_reset)

        # 삭제 버튼
        self.btn_del = QPushButton(I18n.tr("delete"))
        self.btn_del.setProperty("actionType", "danger")
        self.btn_del.setFixedWidth(34)
        self.btn_del.clicked.connect(lambda: self.remove_callback(self.timer_data))
        layout.addWidget(self.btn_del)

        I18n.language_changed.connect(self.retranslate_ui)

    def update_time_display(self, seconds: int):
        self.timer_data["elapsed_seconds"] = seconds
        self.time_label.setText(format_time(seconds))

    def refresh_groups(self):
        self.group_combo.blockSignals(True)
        self.group_combo.clear()
        groups = list(config_mgr.config.get("groups", {}).keys())
        if groups:
            self.group_combo.addItems(groups)
            cur = self.timer_data.get("group", "")
            if cur in groups:
                self.group_combo.setCurrentText(cur)
            else:
                self.timer_data["group"] = groups[0]
                self.group_combo.setCurrentText(groups[0])
        else:
            self.group_combo.addItem(I18n.tr("no_group_available"))
            self.timer_data["group"] = ""
        self.group_combo.blockSignals(False)

    def retranslate_ui(self):
        self.idle_spin.setSuffix(I18n.tr('unit_seconds'))
        self.btn_reset.setText(I18n.tr("reset"))
        self.btn_del.setText(I18n.tr("delete"))
        is_paused = self.timer_data.get("paused", False)
        self.btn_pause.setText(I18n.tr("resume") if is_paused else I18n.tr("pause"))

    def toggle_pause(self):
        new_state = not self.timer_data.get("paused", False)
        self.timer_data["paused"] = new_state
        config_mgr.save_config()
        self.btn_pause.setText(I18n.tr("resume") if new_state else I18n.tr("pause"))
        self.changed.emit()

    def on_name_text_changed(self, txt):
        self.timer_data["name"] = txt
        self.name_updated.emit(self.timer_data.get("id"), txt)

    def on_name_editing_finished(self):
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
            activity_engine.tick.emit({t_id: 0})
            self.changed.emit()


class GroupSectionWidget(QWidget):
    def __init__(self, group_name, windows, remove_group_callback, rename_group_callback, parent=None):
        super().__init__(parent)
        self.group_name = group_name
        self.windows = (list(windows) + ["", "", ""])[:3]
        self.remove_group_callback = remove_group_callback
        self.rename_group_callback = rename_group_callback

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 6, 4, 14)
        layout.setSpacing(6)

        # 상단 그룹명 & 삭제 버튼
        top_h = QHBoxLayout()
        top_h.setSpacing(8)
        self.name_edit = QLineEdit(self.group_name)
        self.name_edit.setFixedWidth(200)
        self.name_edit.setStyleSheet("font-weight: 700; font-size: 13px;")
        self.name_edit.editingFinished.connect(self.on_group_rename_finished)
        top_h.addWidget(self.name_edit)
        top_h.addStretch()

        self.del_btn = QPushButton(I18n.tr("del_group"))
        self.del_btn.setProperty("actionType", "danger")
        self.del_btn.setFixedWidth(36)
        self.del_btn.setStyleSheet("text-align: right;")
        self.del_btn.clicked.connect(lambda: self.remove_group_callback(self.group_name))
        top_h.addWidget(self.del_btn)
        layout.addLayout(top_h)

        self.slot_labels = []
        self.slot_edits = []
        self.slot_pick_btns = []
        self.slot_clear_btns = []

        for i in range(3):
            slot_h = QHBoxLayout()
            slot_h.setContentsMargins(4, 0, 0, 0)
            slot_h.setSpacing(8)

            lbl = QLabel(f"{i+1}{I18n.tr('slot')}")
            lbl.setFixedWidth(46)
            lbl.setStyleSheet("color: #6B7280; font-size: 12px;")
            self.slot_labels.append(lbl)

            le = QLineEdit(self.windows[i])
            le.setFixedHeight(26)
            le.setMinimumWidth(0)
            le.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
            le.setPlaceholderText(I18n.tr("slot_placeholder"))
            le.textChanged.connect(lambda txt, idx=i: self.on_text_changed(idx, txt))
            self.slot_edits.append(le)

            btn_p = QPushButton(I18n.tr("pick_window"))
            btn_p.setFixedWidth(64)
            btn_p.clicked.connect(lambda _, b=btn_p, edit=le, idx=i: self.start_capture(b, edit, idx))
            self.slot_pick_btns.append(btn_p)

            btn_c = QPushButton(I18n.tr("clear"))
            btn_c.setProperty("actionType", "danger")
            btn_c.setFixedWidth(50)
            btn_c.setStyleSheet("text-align: right;")
            btn_c.clicked.connect(lambda _, edit=le, idx=i: self.clear_slot(edit, idx))
            self.slot_clear_btns.append(btn_c)

            slot_h.addWidget(lbl)
            slot_h.addWidget(le, 1)
            slot_h.addWidget(btn_p)
            slot_h.addWidget(btn_c)
            layout.addLayout(slot_h)

        # 그룹 간 구분선
        self.line = QLabel()
        self.line.setObjectName("subDivider")
        self.line.setFixedHeight(1)
        layout.addWidget(self.line)

    def on_group_rename_finished(self):
        new_name = self.name_edit.text().strip()
        if new_name and new_name != self.group_name:
            self.rename_group_callback(self.group_name, new_name)
            self.group_name = new_name

    def retranslate_ui(self):
        self.del_btn.setText(I18n.tr("del_group"))
        for i, lbl in enumerate(self.slot_labels):
            lbl.setText(f"{i+1}{I18n.tr('slot')}")
        for le in self.slot_edits:
            le.setPlaceholderText(I18n.tr("slot_placeholder"))
        for btn in self.slot_pick_btns:
            if not getattr(btn, 'is_capturing', False):
                btn.setText(I18n.tr("pick_window"))
            else:
                btn.setText(I18n.tr("waiting_click"))
        for btn in self.slot_clear_btns:
            btn.setText(I18n.tr("clear"))

    def on_text_changed(self, idx, txt):
        self.windows[idx] = txt.strip()
        config_mgr.config.setdefault("groups", {})[self.group_name] = [w for w in self.windows if w]
        config_mgr.save_config()

    def clear_slot(self, le, idx):
        le.clear()
        self.on_text_changed(idx, "")

    def start_capture(self, btn, le, idx):
        global _active_capture_session
        if getattr(btn, 'is_capturing', False):
            _clear_active_capture_session()
            cancel_window_click_capture()
            return

        _clear_active_capture_session()
        btn.is_capturing = True
        btn.setText(I18n.tr("waiting_click"))
        btn.setProperty("activeCapture", True)
        btn.style().unpolish(btn)
        btn.style().polish(btn)

        _active_capture_session = (self, btn, le, idx)
        start_window_click_capture()

    def reset_btn(self, btn):
        btn.is_capturing = False
        btn.setText(I18n.tr("pick_window"))
        btn.setProperty("activeCapture", False)
        btn.style().unpolish(btn)
        btn.style().polish(btn)


class TabTimerSettings(QWidget):
    settings_changed = pyqtSignal()
    timer_name_changed = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.card_map = {}
        self.init_ui()
        activity_engine.tick.connect(self.on_activity_tick)
        capture_bridge.window_captured.connect(self.on_global_window_captured)
        I18n.language_changed.connect(self.retranslate_ui)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.sub_tabs = QTabWidget()
        self.sub_tabs.setObjectName("subTabWidget")

        # 1. 타이머 목록 탭
        self.sub_page_timers = QWidget()
        l_t = QVBoxLayout(self.sub_page_timers)
        l_t.setContentsMargins(4, 14, 4, 12)
        l_t.setSpacing(10)

        top_bar_t = QHBoxLayout()
        self.snap_cb = QCheckBox(I18n.tr("magnetic_snap"))
        self.snap_cb.setChecked(config_mgr.config.get("settings", {}).get("magnetic_snap", True))
        self.snap_cb.toggled.connect(self.on_snap_toggled)
        self.btn_add_timer = QPushButton(I18n.tr("add_timer"))
        self.btn_add_timer.setProperty("actionType", "primary")
        self.btn_add_timer.clicked.connect(self.add_timer)
        top_bar_t.addWidget(self.snap_cb)
        top_bar_t.addStretch()
        top_bar_t.addWidget(self.btn_add_timer)
        l_t.addLayout(top_bar_t)

        div_t = QLabel()
        div_t.setObjectName("accentDivider")
        div_t.setFixedHeight(1)
        l_t.addWidget(div_t)

        scroll_t = QScrollArea()
        scroll_t.setWidgetResizable(True)
        scroll_t.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.t_content_widget = QWidget()
        self.timer_list_layout = QVBoxLayout(self.t_content_widget)
        self.timer_list_layout.setContentsMargins(0, 0, 0, 0)
        self.timer_list_layout.setSpacing(4)
        self.timer_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_t.setWidget(self.t_content_widget)
        l_t.addWidget(scroll_t)

        # 2. 탭 그룹 탭
        self.sub_page_groups = QWidget()
        l_g = QVBoxLayout(self.sub_page_groups)
        l_g.setContentsMargins(4, 14, 4, 12)
        l_g.setSpacing(10)

        top_bar_g = QHBoxLayout()
        top_bar_g.addStretch()
        self.btn_create_g = QPushButton(I18n.tr("create_group"))
        self.btn_create_g.setProperty("actionType", "primary")
        self.btn_create_g.clicked.connect(self.create_group)
        top_bar_g.addWidget(self.btn_create_g)
        l_g.addLayout(top_bar_g)

        div_g = QLabel()
        div_g.setObjectName("accentDivider")
        div_g.setFixedHeight(1)
        l_g.addWidget(div_g)

        scroll_g = QScrollArea()
        scroll_g.setWidgetResizable(True)
        scroll_g.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.g_content_widget = QWidget()
        self.group_list_layout = QVBoxLayout(self.g_content_widget)
        self.group_list_layout.setContentsMargins(0, 0, 0, 0)
        self.group_list_layout.setSpacing(6)
        self.group_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_g.setWidget(self.g_content_widget)
        l_g.addWidget(scroll_g)

        self.sub_tabs.addTab(self.sub_page_timers, I18n.tr("subtab_timer_list"))
        self.sub_tabs.addTab(self.sub_page_groups, I18n.tr("subtab_window_groups"))
        main_layout.addWidget(self.sub_tabs)

        self.refresh_timer_list()
        self.refresh_group_list()

    def on_global_window_captured(self, slot_text: str, is_cancelled: bool):
        global _active_capture_session
        if _active_capture_session is None:
            return
        card, btn, le, idx = _active_capture_session
        _active_capture_session = None
        try:
            if not is_cancelled and slot_text:
                le.setText(slot_text)
                card.on_text_changed(idx, slot_text)
            card.reset_btn(btn)
        except RuntimeError:
            pass

    def on_activity_tick(self, updated_dict: dict):
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
        groups = config_mgr.config.setdefault("groups", {})
        idx = 1
        name = f"{I18n.tr('default_group_name')} {idx}"
        while name in groups:
            idx += 1
            name = f"{I18n.tr('default_group_name')} {idx}"

        groups[name] = ["", "", ""]
        config_mgr.save_config()
        self.refresh_group_list()
        self.sync_timer_cards_groups()
        self.settings_changed.emit()

    def rename_group(self, old_name, new_name):
        groups = config_mgr.config.setdefault("groups", {})
        if new_name in groups and new_name != old_name:
            return
        if old_name in groups:
            wins = groups.pop(old_name)
            groups[new_name] = wins
            for t in config_mgr.config.get("timers", []):
                if t.get("group") == old_name:
                    t["group"] = new_name
            config_mgr.save_config()
            self.sync_timer_cards_groups()
            self.settings_changed.emit()

    def remove_group(self, name):
        dlg = ConfirmDialog(I18n.tr("del_group"), I18n.tr("del_group_msg").format(name=name), is_danger=True, parent=self)
        if dlg.exec() != ConfirmDialog.DialogCode.Accepted:
            return
        groups = config_mgr.config.get("groups", {})
        if name in groups:
            del groups[name]
        fallback = list(groups.keys())[0] if groups else ""
        for t in config_mgr.config.get("timers", []):
            if t.get("group") == name:
                t["group"] = fallback
        config_mgr.save_config()
        self.refresh_group_list()
        self.sync_timer_cards_groups()
        self.settings_changed.emit()

    def sync_timer_cards_groups(self):
        for card in self.card_map.values():
            card.refresh_groups()

    def refresh_timer_list(self):
        self.card_map.clear()
        while self.timer_list_layout.count():
            item = self.timer_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for t in config_mgr.config.get("timers", []):
            row = TimerRowWidget(t, self.remove_timer)
            row.changed.connect(self.settings_changed.emit)
            row.name_updated.connect(self.timer_name_changed.emit)
            self.card_map[t.get("id")] = row
            self.timer_list_layout.addWidget(row)
        self.timer_list_layout.addStretch()

    def refresh_group_list(self):
        _clear_active_capture_session()
        cancel_window_click_capture()
        while self.group_list_layout.count():
            item = self.group_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for g_name, wins in config_mgr.config.get("groups", {}).items():
            sec = GroupSectionWidget(g_name, wins, self.remove_group, self.rename_group)
            self.group_list_layout.addWidget(sec)
        self.group_list_layout.addStretch()

    def retranslate_ui(self):
        self.sub_tabs.setTabText(0, I18n.tr("subtab_timer_list"))
        self.sub_tabs.setTabText(1, I18n.tr("subtab_window_groups"))
        self.snap_cb.setText(I18n.tr("magnetic_snap"))
        self.btn_add_timer.setText(I18n.tr("add_timer"))
        self.btn_create_g.setText(I18n.tr("create_group"))

        for card in self.card_map.values():
            card.retranslate_ui()
        for i in range(self.group_list_layout.count()):
            w = self.group_list_layout.itemAt(i).widget()
            if isinstance(w, GroupSectionWidget):
                w.retranslate_ui()

    def apply_theme(self):
        pass