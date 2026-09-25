# ui/settings_window.py
import os
import uuid
import zipfile
import shutil
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget, QScrollArea, 
    QComboBox, QCheckBox, QPushButton, QLabel, QMessageBox, QFileDialog,
    QGroupBox, QSlider, QLineEdit, QTableWidget, QHeaderView, QInputDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QUrl, QPoint
from PyQt6.QtGui import QDesktopServices, QMouseEvent
from core.i18n import I18n
from core.config_manager import config_mgr, SKINS_DIR
from ui.theme import LIGHT_THEME, DARK_THEME
from ui.components import PetCardWidget, SoundControlWidget, KeyCaptureButton


class CustomTitleBar(QWidget):
    """창 이동, 테마 토글, 최소화 및 닫기 기능을 지원하는 커스텀 상단 타이틀바"""
    theme_toggled = pyqtSignal()

    def __init__(self, parent_window, title="morningmeal_Compet"):
        super().__init__(parent_window)
        self.parent_window = parent_window
        self.setObjectName("titleBar")
        self.setFixedHeight(40)
        self.drag_start_pos = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 10, 0)
        layout.setSpacing(8)

        # 프로그램 타이틀 라벨
        self.title_label = QLabel(title)
        self.title_label.setObjectName("titleLabel")
        layout.addWidget(self.title_label)

        layout.addStretch()

        # 테마 전환 버튼 (Light / Dark)
        self.theme_btn = QPushButton("Mode")
        self.theme_btn.setObjectName("titleBtn")
        self.theme_btn.setFixedSize(54, 24)
        self.theme_btn.clicked.connect(self.theme_toggled.emit)
        layout.addWidget(self.theme_btn)

        # 최소화 버튼
        self.min_btn = QPushButton("–")
        self.min_btn.setObjectName("titleBtn")
        self.min_btn.setFixedSize(28, 24)
        self.min_btn.clicked.connect(self.parent_window.showMinimized)
        layout.addWidget(self.min_btn)

        # 닫기 버튼
        self.close_btn = QPushButton("✕")
        self.close_btn.setObjectName("titleCloseBtn")
        self.close_btn.setFixedSize(28, 24)
        self.close_btn.clicked.connect(self.parent_window.hide)
        layout.addWidget(self.close_btn)

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


