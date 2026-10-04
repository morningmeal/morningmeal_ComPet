# ui/settings/tab_pet.py
import os
import uuid
import zipfile
import shutil
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QScrollArea,
    QPushButton, QLabel, QLineEdit, QComboBox, QFrame, QSpinBox,
    QSlider, QGroupBox, QTableWidget, QHeaderView, QFileDialog,
    QMessageBox, QInputDialog, QAbstractSpinBox, QCheckBox, QTabWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QUrl
from PyQt6.QtGui import QDesktopServices, QPixmap, QFontMetrics
from core.config_manager import config_mgr, SKINS_DIR
from core.i18n import I18n
from ui.components import KeyCaptureButton

class PetCardWidget(QFrame):
    changed = pyqtSignal()

    def __init__(self, pet_data, remove_callback, parent=None):
        super().__init__(parent)
        self.pet_data = pet_data
        self.remove_callback = remove_callback
        self.setFixedWidth(170)
        self.update_card_style()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        # 삭제 버튼
        top = QHBoxLayout()
        top.addStretch()
        del_btn = QPushButton("✕")
        del_btn.setFixedSize(20, 20)
        del_btn.setStyleSheet("QPushButton { border: none; background: transparent; font-size: 11px; color: #94A3B8; } QPushButton:hover { color: #EF4444; }")
        del_btn.clicked.connect(lambda: self.remove_callback(self.pet_data))
        top.addWidget(del_btn)
        layout.addLayout(top)

        # 프리뷰 라벨
        self.preview_label = QLabel()
        self.preview_label.setFixedSize(70, 70)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("background-color: rgba(128,128,128,0.06); border: 1px dashed #CBD5E1; border-radius: 6px;")
        p_box = QHBoxLayout()
        p_box.addStretch()
        p_box.addWidget(self.preview_label)
        p_box.addStretch()
        layout.addLayout(p_box)

        # 스킨 선택 콤보박스
        self.skin_combo = QComboBox()
        self.skin_combo.setStyleSheet("font-size: 11px;")
        self.refresh_skins()
        self.skin_combo.setCurrentText(self.pet_data.get("skin", "default"))
        self.skin_combo.currentTextChanged.connect(self.on_skin_changed)
        layout.addWidget(self.skin_combo)

        # 크기 조절 (10% ~ 150%, 5% 스텝)
        size_layout = QHBoxLayout()
        self.lbl_size = QLabel(I18n.tr("size_label"))
        self.lbl_size.setStyleSheet("font-size: 11px; color: #64748B;")
        cur_pct = int(self.pet_data.get("scale", 1.0) * 100)
        self.scale_spin = QSpinBox()
        self.scale_spin.setRange(10, 150)
        self.scale_spin.setSingleStep(5)
        self.scale_spin.setValue(cur_pct)
        self.scale_spin.setSuffix("%")
        self.scale_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.scale_spin.setStyleSheet("font-size: 11px; font-weight: bold; color: #2563EB;")
        self.scale_spin.valueChanged.connect(self.on_scale_changed)
        size_layout.addWidget(self.lbl_size)
        size_layout.addStretch()
        size_layout.addWidget(self.scale_spin)
        layout.addLayout(size_layout)

        # 결합 타이머 지정 드롭다운
        t_box = QVBoxLayout()
        self.lbl_bound = QLabel(I18n.tr("bound_timer_label"))
        self.lbl_bound.setStyleSheet("font-size: 11px; color: #64748B;")
        self.bound_combo = QComboBox()
        self.bound_combo.setStyleSheet("font-size: 11px;")
        self.refresh_timers()
        self.bound_combo.currentIndexChanged.connect(self.on_bound_timer_changed)
        t_box.addWidget(self.lbl_bound)
        t_box.addWidget(self.bound_combo)
        layout.addLayout(t_box)

        self.update_preview()

    def update_card_style(self):
        is_dark = config_mgr.config.get("settings", {}).get("dark_mode", False)
        bg = "#27272A" if is_dark else "#FFFFFF"
        border = "#3F3F46" if is_dark else "#D0D7DE"
        text_color = "#FAFAFA" if is_dark else "#111827"
        self.setStyleSheet(f"""
            PetCardWidget {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 8px;
            }}
            QLabel {{ color: {text_color}; }}
        """)

    def refresh_skins(self):
        self.skin_combo.blockSignals(True)
        self.skin_combo.clear()
        skins = [d for d in os.listdir(SKINS_DIR) if os.path.isdir(os.path.join(SKINS_DIR, d))]
        self.skin_combo.addItems(sorted(skins))
        self.skin_combo.blockSignals(False)

    def refresh_timers(self):
        self.bound_combo.blockSignals(True)
        self.bound_combo.clear()
        self.bound_combo.addItem(I18n.tr("unbound"), "")
        cur_bound = self.pet_data.get("bound_timer_id", "")
        sel_idx = 0
        for idx, t in enumerate(config_mgr.config.get("timers", [])):
            name = t.get("name", I18n.tr("default_timer_name"))
            t_id = t.get("id")
            self.bound_combo.addItem(name, t_id)
            if t_id == cur_bound: sel_idx = idx + 1
        self.bound_combo.setCurrentIndex(sel_idx)
        self.bound_combo.blockSignals(False)

    def on_skin_changed(self, skin_name):
        if not skin_name: return
        self.pet_data["skin"] = skin_name
        config_mgr.save_config()
        self.update_preview()
        self.changed.emit()

    def on_scale_changed(self, val):
        self.pet_data["scale"] = val / 100.0
        config_mgr.save_config()
        self.changed.emit()

    def on_bound_timer_changed(self, idx):
        t_id = self.bound_combo.itemData(idx)
        if t_id:
            for p in config_mgr.config.get("pets", []):
                if p.get("bound_timer_id") == t_id and p.get("id") != self.pet_data.get("id"):
                    p["bound_timer_id"] = ""
        self.pet_data["bound_timer_id"] = t_id or ""
        config_mgr.save_config()
        self.changed.emit()

    def update_preview(self):
        skin = self.pet_data.get("skin", "default")
        conf = config_mgr.get_skin_config(skin)
        idle_file = os.path.join(SKINS_DIR, skin, conf.get("idle_image", "idle.png"))
        if os.path.exists(idle_file):
            pix = QPixmap(idle_file)
            if not pix.isNull():
                self.preview_label.setPixmap(pix.scaled(60, 60, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                return
        self.preview_label.clear()
        self.preview_label.setText("No Img")

    def retranslate_ui(self):
        self.lbl_size.setText(I18n.tr("size_label"))
        self.lbl_bound.setText(I18n.tr("bound_timer_label"))
        self.refresh_timers()


class TabPetSettings(QWidget):
    settings_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_editing_skin = "default"
        self.is_loading_skin = False
        self.init_ui()
        self.load_skin_list()
        self.load_current_skin_config()
        I18n.language_changed.connect(self.retranslate_ui)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 8, 4, 4)

        self.sub_tabs = QTabWidget()
        self.sub_tabs.setObjectName("subTabWidget")

        # ==================== 1. 일반 설정 서브 탭 ====================
        self.sub_page_general = QWidget()
        layout_general = QVBoxLayout(self.sub_page_general)
        layout_general.setContentsMargins(14, 14, 14, 14)
        layout_general.setSpacing(12)

        self.clamp_cb = QCheckBox(I18n.tr("clamp_to_screen"))
        self.clamp_cb.setChecked(config_mgr.config.get("settings", {}).get("clamp_to_screen", True))
        self.clamp_cb.toggled.connect(lambda c: self.save_opt("clamp_to_screen", c))

        self.click_thru_cb = QCheckBox(I18n.tr("click_through"))
        self.click_thru_cb.setChecked(config_mgr.config.get("settings", {}).get("click_through", False))
        self.click_thru_cb.toggled.connect(lambda c: self.save_opt("click_through", c))

        layout_general.addWidget(self.clamp_cb)
        layout_general.addWidget(self.click_thru_cb)
        layout_general.addStretch()

        # ==================== 2. 활성 펫 관리 서브 탭 ====================
        self.sub_page_pets = QWidget()
        layout_pets = QVBoxLayout(self.sub_page_pets)
        layout_pets.setContentsMargins(10, 10, 10, 10)
        layout_pets.setSpacing(10)

        top_pets = QHBoxLayout()
        top_pets.addStretch()
        self.btn_add_pet = QPushButton(I18n.tr("add_pet"))
        self.btn_add_pet.setFixedHeight(30)
        self.btn_add_pet.clicked.connect(self.add_pet)
        top_pets.addWidget(self.btn_add_pet)
        layout_pets.addLayout(top_pets)

        scroll_pets = QScrollArea()
        scroll_pets.setWidgetResizable(True)
        p_content = QWidget()
        self.pet_grid = QGridLayout(p_content)
        self.pet_grid.setContentsMargins(4, 4, 4, 4)
        self.pet_grid.setSpacing(10)
        self.pet_grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        scroll_pets.setWidget(p_content)
        layout_pets.addWidget(scroll_pets)

        # ==================== 3. 스킨 에디터 서브 탭 ====================
        self.sub_page_skin = QWidget()
        tab_skin_scroll = QScrollArea()
        tab_skin_scroll.setWidgetResizable(True)
        skin_content = QWidget()
        layout_skin = QVBoxLayout(skin_content)
        layout_skin.setContentsMargins(10, 10, 10, 10)
        layout_skin.setSpacing(14)

        # 상단 스킨 선택 바
        bar_s = QHBoxLayout()
        self.skin_combo = QComboBox()
        self.skin_combo.currentTextChanged.connect(self.on_skin_selected)
        self.btn_new_skin = QPushButton(I18n.tr("create_skin"))
        self.btn_new_skin.clicked.connect(self.create_new_skin)
        self.btn_open_folder = QPushButton(I18n.tr("open_skin_folder"))
        self.btn_open_folder.clicked.connect(self.open_skin_folder)

        bar_s.addWidget(self.skin_combo, 2)
        bar_s.addWidget(self.btn_new_skin, 1)
        bar_s.addWidget(self.btn_open_folder, 1)
        layout_skin.addLayout(bar_s)

        # 스킨별 바운스(압축) 애니메이션 On/Off 체크박스
        self.skin_bounce_cb = QCheckBox(I18n.tr("enable_bounce_animation", "바운스 애니메이션"))
        self.skin_bounce_cb.toggled.connect(self.on_skin_bounce_toggled)
        layout_skin.addWidget(self.skin_bounce_cb)

        # 모션 압축 강도 슬라이더
        squash_layout = QHBoxLayout()
        self.lbl_squash_title = QLabel(I18n.tr("squash_depth"))
        self.squash_slider = QSlider(Qt.Orientation.Horizontal)
        self.squash_slider.setRange(1, 100)
        self.squash_slider.valueChanged.connect(self.on_squash_slider)
        self.squash_lbl = QLabel("20%")
        self.squash_lbl.setFixedWidth(40)
        squash_layout.addWidget(self.lbl_squash_title)
        squash_layout.addWidget(self.squash_slider, 1)
        squash_layout.addWidget(self.squash_lbl)
        layout_skin.addLayout(squash_layout)

        # ★ [3열 균등 정렬] 기본 모션 이미지 설정 영역 (배경/윤곽선 없음)
        self.base_motions_widget = QWidget()
        self.base_motions_widget.setObjectName("baseMotionsWidget")
        self.base_motions_widget.setStyleSheet("#baseMotionsWidget { background: transparent; border: none; }")
        
        # QGridLayout을 통해 3개 컬럼의 너비를 동일 비율(1:1:1)로 균등 분할
        motions_grid = QGridLayout(self.base_motions_widget)
        motions_grid.setContentsMargins(0, 4, 0, 4)
        motions_grid.setHorizontalSpacing(16)
        motions_grid.setVerticalSpacing(0)
        motions_grid.setColumnStretch(0, 1)
        motions_grid.setColumnStretch(1, 1)
        motions_grid.setColumnStretch(2, 1)

        preview_qss = "background-color: rgba(128,128,128,0.06); border: 1px dashed rgba(150,150,150,0.3); border-radius: 8px;"
        btn_qss = """
            QPushButton {
                background-color: #F3F4F6;
                border: 1px solid #D1D5DB;
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: 500;
                color: #374151;
            }
            QPushButton:hover {
                background-color: #E5E7EB;
                color: #111827;
            }
        """

        # 1) 열 1: idle
        widget_col_idle = QWidget()
        col_idle = QVBoxLayout(widget_col_idle)
        col_idle.setContentsMargins(0, 0, 0, 0)
        col_idle.setSpacing(6)
        col_idle.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)

        self.idle_label = QLabel(I18n.tr("idle_image"))
        self.idle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.idle_label.setStyleSheet("font-weight: 600; font-size: 11px;")
        
        self.idle_preview = QLabel("No Img")
        self.idle_preview.setFixedSize(96, 96)
        self.idle_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.idle_preview.setStyleSheet(preview_qss)

        self.idle_name_lbl = QLabel("idle.png")
        self.idle_name_lbl.setFixedWidth(130)
        self.idle_name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.idle_name_lbl.setStyleSheet("font-size: 11px; color: #64748B; padding: 2px;")

        self.idle_browse_btn = QPushButton(I18n.tr("browse"))
        self.idle_browse_btn.setFixedWidth(96)
        self.idle_browse_btn.setStyleSheet(btn_qss)
        self.idle_browse_btn.clicked.connect(lambda: self.browse_base_image("idle"))

        col_idle.addWidget(self.idle_label, alignment=Qt.AlignmentFlag.AlignHCenter)
        col_idle.addWidget(self.idle_preview, alignment=Qt.AlignmentFlag.AlignHCenter)
        col_idle.addWidget(self.idle_name_lbl, alignment=Qt.AlignmentFlag.AlignHCenter)
        col_idle.addWidget(self.idle_browse_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        # 2) 열 2: tap1 (왼손)
        widget_col_tap1 = QWidget()
        col_tap1 = QVBoxLayout(widget_col_tap1)
        col_tap1.setContentsMargins(0, 0, 0, 0)
        col_tap1.setSpacing(6)
        col_tap1.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)

        self.tap1_label = QLabel(I18n.tr("tap1_image"))
        self.tap1_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tap1_label.setStyleSheet("font-weight: 600; font-size: 11px;")

        self.tap1_preview = QLabel("No Img")
        self.tap1_preview.setFixedSize(96, 96)
        self.tap1_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tap1_preview.setStyleSheet(preview_qss)

        self.tap1_name_lbl = QLabel("tap_left.png")
        self.tap1_name_lbl.setFixedWidth(130)
        self.tap1_name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tap1_name_lbl.setStyleSheet("font-size: 11px; color: #64748B; padding: 2px;")

        self.tap1_browse_btn = QPushButton(I18n.tr("browse"))
        self.tap1_browse_btn.setFixedWidth(96)
        self.tap1_browse_btn.setStyleSheet(btn_qss)
        self.tap1_browse_btn.clicked.connect(lambda: self.browse_base_image("tap1"))

        col_tap1.addWidget(self.tap1_label, alignment=Qt.AlignmentFlag.AlignHCenter)
        col_tap1.addWidget(self.tap1_preview, alignment=Qt.AlignmentFlag.AlignHCenter)
        col_tap1.addWidget(self.tap1_name_lbl, alignment=Qt.AlignmentFlag.AlignHCenter)
        col_tap1.addWidget(self.tap1_browse_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        # 3) 열 3: tap2 (오른손)
        widget_col_tap2 = QWidget()
        col_tap2 = QVBoxLayout(widget_col_tap2)
        col_tap2.setContentsMargins(0, 0, 0, 0)
        col_tap2.setSpacing(6)
        col_tap2.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)

        self.tap2_label = QLabel(I18n.tr("tap2_image"))
        self.tap2_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tap2_label.setStyleSheet("font-weight: 600; font-size: 11px;")

        self.tap2_preview = QLabel("No Img")
        self.tap2_preview.setFixedSize(96, 96)
        self.tap2_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tap2_preview.setStyleSheet(preview_qss)

        self.tap2_name_lbl = QLabel("tap_right.png")
        self.tap2_name_lbl.setFixedWidth(130)
        self.tap2_name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tap2_name_lbl.setStyleSheet("font-size: 11px; color: #64748B; padding: 2px;")

        self.tap2_browse_btn = QPushButton(I18n.tr("browse"))
        self.tap2_browse_btn.setFixedWidth(96)
        self.tap2_browse_btn.setStyleSheet(btn_qss)
        self.tap2_browse_btn.clicked.connect(lambda: self.browse_base_image("tap2"))

        col_tap2.addWidget(self.tap2_label, alignment=Qt.AlignmentFlag.AlignHCenter)
        col_tap2.addWidget(self.tap2_preview, alignment=Qt.AlignmentFlag.AlignHCenter)
        col_tap2.addWidget(self.tap2_name_lbl, alignment=Qt.AlignmentFlag.AlignHCenter)
        col_tap2.addWidget(self.tap2_browse_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        motions_grid.addWidget(widget_col_idle, 0, 0, Qt.AlignmentFlag.AlignHCenter)
        motions_grid.addWidget(widget_col_tap1, 0, 1, Qt.AlignmentFlag.AlignHCenter)
        motions_grid.addWidget(widget_col_tap2, 0, 2, Qt.AlignmentFlag.AlignHCenter)
        layout_skin.addWidget(self.base_motions_widget)

        # 키 매핑 섹션 라벨 및 테이블
        self.lbl_key_map = QLabel(I18n.tr("key_mapping_section"))
        self.lbl_key_map.setStyleSheet("font-weight: 600; font-size: 12px; margin-top: 4px; color: #4B5563;")
        layout_skin.addWidget(self.lbl_key_map)

        self.map_table = QTableWidget(0, 3)
        self.map_table.setHorizontalHeaderLabels([
            I18n.tr("col_input"), I18n.tr("col_image"), I18n.tr("col_browse")
        ])
        header = self.map_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.map_table.verticalHeader().setVisible(False)
        self.map_table.setShowGrid(False)
        self.map_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        is_dark = config_mgr.config.get("settings", {}).get("dark_mode", False)
        t_border = "#27272A" if is_dark else "#E5E7EB"
        t_bg = "#18181B" if is_dark else "#FFFFFF"
        th_bg = "#202024" if is_dark else "#F9FAFB"
        th_color = "#A1A1AA" if is_dark else "#6B7280"

        self.map_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {t_bg};
                border: 1px solid {t_border};
                border-radius: 8px;
                padding: 4px;
            }}
            QHeaderView::section {{
                background-color: {th_bg};
                color: {th_color};
                font-weight: 600;
                font-size: 11px;
                border: none;
                border-bottom: 1px solid {t_border};
                padding: 6px 4px;
            }}
        """)
        layout_skin.addWidget(self.map_table)

        btn_map_box = QHBoxLayout()
        self.btn_add_m = QPushButton(I18n.tr("add_mapping"))
        self.btn_add_m.clicked.connect(self.add_mapping_row)
        self.btn_del_m = QPushButton(I18n.tr("del_mapping"))
        self.btn_del_m.clicked.connect(self.del_mapping_row)
        btn_map_box.addWidget(self.btn_add_m)
        btn_map_box.addWidget(self.btn_del_m)
        btn_map_box.addStretch()

        self.btn_imp = QPushButton(I18n.tr("import_skin"))
        self.btn_imp.clicked.connect(self.import_skin)
        self.btn_exp = QPushButton(I18n.tr("export_skin"))
        self.btn_exp.clicked.connect(self.export_skin)
        btn_map_box.addWidget(self.btn_imp)
        btn_map_box.addWidget(self.btn_exp)
        layout_skin.addLayout(btn_map_box)

        tab_skin_scroll.setWidget(skin_content)
        skin_sub_layout = QVBoxLayout(self.sub_page_skin)
        skin_sub_layout.setContentsMargins(0, 0, 0, 0)
        skin_sub_layout.addWidget(tab_skin_scroll)

        # 3개 서브 탭 등록
        self.sub_tabs.addTab(self.sub_page_general, I18n.tr("tab_general"))
        self.sub_tabs.addTab(self.sub_page_pets, I18n.tr("subtab_pet_list"))
        self.sub_tabs.addTab(self.sub_page_skin, I18n.tr("subtab_skin_editor"))

        main_layout.addWidget(self.sub_tabs)
        self.refresh_pet_list()

    def save_opt(self, key, val):
        config_mgr.config.setdefault("settings", {})[key] = val
        config_mgr.save_config()
        self.settings_changed.emit()

    def add_pet(self):
        new_pet = {
            "id": str(uuid.uuid4()),
            "skin": self.current_editing_skin,
            "scale": 1.0, "x": 250, "y": 250,
            "bound_timer_id": ""
        }
        config_mgr.config.setdefault("pets", []).append(new_pet)
        config_mgr.save_config()
        self.refresh_pet_list()
        self.settings_changed.emit()

    def remove_pet(self, pet_data):
        if pet_data in config_mgr.config.get("pets", []):
            config_mgr.config["pets"].remove(pet_data)
            config_mgr.save_config()
            self.refresh_pet_list()
            self.settings_changed.emit()

    def refresh_pet_list(self):
        while self.pet_grid.count():
            item = self.pet_grid.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        for idx, p in enumerate(config_mgr.config.get("pets", [])):
            card = PetCardWidget(p, self.remove_pet)
            card.changed.connect(self.settings_changed.emit)
            self.pet_grid.addWidget(card, idx // 3, idx % 3)

    def load_skin_list(self):
        self.skin_combo.blockSignals(True)
        self.skin_combo.clear()
        skins = [d for d in os.listdir(SKINS_DIR) if os.path.isdir(os.path.join(SKINS_DIR, d))]
        self.skin_combo.addItems(sorted(skins))
        if self.current_editing_skin in skins:
            self.skin_combo.setCurrentText(self.current_editing_skin)
        self.skin_combo.blockSignals(False)

    def on_skin_selected(self, skin_name):
        if not skin_name: return
        self.current_editing_skin = skin_name
        self.load_current_skin_config()

    def _set_elided_filename(self, label: QLabel, full_name: str, max_width: int = 120):
        """긴 파일명을 가운데 말줄임표(...)로 처리하고 툴팁에 원본 전체 파일명 표시"""
        label.setToolTip(full_name)
        fm = QFontMetrics(label.font())
        elided = fm.elidedText(full_name, Qt.TextElideMode.ElideMiddle, max_width)
        label.setText(elided)

    def _update_motion_preview(self, label: QLabel, filename: str):
        """기본 모션 이미지의 미리보기 썸네일 갱신"""
        s_dir = os.path.join(SKINS_DIR, self.current_editing_skin)
        f_path = os.path.join(s_dir, filename)
        if filename and os.path.exists(f_path):
            pix = QPixmap(f_path)
            if not pix.isNull():
                label.setPixmap(pix.scaled(86, 86, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                return
        label.clear()
        label.setText("No Img")

    def load_current_skin_config(self):
        self.is_loading_skin = True
        conf = config_mgr.get_skin_config(self.current_editing_skin)
        
        # 1. 압축 슬라이더
        s_val = int(conf.get("squash_depth", 0.20) * 100)
        self.squash_slider.setValue(s_val)
        self.squash_lbl.setText(f"{s_val}%")
        
        # 2. 스킨별 바운스 애니메이션 체크박스
        self.skin_bounce_cb.blockSignals(True)
        self.skin_bounce_cb.setChecked(conf.get("enable_bounce", True))
        self.skin_bounce_cb.blockSignals(False)

        # 3. 기본 모션 이미지 파일명(말줄임 적용) 및 미리보기 갱신
        idle_file = conf.get("idle_image", "idle.png")
        tap_list = conf.get("tap_images", ["tap_left.png", "tap_right.png"])
        t1 = tap_list[0] if len(tap_list) > 0 else "tap_left.png"
        t2 = tap_list[1] if len(tap_list) > 1 else t1

        self._set_elided_filename(self.idle_name_lbl, idle_file, 120)
        self._update_motion_preview(self.idle_preview, idle_file)

        self._set_elided_filename(self.tap1_name_lbl, t1, 120)
        self._update_motion_preview(self.tap1_preview, t1)

        self._set_elided_filename(self.tap2_name_lbl, t2, 120)
        self._update_motion_preview(self.tap2_preview, t2)

        # 4. 키 매핑 테이블 로드
        self.map_table.setRowCount(0)
        for k, v in conf.get("key_mappings", {}).items():
            self.insert_map_row(k, v)

        self.is_loading_skin = False

    def on_skin_bounce_toggled(self, checked):
        if self.is_loading_skin: return
        conf = config_mgr.get_skin_config(self.current_editing_skin)
        conf["enable_bounce"] = checked
        config_mgr.save_skin_config(self.current_editing_skin, conf)
        self.settings_changed.emit()

    def on_squash_slider(self, val):
        self.squash_lbl.setText(f"{val}%")
        if self.is_loading_skin: return
        conf = config_mgr.get_skin_config(self.current_editing_skin)
        conf["squash_depth"] = round(val / 100.0, 2)
        config_mgr.save_skin_config(self.current_editing_skin, conf)
        self.settings_changed.emit()

    def browse_base_image(self, motion_type: str):
        """버튼을 통해서만 기본 모션 파일 설정 및 즉시 반영"""
        s_dir = os.path.join(SKINS_DIR, self.current_editing_skin)
        path, _ = QFileDialog.getOpenFileName(self, I18n.tr("image_filter"), s_dir, I18n.tr("image_filter"))
        if not path:
            return

        file_name = os.path.basename(path)
        conf = config_mgr.get_skin_config(self.current_editing_skin)

        if motion_type == "idle":
            conf["idle_image"] = file_name
            self._set_elided_filename(self.idle_name_lbl, file_name, 120)
            self._update_motion_preview(self.idle_preview, file_name)
        elif motion_type == "tap1":
            tap_list = conf.get("tap_images", ["tap_left.png", "tap_right.png"])
            t2 = tap_list[1] if len(tap_list) > 1 else tap_list[0]
            conf["tap_images"] = [file_name, t2]
            self._set_elided_filename(self.tap1_name_lbl, file_name, 120)
            self._update_motion_preview(self.tap1_preview, file_name)
        elif motion_type == "tap2":
            tap_list = conf.get("tap_images", ["tap_left.png", "tap_right.png"])
            t1 = tap_list[0] if len(tap_list) > 0 else "tap_left.png"
            conf["tap_images"] = [t1, file_name]
            self._set_elided_filename(self.tap2_name_lbl, file_name, 120)
            self._update_motion_preview(self.tap2_preview, file_name)

        config_mgr.save_skin_config(self.current_editing_skin, conf)
        self.settings_changed.emit()

    def insert_map_row(self, key_text, img_text):
        row = self.map_table.rowCount()
        self.map_table.insertRow(row)
        self.map_table.setRowHeight(row, 36)

        btn_key = KeyCaptureButton(key_text)
        btn_key.setFixedHeight(28)
        btn_key.setStyleSheet("""
            QPushButton {
                background-color: #F3F4F6;
                border: 1px solid #D1D5DB;
                border-radius: 6px;
                color: #111827;
                font-family: monospace;
                font-weight: 600;
                font-size: 11px;
                margin: 2px 4px;
            }
            QPushButton:hover { background-color: #E5E7EB; }
        """)
        btn_key.keyCaptured.connect(lambda k: self.on_key_captured(row, k))
        self.map_table.setCellWidget(row, 0, btn_key)

        le = QLineEdit(img_text)
        le.setFixedHeight(28)
        le.setStyleSheet("""
            QLineEdit {
                background-color: #FFFFFF;
                border: 1px solid #D1D5DB;
                border-radius: 6px;
                padding: 2px 8px;
                color: #111827;
                font-size: 12px;
                margin: 2px 4px;
            }
            QLineEdit:focus {
                border-color: #2563EB;
            }
        """)
        le.textChanged.connect(lambda _: self.save_map_from_table())
        self.map_table.setCellWidget(row, 1, le)

        btn_pick = QPushButton(I18n.tr("col_browse"))
        btn_pick.setFixedHeight(28)
        btn_pick.setStyleSheet("""
            QPushButton {
                background-color: #F3F4F6;
                border: 1px solid #D1D5DB;
                border-radius: 6px;
                color: #374151;
                font-weight: 500;
                font-size: 11px;
                margin: 2px 4px;
            }
            QPushButton:hover {
                background-color: #2563EB;
                border-color: #2563EB;
                color: #FFFFFF;
            }
        """)
        btn_pick.clicked.connect(lambda _, target=le: self.browse_image(target))
        self.map_table.setCellWidget(row, 2, btn_pick)

    def on_key_captured(self, row, key):
        self.save_map_from_table()

    def browse_image(self, target_le):
        s_dir = os.path.join(SKINS_DIR, self.current_editing_skin)
        path, _ = QFileDialog.getOpenFileName(self, I18n.tr("image_filter"), s_dir, I18n.tr("image_filter"))
        if path:
            target_le.setText(os.path.basename(path))

    def add_mapping_row(self):
        self.insert_map_row("space", "tap_left.png")
        self.save_map_from_table()

    def del_mapping_row(self):
        r = self.map_table.currentRow()
        if r >= 0:
            self.map_table.removeRow(r)
            self.save_map_from_table()

    def save_map_from_table(self):
        if self.is_loading_skin: return
        maps = {}
        for r in range(self.map_table.rowCount()):
            kw = self.map_table.cellWidget(r, 0)
            lw = self.map_table.cellWidget(r, 1)
            if kw and lw:
                k = kw.text().strip().lower()
                img = lw.text().strip()
                if k and img and not any(tag in k for tag in ["대기", "감지", "wait", "detecting"]):
                    maps[k] = img
        conf = config_mgr.get_skin_config(self.current_editing_skin)
        conf["key_mappings"] = maps
        config_mgr.save_skin_config(self.current_editing_skin, conf)
        self.settings_changed.emit()

    def create_new_skin(self):
        name, ok = QInputDialog.getText(self, I18n.tr("create_skin"), I18n.tr("create_skin_prompt"))
        if ok and name.strip():
            folder = os.path.join(SKINS_DIR, name.strip())
            if not os.path.exists(folder):
                os.makedirs(folder, exist_ok=True)
                config_mgr.save_skin_config(name.strip(), {
                    "name": name.strip(), "squash_depth": 0.20,
                    "enable_bounce": True,
                    "idle_image": "idle.png", "tap_images": ["tap_left.png", "tap_right.png"],
                    "key_mappings": {}
                })
                self.load_skin_list()
                self.skin_combo.setCurrentText(name.strip())
                self.refresh_pet_list()

    def open_skin_folder(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.join(SKINS_DIR, self.current_editing_skin)))

    def import_skin(self):
        path, _ = QFileDialog.getOpenFileName(self, I18n.tr("open_skin_zip"), "", I18n.tr("zip_filter"))
        if not path: return
        skin_name = os.path.splitext(os.path.basename(path))[0]
        try:
            with zipfile.ZipFile(path, 'r') as zf:
                zf.extractall(os.path.join(SKINS_DIR, skin_name))
            self.load_skin_list()
            self.refresh_pet_list()
            QMessageBox.information(self, I18n.tr("complete"), I18n.tr("applied"))
        except Exception as e:
            QMessageBox.critical(self, I18n.tr("error"), str(e))

    def export_skin(self):
        source = os.path.join(SKINS_DIR, self.current_editing_skin)
        save_path, _ = QFileDialog.getSaveFileName(self, I18n.tr("save_skin_zip"), f"{self.current_editing_skin}.zip", I18n.tr("zip_filter"))
        if not save_path: return
        try:
            shutil.make_archive(save_path.replace('.zip', ''), 'zip', source)
            QMessageBox.information(self, I18n.tr("complete"), I18n.tr("applied"))
        except Exception as e:
            QMessageBox.critical(self, I18n.tr("error"), str(e))

    def retranslate_ui(self):
        # 3개 서브 탭 번역
        self.sub_tabs.setTabText(0, I18n.tr("tab_general"))
        self.sub_tabs.setTabText(1, I18n.tr("subtab_pet_list"))
        self.sub_tabs.setTabText(2, I18n.tr("subtab_skin_editor"))
        
        # 일반 탭
        self.clamp_cb.setText(I18n.tr("clamp_to_screen"))
        self.click_thru_cb.setText(I18n.tr("click_through"))

        # 펫 목록 탭
        self.btn_add_pet.setText(I18n.tr("add_pet"))
        
        # 스킨 에디터 탭
        self.btn_new_skin.setText(I18n.tr("create_skin"))
        self.btn_open_folder.setText(I18n.tr("open_skin_folder"))
        self.skin_bounce_cb.setText(I18n.tr("enable_bounce_animation", "바운스 애니메이션"))
        self.lbl_squash_title.setText(I18n.tr("squash_depth"))

        self.idle_label.setText(I18n.tr("idle_image"))
        self.tap1_label.setText(I18n.tr("tap1_image"))
        self.tap2_label.setText(I18n.tr("tap2_image"))
        self.idle_browse_btn.setText(I18n.tr("browse"))
        self.tap1_browse_btn.setText(I18n.tr("browse"))
        self.tap2_browse_btn.setText(I18n.tr("browse"))

        self.lbl_key_map.setText(I18n.tr("key_mapping_section"))
        self.map_table.setHorizontalHeaderLabels([
            I18n.tr("col_input"), I18n.tr("col_image"), I18n.tr("col_browse")
        ])

        for r in range(self.map_table.rowCount()):
            btn_browse = self.map_table.cellWidget(r, 2)
            if btn_browse:
                btn_browse.setText(I18n.tr("col_browse"))

        self.btn_add_m.setText(I18n.tr("add_mapping"))
        self.btn_del_m.setText(I18n.tr("del_mapping"))
        self.btn_imp.setText(I18n.tr("import_skin"))
        self.btn_exp.setText(I18n.tr("export_skin"))

        for i in range(self.pet_grid.count()):
            w = self.pet_grid.itemAt(i).widget()
            if isinstance(w, PetCardWidget):
                w.retranslate_ui()

    def apply_theme(self):
        is_dark = config_mgr.config.get("settings", {}).get("dark_mode", False)
        
        for i in range(self.pet_grid.count()):
            w = self.pet_grid.itemAt(i).widget()
            if isinstance(w, PetCardWidget):
                w.update_card_style()

        t_border = "#27272A" if is_dark else "#E5E7EB"
        t_bg = "#18181B" if is_dark else "#FFFFFF"
        th_bg = "#202024" if is_dark else "#F9FAFB"
        th_color = "#A1A1AA" if is_dark else "#6B7280"
        title_color = "#FAFAFA" if is_dark else "#4B5563"

        self.lbl_key_map.setStyleSheet(f"font-weight: 600; font-size: 12px; margin-top: 4px; color: {title_color};")
        self.map_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {t_bg};
                border: 1px solid {t_border};
                border-radius: 8px;
                padding: 4px;
            }}
            QHeaderView::section {{
                background-color: {th_bg};
                color: {th_color};
                font-weight: 600;
                font-size: 11px;
                border: none;
                border-bottom: 1px solid {t_border};
                padding: 6px 4px;
            }}
        """)