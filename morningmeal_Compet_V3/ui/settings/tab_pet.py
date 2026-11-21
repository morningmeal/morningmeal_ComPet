# ui/settings/tab_pet.py
import os
import uuid
import zipfile
import shutil
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QPushButton, QLabel, QLineEdit, QComboBox, QSpinBox,
    QSlider, QFileDialog, QMessageBox, QInputDialog, QTabWidget, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QUrl
from PyQt6.QtGui import QDesktopServices, QPixmap, QFontMetrics
from core.config_manager import config_mgr, SKINS_DIR
from core.i18n import I18n
from ui.components import KeyCaptureButton, AlertDialog

class PetRowWidget(QWidget):
    changed = pyqtSignal()

    def __init__(self, pet_data, remove_callback, parent=None):
        super().__init__(parent)
        self.pet_data = pet_data
        self.remove_callback = remove_callback

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 6, 0, 6)
        layout.setSpacing(12)

        self.preview_label = QLabel()
        self.preview_label.setFixedSize(36, 36)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.preview_label)

        self.skin_combo = QComboBox()
        self.skin_combo.setFixedWidth(130)
        self.refresh_skins()
        self.skin_combo.setCurrentText(self.pet_data.get("skin", "default"))
        self.skin_combo.currentTextChanged.connect(self.on_skin_changed)
        layout.addWidget(self.skin_combo)

        cur_pct = int(round(self.pet_data.get("scale", 1.0) * 100))
        self.scale_spin = QSpinBox()
        self.scale_spin.setFixedWidth(70)
        self.scale_spin.setRange(10, 150)
        self.scale_spin.setSingleStep(5)
        self.scale_spin.setValue(cur_pct)
        self.scale_spin.setSuffix("%")
        self.scale_spin.valueChanged.connect(self.on_scale_changed)
        layout.addWidget(self.scale_spin)

        self.bound_combo = QComboBox()
        self.bound_combo.setFixedWidth(140)
        self.refresh_timers()
        self.bound_combo.currentIndexChanged.connect(self.on_bound_timer_changed)
        layout.addWidget(self.bound_combo)

        layout.addStretch()

        self.btn_del = QPushButton(I18n.tr("remove_pet"))
        self.btn_del.setProperty("actionType", "danger")
        self.btn_del.setFixedWidth(45)
        self.btn_del.clicked.connect(lambda: self.remove_callback(self.pet_data))
        layout.addWidget(self.btn_del)

        self.update_preview()
        I18n.language_changed.connect(self.retranslate_ui)

    def sync_from_data(self):
        self.refresh_skins()
        self.skin_combo.blockSignals(True)
        self.skin_combo.setCurrentText(self.pet_data.get("skin", "default"))
        self.skin_combo.blockSignals(False)

        self.scale_spin.blockSignals(True)
        self.scale_spin.setValue(int(round(self.pet_data.get("scale", 1.0) * 100)))
        self.scale_spin.blockSignals(False)

        self.refresh_timers()
        self.update_preview()

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
        self.pet_data["scale"] = round(val / 100.0, 2)
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
                self.preview_label.setPixmap(pix.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                return
        self.preview_label.clear()
        self.preview_label.setText("Img")

    def retranslate_ui(self):
        self.refresh_timers()
        self.btn_del.setText(I18n.tr("remove_pet"))


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
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.sub_tabs = QTabWidget()
        self.sub_tabs.setObjectName("subTabWidget")

        # 1. 일반 설정 서브 탭
        self.sub_page_general = QWidget()
        l_g = QVBoxLayout(self.sub_page_general)
        l_g.setContentsMargins(14, 14, 14, 14)
        l_g.setSpacing(14)

        self.clamp_cb = QCheckBox(I18n.tr("clamp_to_screen"))
        self.clamp_cb.setChecked(config_mgr.config.get("settings", {}).get("clamp_to_screen", True))
        self.clamp_cb.toggled.connect(lambda c: self.save_opt("clamp_to_screen", c))

        self.click_thru_cb = QCheckBox(I18n.tr("click_through"))
        self.click_thru_cb.setChecked(config_mgr.config.get("settings", {}).get("click_through", False))
        self.click_thru_cb.toggled.connect(lambda c: self.save_opt("click_through", c))

        self.tray_mode_cb = QCheckBox(I18n.tr("tray_mode"))
        self.tray_mode_cb.setChecked(config_mgr.config.get("settings", {}).get("tray_mode", False))
        self.tray_mode_cb.toggled.connect(lambda c: self.save_opt("tray_mode", c))

        l_g.addWidget(self.clamp_cb)
        l_g.addWidget(self.click_thru_cb)
        l_g.addWidget(self.tray_mode_cb)
        l_g.addStretch()

        # 2. 활성 펫 관리 서브 탭 (스크롤 지원)
        self.sub_page_pets = QWidget()
        l_p = QVBoxLayout(self.sub_page_pets)
        l_p.setContentsMargins(12, 12, 12, 12)
        l_p.setSpacing(10)

        top_p = QHBoxLayout()
        top_p.addStretch()
        self.btn_add_pet = QPushButton(f"+ {I18n.tr('add_pet')}")
        self.btn_add_pet.setProperty("actionType", "primary")
        self.btn_add_pet.clicked.connect(self.add_pet)
        top_p.addWidget(self.btn_add_pet)
        l_p.addLayout(top_p)

        scroll_p = QScrollArea()
        scroll_p.setWidgetResizable(True)
        p_content = QWidget()
        self.pet_list_layout = QVBoxLayout(p_content)
        self.pet_list_layout.setContentsMargins(0, 0, 0, 0)
        self.pet_list_layout.setSpacing(4)
        self.pet_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_p.setWidget(p_content)
        l_p.addWidget(scroll_p)

        # 3. 스킨 에디터 서브 탭 (스크롤 지원)
        self.sub_page_skin = QWidget()
        l_s_outer = QVBoxLayout(self.sub_page_skin)
        l_s_outer.setContentsMargins(0, 0, 0, 0)

        scroll_s = QScrollArea()
        scroll_s.setWidgetResizable(True)
        skin_content = QWidget()
        layout_skin = QVBoxLayout(skin_content)
        layout_skin.setContentsMargins(14, 14, 14, 14)
        layout_skin.setSpacing(16)

        bar_s = QHBoxLayout()
        self.skin_combo = QComboBox()
        self.skin_combo.currentTextChanged.connect(self.on_skin_selected)
        self.btn_new_skin = QPushButton(f"+ {I18n.tr('create_skin')}")
        self.btn_new_skin.setProperty("actionType", "primary")
        self.btn_new_skin.clicked.connect(self.create_new_skin)
        self.btn_open_folder = QPushButton(I18n.tr("open_skin_folder"))
        self.btn_open_folder.clicked.connect(self.open_skin_folder)

        bar_s.addWidget(self.skin_combo, 2)
        bar_s.addWidget(self.btn_new_skin, 1)
        bar_s.addWidget(self.btn_open_folder, 1)
        layout_skin.addLayout(bar_s)

        self.skin_bounce_cb = QCheckBox(I18n.tr("enable_bounce_animation"))
        self.skin_bounce_cb.toggled.connect(self.on_skin_bounce_toggled)
        layout_skin.addWidget(self.skin_bounce_cb)

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

        # 3열 모션 미리보기
        motions_grid = QHBoxLayout()
        motions_grid.setSpacing(20)

        def make_motion_col(title_key, preview_lbl, name_lbl, browse_btn_ref, motion_type):
            w = QWidget()
            col = QVBoxLayout(w)
            col.setContentsMargins(0, 0, 0, 0)
            col.setSpacing(6)
            lbl = QLabel(I18n.tr(title_key))
            lbl.setStyleSheet("font-weight: 600; font-size: 11px;")
            preview_lbl.setFixedSize(70, 70)
            preview_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            preview_lbl.setStyleSheet("background-color: rgba(128,128,128,0.06); border: 1px dashed #2563EB; border-radius: 6px;")
            name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name_lbl.setStyleSheet("font-size: 11px; color: #6B7280;")
            browse_btn_ref.setText(I18n.tr("browse"))
            browse_btn_ref.clicked.connect(lambda: self.browse_base_image(motion_type))
            col.addWidget(lbl, alignment=Qt.AlignmentFlag.AlignHCenter)
            col.addWidget(preview_lbl, alignment=Qt.AlignmentFlag.AlignHCenter)
            col.addWidget(name_lbl, alignment=Qt.AlignmentFlag.AlignHCenter)
            col.addWidget(browse_btn_ref, alignment=Qt.AlignmentFlag.AlignHCenter)
            return w

        self.idle_preview = QLabel("No Img")
        self.idle_name_lbl = QLabel("idle.png")
        self.idle_browse_btn = QPushButton()
        col1 = make_motion_col("idle_image", self.idle_preview, self.idle_name_lbl, self.idle_browse_btn, "idle")

        self.tap1_preview = QLabel("No Img")
        self.tap1_name_lbl = QLabel("tap_left.png")
        self.tap1_browse_btn = QPushButton()
        col2 = make_motion_col("tap1_image", self.tap1_preview, self.tap1_name_lbl, self.tap1_browse_btn, "tap1")

        self.tap2_preview = QLabel("No Img")
        self.tap2_name_lbl = QLabel("tap_right.png")
        self.tap2_browse_btn = QPushButton()
        col3 = make_motion_col("tap2_image", self.tap2_preview, self.tap2_name_lbl, self.tap2_browse_btn, "tap2")

        motions_grid.addWidget(col1)
        motions_grid.addWidget(col2)
        motions_grid.addWidget(col3)
        layout_skin.addLayout(motions_grid)

        # 키 매핑 섹션 (플랫 행 리스트)
        self.lbl_key_map = QLabel(I18n.tr("key_mapping_section"))
        self.lbl_key_map.setStyleSheet("font-weight: 700; font-size: 13px; color: #2563EB; margin-top: 8px;")
        layout_skin.addWidget(self.lbl_key_map)

        self.map_list_layout = QVBoxLayout()
        self.map_list_layout.setSpacing(4)
        layout_skin.addLayout(self.map_list_layout)

        btn_map_box = QHBoxLayout()
        self.btn_add_m = QPushButton(f"+ {I18n.tr('add_mapping')}")
        self.btn_add_m.setProperty("actionType", "primary")
        self.btn_add_m.clicked.connect(self.add_mapping_row)
        btn_map_box.addWidget(self.btn_add_m)
        btn_map_box.addStretch()

        self.btn_imp = QPushButton(I18n.tr("import_skin"))
        self.btn_imp.clicked.connect(self.import_skin)
        self.btn_exp = QPushButton(I18n.tr("export_skin"))
        self.btn_exp.clicked.connect(self.export_skin)
        btn_map_box.addWidget(self.btn_imp)
        btn_map_box.addWidget(self.btn_exp)
        layout_skin.addLayout(btn_map_box)

        scroll_s.setWidget(skin_content)
        l_s_outer.addWidget(scroll_s)

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

    def sync_pet_cards_state(self):
        pets = config_mgr.config.get("pets", [])
        if self.pet_list_layout.count() - 1 != len(pets):
            self.refresh_pet_list()
            return
        for i in range(self.pet_list_layout.count() - 1):
            w = self.pet_list_layout.itemAt(i).widget()
            if isinstance(w, PetRowWidget): w.sync_from_data()

    def refresh_pet_list(self):
        while self.pet_list_layout.count():
            item = self.pet_list_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        for p in config_mgr.config.get("pets", []):
            row = PetRowWidget(p, self.remove_pet)
            row.changed.connect(self.settings_changed.emit)
            self.pet_list_layout.addWidget(row)
        self.pet_list_layout.addStretch()

    def load_skin_list(self):
        self.skin_combo.blockSignals(True)
        self.skin_combo.clear()
        skins = [d for d in os.listdir(SKINS_DIR) if os.path.isdir(os.path.join(SKINS_DIR, d))]
        self.skin_combo.addItems(sorted(skins))
        if self.current_editing_skin in skins:
            self.skin_combo.setCurrentText(self.current_editing_skin)
        elif skins:
            self.current_editing_skin = skins[0]
            self.skin_combo.setCurrentText(skins[0])
        self.skin_combo.blockSignals(False)

    def on_skin_selected(self, skin_name):
        if not skin_name: return
        self.current_editing_skin = skin_name
        self.load_current_skin_config()

    def _set_elided_filename(self, label: QLabel, full_name: str, max_width: int = 110):
        label.setToolTip(full_name)
        fm = QFontMetrics(label.font())
        label.setText(fm.elidedText(full_name, Qt.TextElideMode.ElideMiddle, max_width))

    def _update_motion_preview(self, label: QLabel, filename: str):
        f_path = os.path.join(SKINS_DIR, self.current_editing_skin, filename)
        if filename and os.path.exists(f_path):
            pix = QPixmap(f_path)
            if not pix.isNull():
                label.setPixmap(pix.scaled(60, 60, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                return
        label.clear()
        label.setText("No Img")

    def _copy_image_into_skin_dir(self, src_path: str) -> str:
        s_dir = os.path.abspath(os.path.join(SKINS_DIR, self.current_editing_skin))
        os.makedirs(s_dir, exist_ok=True)
        src_abs = os.path.abspath(src_path)
        file_name = os.path.basename(src_abs)
        dest_abs = os.path.join(s_dir, file_name)
        if src_abs != dest_abs:
            try: shutil.copy2(src_abs, dest_abs)
            except Exception: pass
        return file_name

    def load_current_skin_config(self):
        self.is_loading_skin = True
        conf = config_mgr.get_skin_config(self.current_editing_skin)
        s_val = int(round(conf.get("squash_depth", 0.20) * 100))
        self.squash_slider.setValue(s_val)
        self.squash_lbl.setText(f"{s_val}%")
        
        self.skin_bounce_cb.blockSignals(True)
        self.skin_bounce_cb.setChecked(conf.get("enable_bounce", True))
        self.skin_bounce_cb.blockSignals(False)

        idle_file = conf.get("idle_image", "idle.png")
        tap_list = conf.get("tap_images", ["tap_left.png", "tap_right.png"])
        t1 = tap_list[0] if len(tap_list) > 0 else "tap_left.png"
        t2 = tap_list[1] if len(tap_list) > 1 else t1

        self._set_elided_filename(self.idle_name_lbl, idle_file)
        self._update_motion_preview(self.idle_preview, idle_file)
        self._set_elided_filename(self.tap1_name_lbl, t1)
        self._update_motion_preview(self.tap1_preview, t1)
        self._set_elided_filename(self.tap2_name_lbl, t2)
        self._update_motion_preview(self.tap2_preview, t2)

        while self.map_list_layout.count():
            item = self.map_list_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

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
        s_dir = os.path.join(SKINS_DIR, self.current_editing_skin)
        path, _ = QFileDialog.getOpenFileName(self, I18n.tr("image_filter"), s_dir, I18n.tr("image_filter"))
        if not path: return
        file_name = self._copy_image_into_skin_dir(path)
        conf = config_mgr.get_skin_config(self.current_editing_skin)

        if motion_type == "idle":
            conf["idle_image"] = file_name
            self._set_elided_filename(self.idle_name_lbl, file_name)
            self._update_motion_preview(self.idle_preview, file_name)
        elif motion_type == "tap1":
            t_list = conf.get("tap_images", ["tap_left.png", "tap_right.png"])
            t2 = t_list[1] if len(t_list) > 1 else t_list[0]
            conf["tap_images"] = [file_name, t2]
            self._set_elided_filename(self.tap1_name_lbl, file_name)
            self._update_motion_preview(self.tap1_preview, file_name)
        elif motion_type == "tap2":
            t_list = conf.get("tap_images", ["tap_left.png", "tap_right.png"])
            t1 = t_list[0] if len(t_list) > 0 else "tap_left.png"
            conf["tap_images"] = [t1, file_name]
            self._set_elided_filename(self.tap2_name_lbl, file_name)
            self._update_motion_preview(self.tap2_preview, file_name)

        config_mgr.save_skin_config(self.current_editing_skin, conf)
        self.sync_pet_cards_state()
        self.settings_changed.emit()

    def insert_map_row(self, key_text, img_text):
        row_w = QWidget()
        h = QHBoxLayout(row_w)
        h.setContentsMargins(0, 2, 0, 2)
        h.setSpacing(10)

        btn_key = KeyCaptureButton(key_text)
        btn_key.setFixedWidth(120)
        btn_key.keyCaptured.connect(lambda _: self.save_map_from_table())
        h.addWidget(btn_key)

        le = QLineEdit(img_text)
        le.setFixedHeight(26)
        le.textChanged.connect(lambda _: self.save_map_from_table())
        h.addWidget(le, 1)

        btn_browse = QPushButton(I18n.tr("col_browse"))
        btn_browse.setFixedWidth(65)
        btn_browse.clicked.connect(lambda _, target=le: self.browse_image(target))
        h.addWidget(btn_browse)

        btn_del = QPushButton(I18n.tr("del_mapping"))
        btn_del.setProperty("actionType", "danger")
        btn_del.setFixedWidth(45)
        btn_del.clicked.connect(lambda: (row_w.deleteLater(), self.save_map_from_table()))
        h.addWidget(btn_del)

        self.map_list_layout.addWidget(row_w)

    def browse_image(self, target_le):
        s_dir = os.path.join(SKINS_DIR, self.current_editing_skin)
        path, _ = QFileDialog.getOpenFileName(self, I18n.tr("image_filter"), s_dir, I18n.tr("image_filter"))
        if path:
            file_name = self._copy_image_into_skin_dir(path)
            target_le.setText(file_name)

    def add_mapping_row(self):
        self.insert_map_row("space", "tap_left.png")
        self.save_map_from_table()

    def save_map_from_table(self):
        if self.is_loading_skin: return
        maps = {}
        for i in range(self.map_list_layout.count()):
            w = self.map_list_layout.itemAt(i).widget()
            if w:
                btn_k = w.findChild(KeyCaptureButton)
                le_img = w.findChild(QLineEdit)
                if btn_k and le_img:
                    k = btn_k.raw_key.strip().lower()
                    img = le_img.text().strip()
                    if k and img: maps[k] = img
        conf = config_mgr.get_skin_config(self.current_editing_skin)
        conf["key_mappings"] = maps
        config_mgr.save_skin_config(self.current_editing_skin, conf)
        self.settings_changed.emit()

    def create_new_skin(self):
        name, ok = QInputDialog.getText(self, I18n.tr("create_skin"), I18n.tr("create_skin_prompt"))
        if ok and name.strip():
            clean_name = name.strip()
            folder = os.path.join(SKINS_DIR, clean_name)
            if os.path.exists(folder):
                AlertDialog(I18n.tr("error"), I18n.tr("skin_exists_warn"), self).exec()
                return
            os.makedirs(folder, exist_ok=True)
            config_mgr.save_skin_config(clean_name, {
                "name": clean_name, "squash_depth": 0.20, "enable_bounce": True,
                "idle_image": "idle.png", "tap_images": ["tap_left.png", "tap_right.png"], "key_mappings": {}
            })
            self.current_editing_skin = clean_name
            self.load_skin_list()
            self.load_current_skin_config()
            self.sync_pet_cards_state()

    def open_skin_folder(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.join(SKINS_DIR, self.current_editing_skin)))

    def import_skin(self):
        path, _ = QFileDialog.getOpenFileName(self, I18n.tr("open_skin_zip"), "", I18n.tr("zip_filter"))
        if not path: return
        skin_name = os.path.splitext(os.path.basename(path))[0].strip()
        target_dir = os.path.join(SKINS_DIR, skin_name)
        try:
            os.makedirs(target_dir, exist_ok=True)
            with zipfile.ZipFile(path, 'r') as zf:
                for member in zf.infolist():
                    if member.filename.startswith("__MACOSX") or member.filename.endswith(".DS_Store"): continue
                    zf.extract(member, target_dir)
            entries = [e for e in os.listdir(target_dir) if e not in ("__MACOSX", ".DS_Store")]
            if len(entries) == 1:
                nested = os.path.join(target_dir, entries[0])
                if os.path.isdir(nested):
                    for item in os.listdir(nested):
                        shutil.move(os.path.join(nested, item), os.path.join(target_dir, item))
                    os.rmdir(nested)
            self.current_editing_skin = skin_name
            self.load_skin_list()
            self.load_current_skin_config()
            self.sync_pet_cards_state()
            AlertDialog(I18n.tr("complete"), I18n.tr("applied"), self).exec()
        except Exception as e:
            QMessageBox.critical(self, I18n.tr("error"), str(e))

    def export_skin(self):
        source = os.path.join(SKINS_DIR, self.current_editing_skin)
        save_path, _ = QFileDialog.getSaveFileName(self, I18n.tr("save_skin_zip"), f"{self.current_editing_skin}.zip", I18n.tr("zip_filter"))
        if not save_path: return
        try:
            base_out = save_path[:-4] if save_path.lower().endswith('.zip') else save_path
            shutil.make_archive(base_out, 'zip', source)
            AlertDialog(I18n.tr("complete"), I18n.tr("applied"), self).exec()
        except Exception as e:
            QMessageBox.critical(self, I18n.tr("error"), str(e))

    def retranslate_ui(self):
        self.sub_tabs.setTabText(0, I18n.tr("tab_general"))
        self.sub_tabs.setTabText(1, I18n.tr("subtab_pet_list"))
        self.sub_tabs.setTabText(2, I18n.tr("subtab_skin_editor"))
        self.clamp_cb.setText(I18n.tr("clamp_to_screen"))
        self.click_thru_cb.setText(I18n.tr("click_through"))
        self.tray_mode_cb.setText(I18n.tr("tray_mode"))
        self.btn_add_pet.setText(f"+ {I18n.tr('add_pet')}")
        self.btn_new_skin.setText(f"+ {I18n.tr('create_skin')}")
        self.btn_open_folder.setText(I18n.tr("open_skin_folder"))
        self.skin_bounce_cb.setText(I18n.tr("enable_bounce_animation"))
        self.lbl_squash_title.setText(I18n.tr("squash_depth"))
        self.idle_browse_btn.setText(I18n.tr("browse"))
        self.tap1_browse_btn.setText(I18n.tr("browse"))
        self.tap2_browse_btn.setText(I18n.tr("browse"))
        self.lbl_key_map.setText(I18n.tr("key_mapping_section"))
        self.btn_add_m.setText(f"+ {I18n.tr('add_mapping')}")
        self.btn_imp.setText(I18n.tr("import_skin"))
        self.btn_exp.setText(I18n.tr("export_skin"))
        for i in range(self.pet_list_layout.count()):
            w = self.pet_list_layout.itemAt(i).widget()
            if isinstance(w, PetRowWidget): w.retranslate_ui()

    def apply_theme(self):
        pass