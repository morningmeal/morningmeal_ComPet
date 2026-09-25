# ui/components.py
import os
import shutil
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QSlider,
    QComboBox, QGroupBox, QCheckBox, QFileDialog, QMessageBox, QFrame, QSpinBox,
    QAbstractSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent, QMouseEvent, QPixmap
from core.config_manager import config_mgr, SKINS_DIR, ASSETS_DIR
from core.sound_manager import sound_mgr, scan_sound_files
from core.i18n import I18n

QT_SHIFT_MAP = {
    '1': '!', '2': '@', '3': '#', '4': '$', '5': '%',
    '6': '^', '7': '&', '8': '*', '9': '(', '0': ')',
    '-': '_', '=': '+', '[': '{', ']': '}', '\\': '|',
    ';': ':', "'": '"', ',': '<', '.': '>', '/': '?', '`': '~'
}

QT_SPECIAL_KEYS = {
    Qt.Key.Key_Exclam: "!",
    Qt.Key.Key_At: "@",
    Qt.Key.Key_NumberSign: "#",
    Qt.Key.Key_Dollar: "$",
    Qt.Key.Key_Percent: "%",
    Qt.Key.Key_AsciiCircum: "^",
    Qt.Key.Key_Ampersand: "&",
    Qt.Key.Key_Asterisk: "*",
    Qt.Key.Key_ParenLeft: "(",
    Qt.Key.Key_ParenRight: ")",
    Qt.Key.Key_Underscore: "_",
    Qt.Key.Key_Plus: "+",
    Qt.Key.Key_BraceLeft: "{",
    Qt.Key.Key_BraceRight: "}",
    Qt.Key.Key_Bar: "|",
    Qt.Key.Key_Colon: ":",
    Qt.Key.Key_QuoteDbl: '"',
    Qt.Key.Key_Less: "<",
    Qt.Key.Key_Greater: ">",
    Qt.Key.Key_Question: "?",
    Qt.Key.Key_AsciiTilde: "~"
}

class CustomTitleBar(QWidget):
    theme_toggled = pyqtSignal()

    def __init__(self, parent_window, title="morningmeal_Compet"):
        super().__init__(parent_window)
        self.parent_window = parent_window
        self.setObjectName("titleBar")
        self.setFixedHeight(38)
        self.drag_start_pos = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 8, 0)
        layout.setSpacing(8)

        # 윈도우 타이틀
        self.title_label = QLabel(title)
        self.title_label.setObjectName("titleLabel")
        layout.addWidget(self.title_label)

        layout.addStretch()

        # 테마 전환 버튼 (Light / Dark)
        self.theme_btn = QPushButton("Mode")
        self.theme_btn.setObjectName("titleBtn")
        self.theme_btn.setFixedSize(50, 24)
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

