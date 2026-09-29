# ui/settings/tab_sound.py
import os
import shutil
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSlider,
    QComboBox, QCheckBox, QFileDialog, QMessageBox, QGroupBox
)
from PyQt6.QtCore import Qt
from core.config_manager import config_mgr, USER_SOUNDS_DIR
from core.sound_manager import sound_mgr, scan_sound_files
from core.i18n import I18n

class SoundGroupWidget(QGroupBox):
    def __init__(self, title_key, prefix, parent=None):
        super().__init__(parent)
        self.title_key = title_key
        self.prefix = prefix
        self.init_ui()
        self.retranslate_ui()
        I18n.language_changed.connect(self.retranslate_ui)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 18, 14, 14)
        layout.setSpacing(12)

        snd_conf = config_mgr.config.get("sound", {})
        
        # 사운드 활성화 체크박스
        self.enable_cb = QCheckBox(I18n.tr("sound_enable"))
        self.enable_cb.setChecked(snd_conf.get(f"{self.prefix}_sound_enabled", True))
        self.enable_cb.toggled.connect(self.on_enable_toggled)

        # 볼륨 조절 슬라이더
        vol_box = QHBoxLayout()
        self.vol_lbl = QLabel(I18n.tr("volume"))
        self.vol_lbl.setFixedWidth(50)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(snd_conf.get(f"{self.prefix}_volume", 50))
        self.slider.valueChanged.connect(self.on_vol_changed)
        self.vol_val = QLabel(f"{self.slider.value()}%")
        self.vol_val.setFixedWidth(40)
        self.vol_val.setStyleSheet("font-weight: bold; color: #2563EB;")
        
        vol_box.addWidget(self.vol_lbl)
        vol_box.addWidget(self.slider, 1)
        vol_box.addWidget(self.vol_val)

        # 사운드 선택 드롭다운
        snd_box = QHBoxLayout()
        self.pick_lbl = QLabel(I18n.tr("select_sound"))
        self.pick_lbl.setFixedWidth(70)
        self.combo = QComboBox()
        self.combo.setFixedHeight(28)
        self.combo.currentIndexChanged.connect(self.on_sound_selected)
        
        snd_box.addWidget(self.pick_lbl)
        snd_box.addWidget(self.combo, 1)

        layout.addWidget(self.enable_cb)
        layout.addLayout(vol_box)
        layout.addLayout(snd_box)

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
            # 선택 즉시 시연 1회 재생
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
        self.setTitle(I18n.tr(self.title_key))
        self.enable_cb.setText(I18n.tr("sound_enable"))
        self.vol_lbl.setText(I18n.tr("volume"))
        self.pick_lbl.setText(I18n.tr("select_sound"))
        self.populate()


class TabSoundSettings(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(14)

        # 서브 탭 없이 그룹 박스로 단일 페이지 구성
        self.key_grp = SoundGroupWidget("key_sound", "key")
        self.click_grp = SoundGroupWidget("click_sound", "click")

        layout.addWidget(self.key_grp)
        layout.addWidget(self.click_grp)
        layout.addStretch()