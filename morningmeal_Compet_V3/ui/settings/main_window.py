# ui/settings/main_window.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, QComboBox, QPushButton
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
    quit_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedWidth(580)
        self.setMinimumHeight(660)

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
        r_layout.setContentsMargins(0, 0, 0, 0)
        r_layout.setSpacing(0)

        self.title_bar = CustomTitleBar(self, "app_title")
        self.title_bar.theme_toggled.connect(self.toggle_theme)
        r_layout.addWidget(self.title_bar)

        content = QWidget()
        c_layout = QVBoxLayout(content)
        c_layout.setContentsMargins(14, 10, 14, 14)

        # 3대 메인 탭 컨테이너
        self.tabs = QTabWidget()
        self.tab_timer = TabTimerSettings()
        self.tab_pet = TabPetSettings()
        self.tab_sound = TabSoundSettings()

        self.tab_timer.settings_changed.connect(self.on_child_settings_changed)
        self.tab_pet.settings_changed.connect(self.on_child_settings_changed)

        self.tabs.addTab(self.tab_timer, I18n.tr("tab_timer"))
        self.tabs.addTab(self.tab_pet, I18n.tr("tab_pet"))
        self.tabs.addTab(self.tab_sound, I18n.tr("tab_sound"))
        c_layout.addWidget(self.tabs)

        # 하단 언어 변경 및 프로그램 완전 종료
        bottom_bar = QHBoxLayout()
        self.lbl_lang = QLabel(I18n.tr("language"))
        self.combo_lang = QComboBox()
        self.lang_map = [
            ("한국어 (KO)", "ko"),
            ("English (EN)", "en"),
            ("日本語 (JA)", "ja"),
            ("简体中文 (ZH_CN)", "zh_CN"),
            ("繁體中文 (ZH_TW)", "zh_TW")
        ]
        for name, code in self.lang_map:
            self.combo_lang.addItem(name, code)

        cur = I18n.get_lang()
        for idx, (_, c) in enumerate(self.lang_map):
            if c == cur:
                self.combo_lang.setCurrentIndex(idx)
                break
        self.combo_lang.currentIndexChanged.connect(self.on_lang_changed)

        bottom_bar.addWidget(self.lbl_lang)
        bottom_bar.addWidget(self.combo_lang)
        bottom_bar.addStretch()

        self.btn_quit = QPushButton(I18n.tr("program_exit_btn"))
        self.btn_quit.setObjectName("dangerBtn")
        self.btn_quit.clicked.connect(self.confirm_quit)
        bottom_bar.addWidget(self.btn_quit)

        c_layout.addLayout(bottom_bar)
        r_layout.addWidget(content)
        outer.addWidget(self.root)

    def on_child_settings_changed(self):
        self.tab_pet.refresh_pet_list()
        self.tab_timer.refresh_timer_list()
        self.settings_updated.emit()

    def toggle_theme(self):
        self.is_dark = not self.is_dark
        config_mgr.config.setdefault("settings", {})["dark_mode"] = self.is_dark
        config_mgr.save_config()
        self.apply_theme()

    def apply_theme(self):
        # 1. 메인 윈도우 스타일시트 적용
        self.setStyleSheet(DARK_THEME if self.is_dark else LIGHT_THEME)
        
        # 2. 타이틀바 버튼 텍스트 변경
        self.title_bar.theme_btn.setText("Light" if self.is_dark else "Dark")

        # 3. 하위 탭들로 테마 갱신 신호 전파 (중요)
        if hasattr(self, 'tab_timer') and hasattr(self.tab_timer, 'apply_theme'):
            self.tab_timer.apply_theme()
            
        if hasattr(self, 'tab_pet') and hasattr(self.tab_pet, 'apply_theme'):
            self.tab_pet.apply_theme()

        # 4. 강제 리페인트
        self.root.style().unpolish(self.root)
        self.root.style().polish(self.root)
        self.update()

    def on_lang_changed(self, idx):
        code = self.combo_lang.itemData(idx)
        if code:
            I18n.set_language(code)
            config_mgr.config.setdefault("settings", {})["language"] = code
            config_mgr.save_config()

    def confirm_quit(self):
        dlg = ConfirmDialog(I18n.tr("exit_confirm_title"), I18n.tr("exit_confirm_msg"), is_danger=True, parent=self)
        if dlg.exec() == ConfirmDialog.DialogCode.Accepted:
            self.quit_requested.emit()

    def retranslate_ui(self):
        # 메인 3대 탭 이름 번역
        self.tabs.setTabText(0, I18n.tr("tab_timer"))
        self.tabs.setTabText(1, I18n.tr("tab_pet"))
        self.tabs.setTabText(2, I18n.tr("tab_sound"))
        
        # 하단 라벨 & 프로그램 완전 종료 버튼
        self.lbl_lang.setText(I18n.tr("language"))
        self.btn_quit.setText(I18n.tr("program_exit_btn"))
        
        # 자식 탭들에도 전달
        self.tab_timer.retranslate_ui()
        self.tab_pet.retranslate_ui()
        self.tab_sound.key_grp.retranslate_ui()
        self.tab_sound.click_grp.retranslate_ui()