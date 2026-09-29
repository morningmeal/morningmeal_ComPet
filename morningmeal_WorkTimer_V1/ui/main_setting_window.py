import uuid
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget, QScrollArea,
    QPushButton, QLabel, QLineEdit, QCheckBox, QComboBox, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from core.config_manager import config_mgr
from core.i18n import I18n
from ui.theme import LIGHT_THEME, DARK_THEME
from ui.components import CustomTitleBar, TimerCardWidget, GroupCardWidget, ConfirmDialog, AlertDialog

def create_h_separator():
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFrameShadow(QFrame.Shadow.Plain)
    line.setStyleSheet("background-color: rgba(128, 128, 128, 0.18); border: none; max-height: 1px;")
    return line

class MainSettingWindow(QWidget):
    settings_updated = pyqtSignal()
    theme_changed = pyqtSignal()
    quit_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedWidth(560)
        self.setMinimumHeight(680)

        self.is_dark_mode = config_mgr.config.get("settings", {}).get("dark_mode", False)

        self.init_ui()
        self.apply_theme()
        I18n.language_changed.connect(self.retranslate_ui)

    def init_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self.root_widget = QWidget()
        self.root_widget.setObjectName("settingsRoot")
        root_layout = QVBoxLayout(self.root_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.title_bar = CustomTitleBar(self, "app_title")
        self.title_bar.theme_toggled.connect(self.toggle_theme)
        root_layout.addWidget(self.title_bar)

        container = QWidget()
        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(16, 12, 16, 16)

        self.tabs = QTabWidget()

        # [탭 1: 타이머 목록]
        self.tab_timers = QWidget()
        t_layout = QVBoxLayout(self.tab_timers)
        t_layout.setContentsMargins(10, 10, 10, 10)
        t_layout.setSpacing(10)
        
        self.btn_add_timer = QPushButton(I18n.tr("add_timer"))
        self.btn_add_timer.setFixedHeight(32)
        self.btn_add_timer.clicked.connect(self.add_timer)
        t_layout.addWidget(self.btn_add_timer)

        scroll_t = QScrollArea()
        scroll_t.setWidgetResizable(True)
        t_content = QWidget()
        self.timer_grid = QGridLayout(t_content)
        self.timer_grid.setContentsMargins(4, 4, 4, 4)
        self.timer_grid.setSpacing(10)
        self.timer_grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        scroll_t.setWidget(t_content)
        t_layout.addWidget(scroll_t)

        # [탭 2: 창 그룹 관리]
        self.tab_groups = QWidget()
        g_layout = QVBoxLayout(self.tab_groups)
        g_layout.setContentsMargins(10, 10, 10, 10)
        g_layout.setSpacing(10)

        top_g = QHBoxLayout()
        self.new_group_name_edit = QLineEdit()
        self.new_group_name_edit.setFixedHeight(32)
        self.new_group_name_edit.setPlaceholderText(I18n.tr("new_group_placeholder"))
        self.new_group_name_edit.returnPressed.connect(self.create_group)  # Enter 키 입력 시 생성 지원

        self.btn_add_group = QPushButton(I18n.tr("create_group"))
        self.btn_add_group.setFixedHeight(32)
        self.btn_add_group.clicked.connect(self.create_group)

        top_g.addWidget(self.new_group_name_edit, 1)
        top_g.addWidget(self.btn_add_group)
        g_layout.addLayout(top_g)

        scroll_g = QScrollArea()
        scroll_g.setWidgetResizable(True)
        g_content = QWidget()
        self.group_list_layout = QVBoxLayout(g_content)
        self.group_list_layout.setContentsMargins(4, 4, 4, 4)
        self.group_list_layout.setSpacing(12)
        self.group_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_g.setWidget(g_content)
        g_layout.addWidget(scroll_g)

        # [탭 3: 환경 설정 & 언어 & 종료]
        self.tab_general = QWidget()
        gen_layout = QVBoxLayout(self.tab_general)
        gen_layout.setContentsMargins(16, 16, 16, 16)
        gen_layout.setSpacing(14)

        # 언어 설정
        lang_layout = QHBoxLayout()
        self.lang_label = QLabel(I18n.tr("language"))
        self.lang_label.setStyleSheet("font-weight: 500; font-size: 13px;")
        self.lang_combo = QComboBox()
        self.lang_combo.setFixedHeight(30)
        self.lang_combo.setMinimumWidth(160)
        self.lang_map = [
            ("한국어 (KO)", "ko"),
            ("English (EN)", "en"),
            ("日本語 (JA)", "ja"),
            ("简体中文 (ZH_CN)", "zh_CN"),
            ("繁體中文 (ZH_TW)", "zh_TW")
        ]
        for name, code in self.lang_map:
            self.lang_combo.addItem(name, code)

        cur_lang = I18n.get_lang()
        for idx, (_, code) in enumerate(self.lang_map):
            if code == cur_lang:
                self.lang_combo.setCurrentIndex(idx)
                break
        self.lang_combo.currentIndexChanged.connect(self.on_lang_changed)
        lang_layout.addWidget(self.lang_label)
        lang_layout.addStretch()
        lang_layout.addWidget(self.lang_combo)
        gen_layout.addLayout(lang_layout)

        gen_layout.addWidget(create_h_separator())

        snap_layout = QHBoxLayout()
        self.snap_cb = QCheckBox(I18n.tr("magnetic_snap"))
        self.snap_cb.setChecked(config_mgr.config.get("settings", {}).get("magnetic_snap", True))
        self.snap_cb.toggled.connect(self.save_general)
        snap_layout.addWidget(self.snap_cb)
        gen_layout.addLayout(snap_layout)

        gen_layout.addWidget(create_h_separator())

        exit_container = QWidget()
        exit_vbox = QVBoxLayout(exit_container)
        exit_vbox.setContentsMargins(0, 4, 0, 0)
        exit_vbox.setSpacing(10)

        self.lbl_desc = QLabel(I18n.tr("program_exit_desc"))
        self.lbl_desc.setStyleSheet("color: #64748B; font-size: 12px;")

        self.btn_exit_app = QPushButton(I18n.tr("program_exit_btn"))
        self.btn_exit_app.setObjectName("dangerBtn")
        self.btn_exit_app.setFixedHeight(34)
        self.btn_exit_app.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_exit_app.clicked.connect(self.confirm_and_exit)

        exit_vbox.addWidget(self.lbl_desc)
        exit_vbox.addWidget(self.btn_exit_app)
        gen_layout.addWidget(exit_container)

        gen_layout.addStretch()

        self.tabs.addTab(self.tab_timers, I18n.tr("tab_timers"))
        self.tabs.addTab(self.tab_groups, I18n.tr("tab_groups"))
        self.tabs.addTab(self.tab_general, I18n.tr("tab_general"))

        c_layout.addWidget(self.tabs)
        root_layout.addWidget(container)
        outer.addWidget(self.root_widget)

        self.refresh_timer_list()
        self.refresh_group_list()

    def on_lang_changed(self, index):
        code = self.lang_combo.itemData(index)
        if code:
            I18n.set_language(code)
            config_mgr.config.setdefault("settings", {})["language"] = code
            config_mgr.save_config()

    def retranslate_ui(self):
        self.tabs.setTabText(0, I18n.tr("tab_timers"))
        self.tabs.setTabText(1, I18n.tr("tab_groups"))
        self.tabs.setTabText(2, I18n.tr("tab_general"))
        self.btn_add_timer.setText(I18n.tr("add_timer"))
        self.btn_add_group.setText(I18n.tr("create_group"))
        self.new_group_name_edit.setPlaceholderText(I18n.tr("new_group_placeholder"))
        self.lang_label.setText(I18n.tr("language"))
        self.snap_cb.setText(I18n.tr("magnetic_snap"))
        self.lbl_desc.setText(I18n.tr("program_exit_desc"))
        self.btn_exit_app.setText(I18n.tr("program_exit_btn"))

    def confirm_and_exit(self):
        dlg = ConfirmDialog(
            title_text=I18n.tr("exit_confirm_title"),
            msg_text=I18n.tr("exit_confirm_msg"),
            is_danger=True,
            parent=self
        )
        if dlg.exec() == ConfirmDialog.DialogCode.Accepted:
            self.quit_requested.emit()

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        config_mgr.config.setdefault("settings", {})["dark_mode"] = self.is_dark_mode
        config_mgr.save_config()
        self.apply_theme()
        self.refresh_all_cards_theme()
        self.theme_changed.emit()

    def refresh_all_cards_theme(self):
        for i in range(self.timer_grid.count()):
            w = self.timer_grid.itemAt(i).widget()
            if isinstance(w, TimerCardWidget):
                w.update_card_style()

        for i in range(self.group_list_layout.count()):
            w = self.group_list_layout.itemAt(i).widget()
            if isinstance(w, GroupCardWidget):
                w.update_card_style()

    def apply_theme(self):
        theme = DARK_THEME if self.is_dark_mode else LIGHT_THEME
        self.setStyleSheet(theme)
        self.title_bar.theme_btn.setText("Light" if self.is_dark_mode else "Dark")

    def save_general(self, checked):
        config_mgr.config.setdefault("settings", {})["magnetic_snap"] = checked
        config_mgr.save_config()

    def add_timer(self):
        groups = list(config_mgr.config.get("groups", {}).keys())
        first_group = groups[0] if groups else ""
        new_timer = {
            "id": str(uuid.uuid4()),
            "name": f"{I18n.tr('default_timer_name')} {len(config_mgr.config.get('timers', [])) + 1}",
            "group": first_group,
            "idle_timeout": 5,
            "elapsed_seconds": 0,
            "x": 120,
            "y": 120,
            "paused": False
        }
        config_mgr.config.setdefault("timers", []).append(new_timer)
        config_mgr.save_config()
        self.refresh_timer_list()
        self.settings_updated.emit()

    def remove_timer(self, timer_data):
        timer_name = timer_data.get("name", I18n.tr("default_timer_name"))
        msg = I18n.tr("del_timer_msg").format(name=timer_name)

        # 커스텀 위험 작업 확인 다이얼로그 호출
        dlg = ConfirmDialog(
            title_text=I18n.tr("del_timer_title"),
            msg_text=msg,
            is_danger=True,
            parent=self
        )
        if dlg.exec() != ConfirmDialog.DialogCode.Accepted:
            return

        if timer_data in config_mgr.config.get("timers", []):
            config_mgr.config["timers"].remove(timer_data)
            config_mgr.save_config()
            self.refresh_timer_list()
            self.settings_updated.emit()

    def refresh_timer_list(self):
        while self.timer_grid.count():
            item = self.timer_grid.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        timers = config_mgr.config.get("timers", [])
        for idx, t in enumerate(timers):
            card = TimerCardWidget(t, self.remove_timer)
            card.changed.connect(self.settings_updated.emit)
            self.timer_grid.addWidget(card, idx // 2, idx % 2)

    def create_group(self):
        name = self.new_group_name_edit.text().strip()
        groups = config_mgr.config.setdefault("groups", {})

        # 이름을 입력하지 않은 경우: 번호 순서대로 빈 번호 자동 할당
        if not name:
            prefix = I18n.tr("default_group_name")
            idx = 1
            while f"{prefix} {idx}" in groups or f"{prefix}{idx}" in groups:
                idx += 1
            name = f"{prefix} {idx}"

        # 직접 입력했으나 이미 중복된 이름이 있는 경우 커스텀 경고창 출력
        elif name in groups:
            dlg = AlertDialog(
                title_text=I18n.tr("error"),
                msg_text=I18n.tr("group_exists_warn"),
                parent=self
            )
            dlg.exec()
            return

        # 새 그룹 생성 (3개 슬롯 기본 세팅)
        groups[name] = ["", "", ""]
        config_mgr.save_config()
        self.new_group_name_edit.clear()

        # 목록 갱신 및 설정 변경 시그널 전파
        self.refresh_group_list()
        self.refresh_timer_list()
        self.settings_updated.emit()

    def remove_group(self, name):
        dlg = ConfirmDialog(
            title_text=I18n.tr("del_group"),
            msg_text=f"'{name}' 그룹을 삭제하시겠습니까?",
            is_danger=True,
            parent=self
        )
        if dlg.exec() != ConfirmDialog.DialogCode.Accepted:
            return

        groups = config_mgr.config.get("groups", {})
        if name in groups:
            del groups[name]

        remaining_groups = list(groups.keys())
        fallback_group = remaining_groups[0] if remaining_groups else ""

        for t in config_mgr.config.get("timers", []):
            if t.get("group") == name or t.get("group") not in groups:
                t["group"] = fallback_group

        config_mgr.save_config()
        self.refresh_group_list()
        self.refresh_timer_list()
        self.settings_updated.emit()

    def refresh_group_list(self):
        while self.group_list_layout.count():
            item = self.group_list_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        groups = config_mgr.config.get("groups", {})
        for g_name, wins in groups.items():
            card = GroupCardWidget(g_name, wins, self.remove_group)
            self.group_list_layout.addWidget(card)