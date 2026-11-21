# ui/settings/tab_sound.py
import os
import shutil
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider,
    QComboBox, QCheckBox, QFileDialog, QMessageBox, QScrollArea, QPushButton
)
from PyQt6.QtCore import Qt
from core.config_manager import config_mgr, USER_SOUNDS_DIR
from core.sound_manager import sound_mgr, scan_sound_files
from core.i18n import I18n

class SoundGroupWidget(QWidget):
    def __init__(self, title_key, prefix, parent=None):
        super().__init__(parent)
        self.title_key = title_key
        self.prefix = prefix
        self.init_ui()
        self.retranslate_ui()
        I18n.language_changed.connect(self.retranslate_ui)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 16)
        layout.setSpacing(10)

        top_h = QHBoxLayout()
        self.title_lbl = QLabel()
        self.title_lbl.setStyleSheet("font-weight: 700; font-size: 14px; color: #2563EB;")
        top_h.addWidget(self.title_lbl)
        top_h.addStretch()

        snd_conf = config_mgr.config.get("sound", {})
        self.enable_cb = QCheckBox(I18n.tr("sound_enable"))
        self.enable_cb.setChecked(snd_conf.get(f"{self.prefix}_sound_enabled", True))
        self.enable_cb.toggled.connect(self.on_enable_toggled)
        top_h.addWidget(self.enable_cb)
        layout.addLayout(top_h)

        vol_box = QHBoxLayout()
        self.vol_lbl = QLabel(I18n.tr("volume"))
        self.vol_lbl.setFixedWidth(60)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(snd_conf.get(f"{self.prefix}_volume", 50))
        self.slider.valueChanged.connect(self.on_vol_changed)
        self.vol_val = QLabel(f"{self.slider.value()}%")
        self.vol_val.setFixedWidth(40)
        vol_box.addWidget(self.vol_lbl)
        vol_box.addWidget(self.slider, 1)
        vol_box.addWidget(self.vol_val)
        layout.addLayout(vol_box)

        snd_box = QHBoxLayout()
        self.pick_lbl = QLabel(I18n.tr("select_sound"))
        self.pick_lbl.setFixedWidth(80)
        self.combo = QComboBox()
        self.combo.setFixedHeight(28)
        self.combo.currentIndexChanged.connect(self.on_sound_selected)

        self.btn_upload = QPushButton(I18n.tr("upload_sound"))
        self.btn_upload.clicked.connect(self.upload_wav)

        snd_box.addWidget(self.pick_lbl)
        snd_box.addWidget(self.combo, 1)
        snd_box.addWidget(self.btn_upload)
        layout.addLayout(snd_box)

        self.line = QLabel()
        self.line.setFixedHeight(1)
        self.line.setStyleSheet("background-color: #2563EB;")
        layout.addWidget(self.line)

    def populate(self):
        self.combo.blockSignals(True)
        self.combo.clear()
        sounds = scan_sound_files()
        cur = config_mgr.config.get("sound", {}).get(f"{self.prefix}_sound_path", "")
        sel_idx = 0
        idx = 0
        for name, path in sounds.items():
            self.combo.addItem(name, path)
            if cur and (cur == path or os.path.basename(cur) == os.path.basename(path)):
                sel_idx = idx
            idx += 1
        self.combo.addItem(I18n.tr("upload_sound") + "...", "__upload__")
        self.combo.setCurrentIndex(sel_idx)
        self.combo.blockSignals(False)

    def on_enable_toggled(self, chk):
        config_mgr.config.setdefault("sound", {})[f"{self.prefix}_sound_enabled"] = chk
        config_mgr.save_config()

    def on_vol_changed(self, val):
        self.vol_val.setText(f"{val}%")
        config_mgr.config.setdefault("sound", {})[f"{self.prefix}_volume"] = val
        config_mgr.save_config()
        sound_mgr.update_volumes()

    def on_sound_selected(self, idx):
        if idx < 0: return
        data = self.combo.itemData(idx)
        if data == "__upload__":
            self.upload_wav()
            return
        if data:
            config_mgr.config.setdefault("sound", {})[f"{self.prefix}_sound_path"] = data
            config_mgr.save_config()
            sound_mgr.load_sounds()
            if self.prefix == "key": sound_mgr.play_key()
            else: sound_mgr.play_click()

    def upload_wav(self):
        path, _ = QFileDialog.getOpenFileName(self, I18n.tr("select_wav"), "", "WAV Files (*.wav)")
        if not path:
            self.populate()
            return
        if not sound_mgr.is_valid_wav(path, 2.5):
            QMessageBox.warning(self, I18n.tr("error"), I18n.tr("upload_err"))
            self.populate()
            return
        dest = os.path.join(USER_SOUNDS_DIR, os.path.basename(path))
        try:
            if os.path.abspath(path) != os.path.abspath(dest):
                shutil.copy2(path, dest)
            config_mgr.config.setdefault("sound", {})[f"{self.prefix}_sound_path"] = dest
            config_mgr.save_config()
            sound_mgr.load_sounds()
            self.populate()
            if self.prefix == "key": sound_mgr.play_key()
            else: sound_mgr.play_click()
        except Exception as e:
            QMessageBox.critical(self, I18n.tr("error"), str(e))
            self.populate()

    def retranslate_ui(self):
        self.title_lbl.setText(I18n.tr(self.title_key))
        self.enable_cb.setText(I18n.tr("sound_enable"))
        self.vol_lbl.setText(I18n.tr("volume"))
        self.pick_lbl.setText(I18n.tr("select_sound"))
        self.btn_upload.setText(I18n.tr("upload_sound"))
        self.populate()

class TabSoundSettings(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(16)

        self.key_grp = SoundGroupWidget("key_sound", "key")
        self.click_grp = SoundGroupWidget("click_sound", "click")

        layout.addWidget(self.key_grp)
        layout.addWidget(self.click_grp)
        layout.addStretch()
        scroll.setWidget(content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)