class KeyCaptureButton(QPushButton):
    """단일 키, 조합 키, 특수 기호(!, ? 등), 마우스 입력을 일관되게 캡처하는 버튼"""
    keyCaptured = pyqtSignal(str)

    def __init__(self, text="", parent=None):
        waiting_text = I18n.tr("input_waiting")
        # 입력된 텍스트가 없거나 플레이스홀더면 빈 값으로 처리
        self.raw_key = text if (text and text != waiting_text) else ""
        super().__init__(self.raw_key or waiting_text, parent)
        self.capturing = False

        # 언어 변경 시그널 연결
        I18n.language_changed.connect(self.retranslate_ui)

    def retranslate_ui(self):
        """언어가 변경되었을 때 키가 미설정된 상태라면 안내 텍스트 갱신"""
        if not self.raw_key:
            if self.capturing:
                self.setText(I18n.tr("input_detecting"))
            else:
                self.setText(I18n.tr("input_waiting"))

    def mousePressEvent(self, event: QMouseEvent):
        if not self.capturing:
            self.capturing = True
            self.setText(I18n.tr("input_detecting"))
            self.setProperty("activeCapture", True)
            self.style().unpolish(self)
            self.style().polish(self)
            self.setFocus()
            event.accept()
            return

        btn = event.button()
        if btn == Qt.MouseButton.LeftButton:
            k_name = "mouse_left"
        elif btn == Qt.MouseButton.RightButton:
            k_name = "mouse_right"
        elif btn == Qt.MouseButton.MiddleButton:
            k_name = "mouse_middle"
        else:
            k_name = "mouse_click"

        self.raw_key = k_name
        self.setText(k_name)
        self.capturing = False
        self.setProperty("activeCapture", False)
        self.style().unpolish(self)
        self.style().polish(self)
        self.keyCaptured.emit(k_name)
        event.accept()

    def keyPressEvent(self, event: QKeyEvent):
        if not self.capturing:
            super().keyPressEvent(event)
            return

        key = event.key()
        modifiers = event.modifiers()

        # 제어 키 단독 입력 시 대기 유지
        if key in (Qt.Key.Key_Shift, Qt.Key.Key_Control, Qt.Key.Key_Alt, Qt.Key.Key_Meta):
            event.accept()
            return

        text = event.text().strip()
        is_shift = bool(modifiers & Qt.KeyboardModifier.ShiftModifier)
        is_ctrl = bool(modifiers & Qt.KeyboardModifier.ControlModifier)
        is_alt = bool(modifiers & Qt.KeyboardModifier.AltModifier)

        final_key = None

        # 1. Qt 고유 특수문자 Key Enum 확인
        if key in QT_SPECIAL_KEYS:
            final_key = QT_SPECIAL_KEYS[key]

        # 2. 실제로 타이핑되어 나온 문자가 기호인 경우
        elif text and text in "!@#$%^&*()_+{}|:\"<>?~`-=[]\\;',./":
            final_key = text

        # 3. Shift + 숫자/기호 키 처리 (Shift + 1 -> !)
        elif is_shift:
            char_guess = chr(key).lower() if (32 <= key <= 126) else text.lower()
            if char_guess in QT_SHIFT_MAP:
                final_key = QT_SHIFT_MAP[char_guess]

        # 4. 일반 키 또는 조합 키 처리
        if not final_key:
            key_names = {
                Qt.Key.Key_Space: "space",
                Qt.Key.Key_Return: "enter",
                Qt.Key.Key_Enter: "enter",
                Qt.Key.Key_Tab: "tab",
                Qt.Key.Key_Backspace: "backspace",
                Qt.Key.Key_Escape: "esc",
                Qt.Key.Key_Left: "left",
                Qt.Key.Key_Right: "right",
                Qt.Key.Key_Up: "up",
                Qt.Key.Key_Down: "down"
            }
            base = key_names.get(key, text.lower() if text else f"key_{key}")

            mod_parts = []
            if modifiers & Qt.KeyboardModifier.MetaModifier:
                mod_parts.append("cmd" if sys.platform == "darwin" else "win")
            if is_ctrl: mod_parts.append("ctrl")
            if is_alt: mod_parts.append("alt")
            if is_shift: mod_parts.append("shift")

            if mod_parts:
                final_key = "+".join(mod_parts) + "+" + base
            else:
                final_key = base

        self.raw_key = final_key
        self.setText(final_key)
        self.capturing = False
        self.setProperty("activeCapture", False)
        self.style().unpolish(self)
        self.style().polish(self)
        self.keyCaptured.emit(final_key)
        event.accept()