class SettingsWindow(QWidget):
    settings_changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        # OS 기본 타이틀바를 제거하고 커스텀 프레임리스 윈도우 구성
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedWidth(560)
        self.setMinimumHeight(680)
        
        self.current_editing_skin = "default"
        self.skin_data = {}
        self.is_loading_skin = False
        self.pet_cards = {}
        self.is_dark_mode = config_mgr.settings.get("dark_mode", False)

        self.init_ui()
        self.apply_theme()
        self.load_skin_list()
        self.load_current_skin_config()
        self.retranslate_ui()
        I18n.language_changed.connect(self.retranslate_ui)

    def init_ui(self):
        # 최외곽 배경 레이아웃 (둥근 테두리 및 섀도우 지원)
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        
        self.root_widget = QWidget()
        self.root_widget.setObjectName("settingsRoot")
        root_layout = QVBoxLayout(self.root_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. 커스텀 타이틀바
        self.title_bar = CustomTitleBar(self, "morningmeal_Compet")
        self.title_bar.theme_toggled.connect(self.toggle_theme)
        root_layout.addWidget(self.title_bar)

        # 2. 본문 컨텐츠 영역
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(16, 12, 16, 16)

        self.tabs = QTabWidget()
        
        # ==================== 1. 일반 설정 탭 ====================
        self.tab_general = QWidget()
        gen_layout = QVBoxLayout(self.tab_general)
        self.lang_label = QLabel()
        self.lang_combo = QComboBox()
        
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
        for i, (_, code) in enumerate(self.lang_map):
            if code == cur_lang:
                self.lang_combo.setCurrentIndex(i)
                break
                
        self.lang_combo.currentIndexChanged.connect(self.change_language)
        
        self.tray_cb = QCheckBox()
        self.tray_cb.setChecked(config_mgr.settings.get("tray_mode", False))
        self.tray_cb.toggled.connect(self.toggle_tray_mode)

        self.click_through_cb = QCheckBox()
        self.click_through_cb.setChecked(config_mgr.settings.get("click_through", False))
        self.click_through_cb.toggled.connect(self.toggle_click_through)

        self.clamp_cb = QCheckBox()
        self.clamp_cb.setChecked(config_mgr.settings.get("clamp_to_screen", True))
        self.clamp_cb.toggled.connect(self.toggle_clamp_screen)

        gen_layout.addWidget(self.lang_label)
        gen_layout.addWidget(self.lang_combo)
        gen_layout.addWidget(self.tray_cb)
        gen_layout.addWidget(self.click_through_cb)
        gen_layout.addWidget(self.clamp_cb)
        gen_layout.addStretch()
        
        # ==================== 2. 사운드 탭 ====================
        self.tab_sound = QWidget()
        snd_layout = QVBoxLayout(self.tab_sound)
        self.key_sound_ctrl = SoundControlWidget("key_sound", "key")
        self.click_sound_ctrl = SoundControlWidget("click_sound", "click")
        snd_layout.addWidget(self.key_sound_ctrl)
        snd_layout.addWidget(self.click_sound_ctrl)
        snd_layout.addStretch()

        # ==================== 3. 펫 관리 탭 ====================
        self.tab_pets = QWidget()
        pets_layout = QVBoxLayout(self.tab_pets)
        pets_layout.setContentsMargins(10, 10, 10, 10)
        pets_layout.setSpacing(10)

        self.add_pet_btn = QPushButton()
        self.add_pet_btn.clicked.connect(self.add_pet)
        pets_layout.addWidget(self.add_pet_btn)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        pet_content = QWidget()
        self.pet_grid = QGridLayout(pet_content)
        self.pet_grid.setContentsMargins(4, 4, 4, 4)
        self.pet_grid.setSpacing(10)
        self.pet_grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        scroll.setWidget(pet_content)
        pets_layout.addWidget(scroll)
        self.refresh_pet_list()
        
        # ==================== 4. 스킨 편집 탭 ====================
        self.tab_skin = QWidget()
        tab_skin_scroll = QScrollArea()
        tab_skin_scroll.setWidgetResizable(True)
        skin_content = QWidget()
        skin_layout = QVBoxLayout(skin_content)
        skin_layout.setContentsMargins(10, 10, 10, 10)
        skin_layout.setSpacing(12)

        skin_select_box = QGroupBox()
        self.skin_select_box = skin_select_box
        ss_layout = QHBoxLayout(skin_select_box)
        self.skin_selector_combo = QComboBox()
        self.skin_selector_combo.currentTextChanged.connect(self.on_editing_skin_changed)
        
        self.btn_new_skin = QPushButton()
        self.btn_new_skin.clicked.connect(self.create_new_skin)
        self.btn_open_folder = QPushButton()
        self.btn_open_folder.clicked.connect(self.open_current_skin_folder)

        ss_layout.addWidget(self.skin_selector_combo, 2)
        ss_layout.addWidget(self.btn_new_skin, 1)
        ss_layout.addWidget(self.btn_open_folder, 1)
        skin_layout.addWidget(skin_select_box)

        # ★ 1. 모션 압축 정도를 1% ~ 100% 범위로 조절할 수 있도록 설정
        squash_box = QGroupBox()
        self.squash_box = squash_box
        squash_layout = QHBoxLayout(squash_box)
        self.squash_slider = QSlider(Qt.Orientation.Horizontal)
        self.squash_slider.setRange(1, 100)
        self.squash_slider.setValue(20)
        self.squash_slider.valueChanged.connect(self.on_squash_changed)
        self.squash_label = QLabel("20%")
        self.squash_label.setFixedWidth(50)
        self.squash_label.setStyleSheet("font-weight: bold; color: #2563EB;")
        squash_layout.addWidget(self.squash_slider, 1)
        squash_layout.addWidget(self.squash_label)
        skin_layout.addWidget(squash_box)

        base_img_box = QGroupBox()
        self.base_img_box = base_img_box
        base_layout = QVBoxLayout(base_img_box)

        self.idle_label = QLabel()
        h_idle = QHBoxLayout()
        self.idle_input = QLineEdit()
        self.idle_input.textChanged.connect(self.on_base_images_changed)
        self.idle_browse_btn = QPushButton()
        self.idle_browse_btn.clicked.connect(lambda: self.browse_image_for(self.idle_input))
        h_idle.addWidget(self.idle_input, 1)
        h_idle.addWidget(self.idle_browse_btn)

        self.tap1_label = QLabel()
        h_tap1 = QHBoxLayout()
        self.tap1_input = QLineEdit()
        self.tap1_input.textChanged.connect(self.on_base_images_changed)
        self.tap1_browse_btn = QPushButton()
        self.tap1_browse_btn.clicked.connect(lambda: self.browse_image_for(self.tap1_input))
        h_tap1.addWidget(self.tap1_input, 1)
        h_tap1.addWidget(self.tap1_browse_btn)

        self.tap2_label = QLabel()
        h_tap2 = QHBoxLayout()
        self.tap2_input = QLineEdit()
        self.tap2_input.textChanged.connect(self.on_base_images_changed)
        self.tap2_browse_btn = QPushButton()
        self.tap2_browse_btn.clicked.connect(lambda: self.browse_image_for(self.tap2_input))
        h_tap2.addWidget(self.tap2_input, 1)
        h_tap2.addWidget(self.tap2_browse_btn)

        base_layout.addWidget(self.idle_label)
        base_layout.addLayout(h_idle)
        base_layout.addWidget(self.tap1_label)
        base_layout.addLayout(h_tap1)
        base_layout.addWidget(self.tap2_label)
        base_layout.addLayout(h_tap2)
        skin_layout.addWidget(base_img_box)

        # 4-4. 키 및 마우스 매핑 테이블
        mapping_box = QGroupBox()
        self.mapping_box = mapping_box
        map_layout = QVBoxLayout(mapping_box)
        
        self.mapping_table = QTableWidget(0, 3)
        self.mapping_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.mapping_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.mapping_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.mapping_table.verticalHeader().setVisible(False)
        self.mapping_table.setMinimumHeight(170)
        self.mapping_table.setShowGrid(False)
        map_layout.addWidget(self.mapping_table)

        map_btn_layout = QHBoxLayout()
        self.btn_add_map = QPushButton()
        self.btn_add_map.clicked.connect(self.add_mapping_row)
        self.btn_del_map = QPushButton()
        self.btn_del_map.clicked.connect(self.delete_mapping_row)
        map_btn_layout.addWidget(self.btn_add_map)
        map_btn_layout.addWidget(self.btn_del_map)
        map_layout.addLayout(map_btn_layout)
        skin_layout.addWidget(mapping_box)

        pkg_box = QGroupBox()
        self.pkg_box = pkg_box
        pkg_layout = QHBoxLayout(pkg_box)
        self.btn_import = QPushButton()
        self.btn_import.clicked.connect(self.import_skin)
        self.btn_export = QPushButton()
        self.btn_export.clicked.connect(self.export_skin)
        pkg_layout.addWidget(self.btn_import)
        pkg_layout.addWidget(self.btn_export)
        skin_layout.addWidget(pkg_box)

        tab_skin_scroll.setWidget(skin_content)
        skin_main_layout = QVBoxLayout(self.tab_skin)
        skin_main_layout.setContentsMargins(0, 0, 0, 0)
        skin_main_layout.addWidget(tab_skin_scroll)

        self.tabs.addTab(self.tab_general, "")
        self.tabs.addTab(self.tab_sound, "")
        self.tabs.addTab(self.tab_pets, "")
        self.tabs.addTab(self.tab_skin, "")
        content_layout.addWidget(self.tabs)

        root_layout.addWidget(content_container)
        outer_layout.addWidget(self.root_widget)

    def toggle_theme(self):
        """다크 / 라이트 모드 전환"""
        self.is_dark_mode = not self.is_dark_mode
        config_mgr.settings["dark_mode"] = self.is_dark_mode
        config_mgr.save_global_settings()
        self.apply_theme()

    def apply_theme(self):
        theme = DARK_THEME if self.is_dark_mode else LIGHT_THEME
        self.setStyleSheet(theme)
        self.title_bar.theme_btn.setText("Light" if self.is_dark_mode else "Dark")
        # 테마 변경 시 테이블 내부 셀 위젯 스타일도 동기화 갱신
        self.refresh_table_widgets_style()

    def refresh_table_widgets_style(self):
        """테이블 내부에 동적으로 추가된 셀 위젯들의 스타일을 현재 테마에 맞게 갱신"""
        bg_btn = "#27272A" if self.is_dark_mode else "#F3F4F6"
        border_btn = "#3F3F46" if self.is_dark_mode else "#E5E7EB"
        text_btn = "#F4F4F5" if self.is_dark_mode else "#1F2937"
        bg_input = "#27272A" if self.is_dark_mode else "#FFFFFF"
        border_input = "#3F3F46" if self.is_dark_mode else "#D1D5DB"
        text_input = "#F4F4F5" if self.is_dark_mode else "#111827"

        btn_qss = f"""
            QPushButton {{
                background-color: {bg_btn};
                border: 1px solid {border_btn};
                border-radius: 6px;
                padding: 4px 8px;
                color: {text_btn};
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {"#3F3F46" if self.is_dark_mode else "#E5E7EB"};
            }}
        """
        line_qss = f"""
            QLineEdit {{
                background-color: {bg_input};
                border: 1px solid {border_input};
                border-radius: 6px;
                padding: 4px 8px;
                color: {text_input};
            }}
            QLineEdit:focus {{
                border-color: {"#FAFAFA" if self.is_dark_mode else "#111827"};
            }}
        """

        for r in range(self.mapping_table.rowCount()):
            w0 = self.mapping_table.cellWidget(r, 0)
            w1 = self.mapping_table.cellWidget(r, 1)
            w2 = self.mapping_table.cellWidget(r, 2)
            if w0 and not getattr(w0, 'capturing', False):
                w0.setStyleSheet(btn_qss)
            if w1:
                w1.setStyleSheet(line_qss)
            if w2:
                w2.setStyleSheet(btn_qss)

    def retranslate_ui(self):
        self.title_bar.title_label.setText(I18n.tr("settings_title"))
        self.tabs.setTabText(0, I18n.tr("tab_general"))
        self.tabs.setTabText(1, I18n.tr("tab_sound"))
        self.tabs.setTabText(2, I18n.tr("tab_pets"))
        self.tabs.setTabText(3, I18n.tr("tab_skin"))
        
        self.lang_label.setText(I18n.tr("language"))
        self.tray_cb.setText(I18n.tr("tray_mode"))
        self.click_through_cb.setText(I18n.tr("click_through"))
        self.clamp_cb.setText(I18n.tr("clamp_to_screen"))
        self.add_pet_btn.setText(I18n.tr("add_pet"))

        self.skin_select_box.setTitle(I18n.tr("current_skin"))
        self.btn_new_skin.setText(I18n.tr("create_skin"))
        self.btn_open_folder.setText(I18n.tr("open_skin_folder"))

        self.squash_box.setTitle(I18n.tr("squash_depth"))
        self.base_img_box.setTitle(I18n.tr("tab_skin"))
        self.idle_label.setText(I18n.tr("idle_image"))
        self.tap1_label.setText(I18n.tr("tap1_image"))
        self.tap2_label.setText(I18n.tr("tap2_image"))
        self.idle_browse_btn.setText(I18n.tr("browse"))
        self.tap1_browse_btn.setText(I18n.tr("browse"))
        self.tap2_browse_btn.setText(I18n.tr("browse"))

        self.mapping_box.setTitle(I18n.tr("key_mapping_title"))
        self.mapping_table.setHorizontalHeaderLabels([
            I18n.tr("col_input"), I18n.tr("col_image"), I18n.tr("col_browse")
        ])
        self.btn_add_map.setText(I18n.tr("add_mapping"))
        self.btn_del_map.setText(I18n.tr("del_mapping"))

        self.pkg_box.setTitle(I18n.tr("skin_pkg_manage"))
        self.btn_import.setText(I18n.tr("import_skin"))
        self.btn_export.setText(I18n.tr("export_skin"))

    def load_skin_list(self):
        os.makedirs(SKINS_DIR, exist_ok=True)
        skins = [d for d in os.listdir(SKINS_DIR) if os.path.isdir(os.path.join(SKINS_DIR, d))]
        if not skins:
            skins = ["default"]
            os.makedirs(os.path.join(SKINS_DIR, "default"), exist_ok=True)
            
        self.skin_selector_combo.blockSignals(True)
        self.skin_selector_combo.clear()
        self.skin_selector_combo.addItems(sorted(skins))
        if self.current_editing_skin in skins:
            self.skin_selector_combo.setCurrentText(self.current_editing_skin)
        else:
            self.current_editing_skin = skins[0]
            self.skin_selector_combo.setCurrentText(self.current_editing_skin)
        self.skin_selector_combo.blockSignals(False)

    def on_editing_skin_changed(self, skin_name):
        if not skin_name:
            return
        self.current_editing_skin = skin_name
        self.load_current_skin_config()

    def load_current_skin_config(self):
        self.is_loading_skin = True
        self.skin_data = config_mgr.get_skin_config(self.current_editing_skin)

        # 1% ~ 100% 범위 대응
        squash_val = float(self.skin_data.get("squash_depth", 0.20))
        val_pct = max(1, min(100, int(round(squash_val * 100))))
        self.squash_slider.setValue(val_pct)
        self.squash_label.setText(f"{val_pct}%")

        self.idle_input.setText(self.skin_data.get("idle_image", "idle.png"))
        tap_list = self.skin_data.get("tap_images", ["tap_left.png", "tap_right.png"])
        t1 = tap_list[0] if len(tap_list) > 0 else "tap_left.png"
        t2 = tap_list[1] if len(tap_list) > 1 else t1
        self.tap1_input.setText(t1)
        self.tap2_input.setText(t2)

        mappings = self.skin_data.get("key_mappings", {})
        self.mapping_table.setRowCount(0)
        for key, img in mappings.items():
            self.insert_mapping_row(key, img)

        self.is_loading_skin = False

    def save_current_skin_to_file(self):
        if self.is_loading_skin:
            return

        squash = round(self.squash_slider.value() / 100.0, 2)
        idle = self.idle_input.text().strip() or "idle.png"
        t1 = self.tap1_input.text().strip() or "tap_left.png"
        t2 = self.tap2_input.text().strip() or t1

        mappings = {}
        for r in range(self.mapping_table.rowCount()):
            key_widget = self.mapping_table.cellWidget(r, 0)
            img_widget = self.mapping_table.cellWidget(r, 1)
            
            if isinstance(key_widget, KeyCaptureButton) and isinstance(img_widget, QLineEdit):
                k = key_widget.text().strip()
                img = img_widget.text().strip()
                
                is_placeholder = any(tag in k for tag in ["대기", "감지", "Wait", "Detecting", "..."])
                if k and img and not is_placeholder:
                    clean_k = k.lower() if not any(c in "!@#$%^&*()_+{}|:\"<>?~`-=[]\\;',./" for c in k) else k
                    mappings[clean_k] = img

        save_dict = {
            "name": self.current_editing_skin,
            "squash_depth": squash,
            "idle_image": idle,
            "tap_images": [t1, t2],
            "key_mappings": mappings
        }
        
        self.skin_data = save_dict
        config_mgr.save_skin_config(self.current_editing_skin, save_dict)
        self.settings_changed.emit()

    def on_squash_changed(self, value):
        self.squash_label.setText(f"{value}%")
        self.save_current_skin_to_file()

    def on_base_images_changed(self):
        self.save_current_skin_to_file()

    def create_new_skin(self):
        name, ok = QInputDialog.getText(self, I18n.tr("create_skin"), I18n.tr("create_skin_prompt"))
        if ok and name.strip():
            name = name.strip()
            folder_path = os.path.join(SKINS_DIR, name)
            if os.path.exists(folder_path):
                QMessageBox.warning(self, I18n.tr("error"), I18n.tr("skin_exists_warn"))
                return

            os.makedirs(folder_path, exist_ok=True)
            default_conf = {
                "name": name,
                "squash_depth": 0.20,
                "idle_image": "idle.png",
                "tap_images": ["tap_left.png", "tap_right.png"],
                "key_mappings": {}
            }
            config_mgr.save_skin_config(name, default_conf)
            
            self.load_skin_list()
            self.skin_selector_combo.setCurrentText(name)
            self.refresh_pet_list()

    def open_current_skin_folder(self):
        folder_path = os.path.join(SKINS_DIR, self.current_editing_skin)
        os.makedirs(folder_path, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath(folder_path)))

    def browse_image_for(self, target_line_edit: QLineEdit):
        skin_folder = os.path.join(SKINS_DIR, self.current_editing_skin)
        os.makedirs(skin_folder, exist_ok=True)
        file_path, _ = QFileDialog.getOpenFileName(
            self, I18n.tr("select_wav"), skin_folder, I18n.tr("image_filter")
        )
        if file_path:
            rel_name = os.path.basename(file_path)
            target_line_edit.setText(rel_name)
            self.save_current_skin_to_file()

    def insert_mapping_row(self, key_text, img_text):
        """★ 2. 매핑 행 추가 시 현재 테마와 통일된 모던 플랫 UI 스타일 적용"""
        row = self.mapping_table.rowCount()
        self.mapping_table.insertRow(row)
        self.mapping_table.setRowHeight(row, 36)

        bg_btn = "#27272A" if self.is_dark_mode else "#F3F4F6"
        border_btn = "#3F3F46" if self.is_dark_mode else "#E5E7EB"
        text_btn = "#F4F4F5" if self.is_dark_mode else "#1F2937"
        bg_input = "#27272A" if self.is_dark_mode else "#FFFFFF"
        border_input = "#3F3F46" if self.is_dark_mode else "#D1D5DB"
        text_input = "#F4F4F5" if self.is_dark_mode else "#111827"

        btn_qss = f"""
            QPushButton {{
                background-color: {bg_btn};
                border: 1px solid {border_btn};
                border-radius: 6px;
                padding: 4px 8px;
                color: {text_btn};
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {"#3F3F46" if self.is_dark_mode else "#E5E7EB"};
            }}
            QPushButton[activeCapture="true"] {{
                background-color: {"#78350F" if self.is_dark_mode else "#FEF3C7"};
                border: 1px solid #F59E0B;
                color: {"#FEF3C7" if self.is_dark_mode else "#92400E"};
            }}
        """

        line_qss = f"""
            QLineEdit {{
                background-color: {bg_input};
                border: 1px solid {border_input};
                border-radius: 6px;
                padding: 4px 8px;
                color: {text_input};
            }}
            QLineEdit:focus {{
                border-color: {"#FAFAFA" if self.is_dark_mode else "#111827"};
            }}
        """

        # 1. 키 캡처 버튼 (통일된 스타일 부여)
        btn_key = KeyCaptureButton(key_text or I18n.tr("input_waiting"))
        btn_key.setStyleSheet(btn_qss)
        btn_key.keyCaptured.connect(lambda captured: self.on_key_captured_in_row(btn_key, captured))
        self.mapping_table.setCellWidget(row, 0, btn_key)

        # 2. 이미지 파일명 입력 필드
        line_edit = QLineEdit(img_text)
        line_edit.setStyleSheet(line_qss)
        line_edit.textChanged.connect(lambda _: self.save_current_skin_to_file())
        self.mapping_table.setCellWidget(row, 1, line_edit)

        # 3. 찾아보기 버튼
        pick_btn = QPushButton(I18n.tr("col_browse"))
        pick_btn.setStyleSheet(btn_qss)
        pick_btn.clicked.connect(lambda _, le=line_edit: self.browse_image_for(le))
        self.mapping_table.setCellWidget(row, 2, pick_btn)

    def on_key_captured_in_row(self, button_widget: KeyCaptureButton, captured_key: str):
        button_widget.setText(captured_key)
        self.save_current_skin_to_file()

    def add_mapping_row(self):
        self.insert_mapping_row("space", "tap_left.png")
        self.save_current_skin_to_file()

    def delete_mapping_row(self):
        r = self.mapping_table.currentRow()
        if r >= 0:
            self.mapping_table.removeRow(r)
            self.save_current_skin_to_file()

    def change_language(self, index):
        lang_code = self.lang_combo.itemData(index)
        if lang_code:
            I18n.set_language(lang_code)
            config_mgr.settings["language"] = lang_code
            config_mgr.save_global_settings()

    def toggle_tray_mode(self, checked):
        config_mgr.settings["tray_mode"] = checked
        config_mgr.save_global_settings()
        self.settings_changed.emit()

    def toggle_click_through(self, checked):
        config_mgr.settings["click_through"] = checked
        config_mgr.save_global_settings()
        self.settings_changed.emit()

    def toggle_clamp_screen(self, checked):
        config_mgr.settings["clamp_to_screen"] = checked
        config_mgr.save_global_settings()

    def add_pet(self):
        new_pet = {"id": str(uuid.uuid4()), "skin": self.current_editing_skin, "scale": 1.0, "x": 150, "y": 150}
        config_mgr.settings["instances"].append(new_pet)
        config_mgr.save_global_settings()
        self.refresh_pet_list()
        self.settings_changed.emit()

    def remove_pet(self, widget):
        # 0마리까지 완전 삭제 지원
        if widget.instance_data in config_mgr.settings["instances"]:
            config_mgr.settings["instances"].remove(widget.instance_data)
            config_mgr.save_global_settings()
            self.refresh_pet_list()
            self.settings_changed.emit()

    def refresh_pet_list(self):
        while self.pet_grid.count():
            item = self.pet_grid.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        self.pet_cards.clear()
        columns = 3
        for idx, inst in enumerate(config_mgr.settings["instances"]):
            row = idx // columns
            col = idx % columns
            card = PetCardWidget(inst, self.remove_pet)
            card.changed.connect(self.settings_changed.emit)
            self.pet_grid.addWidget(card, row, col)
            
            p_id = inst.get("id")
            if p_id:
                self.pet_cards[p_id] = card

    def update_pet_card_scale(self, pet_id, scale_val):
        if pet_id in self.pet_cards:
            self.pet_cards[pet_id].sync_scale_from_external(scale_val)
            inst = next((i for i in config_mgr.settings["instances"] if i.get("id") == pet_id), None)
            if inst:
                self.pet_cards[pet_id].sync_skin(inst.get("skin", "default"))

    def import_skin(self):
        path, _ = QFileDialog.getOpenFileName(self, I18n.tr("open_skin_zip"), "", I18n.tr("zip_filter"))
        if not path: return
        skin_name = os.path.splitext(os.path.basename(path))[0]
        target_dir = os.path.join(SKINS_DIR, skin_name)
        try:
            with zipfile.ZipFile(path, 'r') as zip_ref:
                zip_ref.extractall(target_dir)
            self.load_skin_list()
            self.refresh_pet_list()
            QMessageBox.information(self, I18n.tr("complete"), f"'{skin_name}' {I18n.tr('import_success')}")
        except Exception as e:
            QMessageBox.critical(self, I18n.tr("error"), f"{I18n.tr('import_fail')}\n{e}")

    def export_skin(self):
        source_dir = os.path.join(SKINS_DIR, self.current_editing_skin)
        save_path, _ = QFileDialog.getSaveFileName(self, I18n.tr("save_skin_zip"), f"{self.current_editing_skin}.zip", I18n.tr("zip_filter"))
        if not save_path: return
        try:
            shutil.make_archive(save_path.replace('.zip',''), 'zip', source_dir)
            QMessageBox.information(self, I18n.tr("complete"), I18n.tr("export_success"))
        except Exception as e:
            QMessageBox.critical(self, I18n.tr("error"), f"{I18n.tr('export_fail')}\n{e}")