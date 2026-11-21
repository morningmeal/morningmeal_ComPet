# ui/settings/main_window.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QFrame, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from core.config_manager import config_mgr
from core.i18n import I18n
from ui.theme import LIGHT_THEME, DARK_THEME
from ui.components import CustomTitleBar, ConfirmDialog
from ui.settings.tab_timer import TabTimerSettings
from ui.settings.tab_pet import TabPetSettings
from ui.settings.tab_sound import TabSoundSettings


class MainSettingWindow(QWidget):
    settings_updated = pyqtSignal()
    timer_name_updated = pyqtSignal(str, str)
    quit_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedWidth(560)
        self.setMinimumHeight(680)

        self.is_dark = config_mgr.config.get("settings", {}).get("dark_mode", False)
        self.init_ui()
        self.apply_theme()
        I18n.language_changed.connect(self.retranslate_ui)

    def init_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self.root = QWidget()
        self.root.setObjectName("settingsRoot")
        r_layout = QVBoxLayout(self.root)
        r_layout.setContentsMargins(20, 8, 20, 16)
        r_layout.setSpacing(0)

        self.title_bar = CustomTitleBar(self, "app_title")
        self.title_bar.layout().setContentsMargins(4, 0, 4, 0)
        self.title_bar.theme_toggled.connect(self.toggle_theme)
        r_layout.addWidget(self.title_bar)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("mainTabWidget")
        self.tab_timer = TabTimerSettings()
        self.tab_pet = TabPetSettings()
        self.tab_sound = TabSoundSettings()

        self.tab_timer.settings_changed.connect(self.on_child_settings_changed)
        self.tab_timer.timer_name_changed.connect(self.on_timer_name_changed)
        self.tab_pet.settings_changed.connect(self.on_child_settings_changed)

        self.tabs.addTab(self.tab_timer, I18n.tr("tab_timer"))
        self.tabs.addTab(self.tab_pet, I18n.tr("tab_pet"))
        self.tabs.addTab(self.tab_sound, I18n.tr("tab_sound"))
        r_layout.addWidget(self.tabs, 1)

        # 하단 파란 구분선
        bottom_line = QFrame()
        bottom_line.setObjectName("accentDivider")
        bottom_line.setFixedHeight(1)
        r_layout.addWidget(bottom_line)

        # 하단 우측 프로그램 종료 버튼
        bottom_bar = QHBoxLayout()
        bottom_bar.setContentsMargins(4, 12, 4, 0)
        bottom_bar.addStretch()
        self.btn_quit = QPushButton(I18n.tr("program_exit_btn"))
        self.btn_quit.setProperty("actionType", "danger")
        self.btn_quit.clicked.connect(self.confirm_quit)
        bottom_bar.addWidget(self.btn_quit)
        r_layout.addLayout(bottom_bar)

        outer.addWidget(self.root)

    def on_child_settings_changed(self):
        self.tab_pet.sync_pet_cards_state()
        self.settings_updated.emit()

    def on_timer_name_changed(self, timer_id: str, new_name: str):
        self.tab_pet.sync_pet_cards_state()
        self.timer_name_updated.emit(timer_id, new_name)

    def toggle_theme(self):
        self.is_dark = not self.is_dark
        config_mgr.config.setdefault("settings", {})["dark_mode"] = self.is_dark
        config_mgr.save_config()
        self.apply_theme()
        self.settings_updated.emit()

    def apply_theme(self):
        self.setStyleSheet(DARK_THEME if self.is_dark else LIGHT_THEME)
        self.title_bar.theme_btn.setText("light" if self.is_dark else "dark")

        self.root.style().unpolish(self.root)
        self.root.style().polish(self.root)
        self.update()

    def confirm_quit(self):
        dlg = ConfirmDialog(
            I18n.tr("exit_confirm_title"),
            I18n.tr("exit_confirm_msg"),
            is_danger=True,
            parent=self
        )
        if dlg.exec() == ConfirmDialog.DialogCode.Accepted:
            self.quit_requested.emit()

    def retranslate_ui(self):
        self.tabs.setTabText(0, I18n.tr("tab_timer"))
        self.tabs.setTabText(1, I18n.tr("tab_pet"))
        self.tabs.setTabText(2, I18n.tr("tab_sound"))
        self.btn_quit.setText(I18n.tr("program_exit_btn"))

        self.tab_timer.retranslate_ui()
        self.tab_pet.retranslate_ui()
        self.tab_sound.key_grp.retranslate_ui()
        self.tab_sound.click_grp.retranslate_ui()