class PetCardWidget(QFrame):
    changed = pyqtSignal()

    def __init__(self, instance_data, remove_callback, parent=None):
        super().__init__(parent)
        self.instance_data = instance_data
        self.remove_callback = remove_callback
        
        self.setFixedWidth(150)
        self.setStyleSheet("""
            PetCardWidget {
                background-color: #FFFFFF;
                border: 1px solid #D0D7DE;
                border-radius: 8px;
            }
            PetCardWidget:hover {
                border-color: #93C5FD;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)
        top_bar.addStretch()
        
        # 0마리 허용: X버튼 누르면 언제든 삭제
        del_btn = QPushButton("❌")
        del_btn.setFixedSize(20, 20)
        del_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                font-size: 11px;
                color: #94A3B8;
                padding: 0;
            }
            QPushButton:hover {
                color: #EF4444;
            }
        """)
        del_btn.clicked.connect(lambda: self.remove_callback(self))
        top_bar.addWidget(del_btn)
        layout.addLayout(top_bar)

        self.preview_label = QLabel()
        self.preview_label.setFixedSize(70, 70)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("""
            background-color: #F8FAFC;
            border: 1px dashed #CBD5E1;
            border-radius: 6px;
        """)
        
        preview_container = QHBoxLayout()
        preview_container.setContentsMargins(0, 0, 0, 0)
        preview_container.addStretch()
        preview_container.addWidget(self.preview_label)
        preview_container.addStretch()
        layout.addLayout(preview_container)

        self.skin_combo = QComboBox()
        self.skin_combo.setStyleSheet("font-size: 11px; padding: 2px 4px;")
        self.refresh_skins()
        self.skin_combo.setCurrentText(self.instance_data.get("skin", "default"))
        self.skin_combo.currentTextChanged.connect(self.update_skin)
        layout.addWidget(self.skin_combo)

        size_layout = QHBoxLayout()
        size_layout.setContentsMargins(0, 0, 0, 0)
        size_layout.setSpacing(4)
        
        self.size_title_label = QLabel()
        self.size_title_label.setStyleSheet("font-size: 11px; color: #64748B;")
        
        current_percent = int(self.instance_data.get('scale', 1.0) * 100)
        self.scale_spinbox = QSpinBox()
        self.scale_spinbox.setRange(30, 300)
        self.scale_spinbox.setValue(current_percent)
        self.scale_spinbox.setSuffix("%")
        self.scale_spinbox.setFixedWidth(52)
        self.scale_spinbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scale_spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.scale_spinbox.setStyleSheet("""
            QSpinBox {
                font-size: 11px;
                font-weight: bold;
                color: #2563EB;
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                padding: 1px 0px;
                background: white;
            }
            QSpinBox:focus {
                border-color: #2563EB;
            }
        """)
        self.scale_spinbox.valueChanged.connect(self.on_spinbox_changed)
        
        size_layout.addWidget(self.size_title_label)
        size_layout.addStretch()
        size_layout.addWidget(self.scale_spinbox)
        layout.addLayout(size_layout)

        self.scale_slider = QSlider(Qt.Orientation.Horizontal)
        self.scale_slider.setRange(30, 300)
        self.scale_slider.setValue(current_percent)
        self.scale_slider.valueChanged.connect(self.on_slider_changed)
        self.scale_slider.setStyleSheet("""
            QSlider::groove:horizontal { height: 4px; background: #E2E8F0; border-radius: 2px; }
            QSlider::sub-page:horizontal { background: #2563EB; border-radius: 2px; }
            QSlider::handle:horizontal { width: 10px; height: 10px; margin-top: -3px; margin-bottom: -3px; border-radius: 5px; }
        """)
        layout.addWidget(self.scale_slider)

        self.update_preview_image()
        self.retranslate_ui()
        I18n.language_changed.connect(self.retranslate_ui)

    def refresh_skins(self):
        cur = self.skin_combo.currentText()
        self.skin_combo.blockSignals(True)
        self.skin_combo.clear()
        skins = [d for d in os.listdir(SKINS_DIR) if os.path.isdir(os.path.join(SKINS_DIR, d))]
        self.skin_combo.addItems(sorted(skins))
        if cur in skins:
            self.skin_combo.setCurrentText(cur)
        self.skin_combo.blockSignals(False)

    def update_preview_image(self):
        skin_name = self.instance_data.get("skin", "default")
        skin_conf = config_mgr.get_skin_config(skin_name)
        idle_file = skin_conf.get("idle_image", "idle.png")
        img_path = os.path.join(SKINS_DIR, skin_name, idle_file)
        
        if os.path.exists(img_path):
            pix = QPixmap(img_path)
            if not pix.isNull():
                scaled = pix.scaled(
                    60, 60,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.preview_label.setPixmap(scaled)
                return
        self.preview_label.clear()
        self.preview_label.setText("No Image")

    def retranslate_ui(self):
        self.size_title_label.setText(I18n.tr("size_label"))

    def update_skin(self, text):
        if not text:
            return
        self.instance_data["skin"] = text
        config_mgr.save_global_settings()
        self.update_preview_image()
        self.changed.emit()

    def sync_skin(self, skin_name):
        """외부(펫 우클릭 메뉴 등)에서 스킨이 변경되었을 때 콤보박스와 프리뷰 즉시 동기화"""
        self.skin_combo.blockSignals(True)
        self.skin_combo.setCurrentText(skin_name)
        self.instance_data["skin"] = skin_name
        self.skin_combo.blockSignals(False)
        self.update_preview_image()

    def on_slider_changed(self, val):
        self.scale_spinbox.blockSignals(True)
        self.scale_spinbox.setValue(val)
        self.scale_spinbox.blockSignals(False)

        self.instance_data["scale"] = val / 100.0
        config_mgr.save_global_settings()
        self.changed.emit()

    def on_spinbox_changed(self, val):
        self.scale_slider.blockSignals(True)
        self.scale_slider.setValue(val)
        self.scale_slider.blockSignals(False)

        self.instance_data["scale"] = val / 100.0
        config_mgr.save_global_settings()
        self.changed.emit()

    def sync_scale_from_external(self, scale_val):
        percent = int(round(scale_val * 100))
        self.scale_slider.blockSignals(True)
        self.scale_spinbox.blockSignals(True)
        
        self.scale_slider.setValue(percent)
        self.scale_spinbox.setValue(percent)
        self.instance_data["scale"] = scale_val
        
        self.scale_slider.blockSignals(False)
        self.scale_spinbox.blockSignals(False)


class SoundControlWidget(QGroupBox):
    def __init__(self, title_key, prefix, parent=None):
        super().__init__(parent)
        self.title_key = title_key
        self.prefix = prefix
        self.init_ui()
        self.retranslate_ui()
        I18n.language_changed.connect(self.retranslate_ui)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        self.enable_cb = QCheckBox()
        self.enable_cb.setChecked(config_mgr.settings.get(f"{self.prefix}_sound_enabled", True))
        self.enable_cb.toggled.connect(self.on_enable_changed)
        
        vol_layout = QHBoxLayout()
        self.vol_title = QLabel()
        self.vol_slider = QSlider(Qt.Orientation.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(config_mgr.settings.get(f"{self.prefix}_volume", 50))
        self.vol_slider.valueChanged.connect(self.on_volume_changed)
        self.vol_label = QLabel(f"{self.vol_slider.value()}%")
        vol_layout.addWidget(self.vol_title)
        vol_layout.addWidget(self.vol_slider)
        vol_layout.addWidget(self.vol_label)
        
        preset_layout = QHBoxLayout()
        self.preset_title = QLabel()
        self.sound_combo = QComboBox()
        self.sound_combo.currentIndexChanged.connect(self.on_sound_selected)
        
        preset_layout.addWidget(self.preset_title)
        preset_layout.addWidget(self.sound_combo, 1)

        layout.addWidget(self.enable_cb)
        layout.addLayout(vol_layout)
        layout.addLayout(preset_layout)

    def populate_sounds(self):
        self.sound_combo.blockSignals(True)
        self.sound_combo.clear()

        # assets/sounds 폴더 내 실제 wav 파일들을 실시간 스캔
        scanned = scan_sound_files()
        cur_saved = config_mgr.settings.get(f"{self.prefix}_sound_path", "")
        
        selected_index = 0
        idx = 0
        
        for display_name, full_path in scanned.items():
            self.sound_combo.addItem(f"{display_name}", full_path)
            # 저장된 경로와 일치하는 항목 확인
            if cur_saved and (cur_saved == full_path or os.path.basename(cur_saved) == os.path.basename(full_path)):
                selected_index = idx
            idx += 1

        # 맨 하단에 파일 직접 업로드/가져오기 항목 배치
        self.sound_combo.addItem(I18n.tr("upload_sound") + "...", "__import__")

        if self.sound_combo.count() > 1:
            self.sound_combo.setCurrentIndex(selected_index)
            # 만약 저장된 사운드 경로가 비어있거나 유효하지 않다면, 첫 번째 실제 사운드를 기본값으로 즉시 바인딩
            first_path = self.sound_combo.itemData(selected_index)
            if first_path and first_path != "__import__":
                config_mgr.settings[f"{self.prefix}_sound_path"] = first_path
                config_mgr.save_global_settings()
                sound_mgr.load_sounds()
        
        self.sound_combo.blockSignals(False)

    def retranslate_ui(self):
        self.setTitle(I18n.tr(self.title_key))
        self.enable_cb.setText(I18n.tr("sound_enable"))
        self.vol_title.setText(I18n.tr("volume"))
        self.preset_title.setText(I18n.tr("select_sound"))
        self.populate_sounds()

    def on_enable_changed(self, checked):
        config_mgr.settings[f"{self.prefix}_sound_enabled"] = checked
        config_mgr.save_global_settings()

    def on_volume_changed(self, val):
        self.vol_label.setText(f"{val}%")
        config_mgr.settings[f"{self.prefix}_volume"] = val
        config_mgr.save_global_settings()
        sound_mgr.update_volumes()

    def on_sound_selected(self, index):
        if index < 0:
            return

        data = self.sound_combo.itemData(index)

        # 사운드 파일 추가 버튼 클릭 시
        if data == "__import__":
            self.import_sound_file()
            return

        # 실제 선택된 사운드 파일 경로를 즉시 설정에 반영
        if data:
            config_mgr.settings[f"{self.prefix}_sound_path"] = data
            config_mgr.save_global_settings()
            sound_mgr.load_sounds()

            # ★ 사용자가 드롭다운에서 선택하는 즉시 소리가 나도록 1회 시연 재생
            if config_mgr.settings.get(f"{self.prefix}_sound_enabled", True):
                if self.prefix == "key":
                    sound_mgr.play_key()
                else:
                    sound_mgr.play_click()

    def import_sound_file(self):
        filter_str = "WAV Files (*.wav)"
        path, _ = QFileDialog.getOpenFileName(self, I18n.tr("select_wav"), "", filter_str)
        if not path:
            self.populate_sounds()
            return

        if not sound_mgr.is_valid_wav(path, 2.5):
            QMessageBox.warning(self, I18n.tr("error"), I18n.tr("upload_err"))
            self.populate_sounds()
            return

        os.makedirs(ASSETS_DIR, exist_ok=True)
        dest_filename = os.path.basename(path)
        dest_path = os.path.join(ASSETS_DIR, dest_filename)

        try:
            if os.path.abspath(path) != os.path.abspath(dest_path):
                shutil.copy2(path, dest_path)
            
            config_mgr.settings[f"{self.prefix}_sound_path"] = dest_path
            config_mgr.save_global_settings()
            sound_mgr.load_sounds()
            
            self.populate_sounds()

            # 업로드 직후 즉시 1회 재생
            if config_mgr.settings.get(f"{self.prefix}_sound_enabled", True):
                if self.prefix == "key":
                    sound_mgr.play_key()
                else:
                    sound_mgr.play_click()

            QMessageBox.information(self, I18n.tr("complete"), f"{dest_filename} {I18n.tr('applied')}")
        except Exception as e:
            QMessageBox.critical(self, I18n.tr("error"), f"Import failed:\n{e}")
            self.populate_sounds()