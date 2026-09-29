from PyQt6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QComboBox, QLabel
from PyQt6.QtCore import Qt
from core.config_manager import config_mgr
from core.i18n import I18n

class MiniSettingDialog(QDialog):
    def __init__(self, timer_data, open_main_settings_callback, parent=None):
        super().__init__(parent)
        self.timer_data = timer_data
        self.parent_widget = parent  # TimerWidget 참조
        self.open_main_settings_callback = open_main_settings_callback
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setFixedWidth(180)

        is_dark = config_mgr.config.get("settings", {}).get("dark_mode", False)
        if is_dark:
            self.setStyleSheet("""
                QDialog {
                    background-color: #18181B;
                    border: 1px solid #3F3F46;
                    border-radius: 8px;
                }
                QLabel {
                    color: #A1A1AA;
                    font-size: 11px;
                    font-weight: 600;
                }
                QPushButton {
                    background-color: #27272A;
                    color: #F4F4F5;
                    border: 1px solid #3F3F46;
                    border-radius: 6px;
                    padding: 5px 10px;
                    font-size: 12px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #3F3F46;
                }
                QComboBox {
                    background-color: #27272A;
                    color: #F4F4F5;
                    border: 1px solid #3F3F46;
                    border-radius: 6px;
                    padding: 4px 8px;
                    font-size: 12px;
                }
                QComboBox:focus {
                    border-color: #FAFAFA;
                }
                QComboBox::drop-down {
                    border: none;
                    width: 20px;
                }
                QComboBox QAbstractItemView {
                    background-color: #18181B;
                    border: 1px solid #3F3F46;
                    border-radius: 6px;
                    color: #F4F4F5;
                    selection-background-color: #3F3F46;
                    selection-color: #FFFFFF;
                    padding: 4px;
                    outline: none;
                }
            """)
        else:
            self.setStyleSheet("""
                QDialog {
                    background-color: #FFFFFF;
                    border: 1px solid #E5E7EB;
                    border-radius: 8px;
                }
                QLabel {
                    color: #4B5563;
                    font-size: 11px;
                    font-weight: 600;
                }
                QPushButton {
                    background-color: #F3F4F6;
                    color: #1F2937;
                    border: 1px solid #E5E7EB;
                    border-radius: 6px;
                    padding: 5px 10px;
                    font-size: 12px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #E5E7EB;
                }
                QComboBox {
                    background-color: #FFFFFF;
                    color: #111827;
                    border: 1px solid #D1D5DB;
                    border-radius: 6px;
                    padding: 4px 8px;
                    font-size: 12px;
                }
                QComboBox:focus {
                    border-color: #111827;
                }
                QComboBox::drop-down {
                    border: none;
                    width: 20px;
                }
                QComboBox QAbstractItemView {
                    background-color: #FFFFFF;
                    border: 1px solid #E5E7EB;
                    border-radius: 6px;
                    color: #111827;
                    selection-background-color: #F3F4F6;
                    selection-color: #111827;
                    padding: 4px;
                    outline: none;
                }
            """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        is_paused = self.timer_data.get("paused", False)
        self.pause_btn = QPushButton(I18n.tr("resume") if is_paused else I18n.tr("pause"))
        self.pause_btn.clicked.connect(self.toggle_pause)
        layout.addWidget(self.pause_btn)

        self.match_lbl = QLabel(I18n.tr("match_group"))
        layout.addWidget(self.match_lbl)
        
        self.group_combo = QComboBox()
        groups = list(config_mgr.config.get("groups", {}).keys())
        self.group_combo.addItems(groups)
        cur_group = self.timer_data.get("group", "")
        if cur_group in groups:
            self.group_combo.setCurrentText(cur_group)
        self.group_combo.currentTextChanged.connect(self.on_group_changed)
        layout.addWidget(self.group_combo)

        self.main_btn = QPushButton(I18n.tr("open_settings"))
        self.main_btn.clicked.connect(self.open_main)
        layout.addWidget(self.main_btn)

    def toggle_pause(self):
        new_state = not self.timer_data.get("paused", False)
        self.timer_data["paused"] = new_state
        config_mgr.save_config()
        self.pause_btn.setText(I18n.tr("resume") if new_state else I18n.tr("pause"))
        self.close()

    def on_group_changed(self, group_name):
        self.timer_data["group"] = group_name
        config_mgr.save_config()
        if self.parent_widget and hasattr(self.parent_widget, "update_metadata"):
            self.parent_widget.update_metadata()

    def open_main(self):
        self.close()
        if self.open_main_settings_callback:
            self.open_main_settings_callback()