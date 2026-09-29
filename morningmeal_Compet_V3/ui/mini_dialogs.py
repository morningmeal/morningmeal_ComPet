# ui/mini_dialogs.py
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QComboBox, QLabel
from PyQt6.QtCore import Qt
from core.config_manager import config_mgr
from core.i18n import I18n

class TimerMiniDialog(QDialog):
    def __init__(self, timer_data, open_main_settings_callback, parent=None):
        super().__init__(parent)
        self.timer_data = timer_data
        self.parent_widget = parent
        self.open_main_settings_callback = open_main_settings_callback
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setFixedWidth(180)

        is_dark = config_mgr.config.get("settings", {}).get("dark_mode", False)
        bg = "#18181B" if is_dark else "#FFFFFF"
        border = "#3F3F46" if is_dark else "#E5E7EB"
        text = "#F4F4F5" if is_dark else "#111827"
        btn_bg = "#27272A" if is_dark else "#F3F4F6"
        
        self.setStyleSheet(f"""
            QDialog {{ background-color: {bg}; border: 1px solid {border}; border-radius: 8px; }}
            QLabel {{ color: {"#A1A1AA" if is_dark else "#4B5563"}; font-size: 11px; font-weight: 600; }}
            QPushButton {{ background-color: {btn_bg}; color: {text}; border: 1px solid {border}; border-radius: 6px; padding: 5px 10px; font-size: 12px; }}
            QPushButton:hover {{ background-color: {"#3F3F46" if is_dark else "#E5E7EB"}; }}
            QComboBox {{ background-color: {btn_bg}; color: {text}; border: 1px solid {border}; border-radius: 6px; padding: 4px 8px; font-size: 12px; }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        is_paused = self.timer_data.get("paused", False)
        self.pause_btn = QPushButton(I18n.tr("resume") if is_paused else I18n.tr("pause"))
        self.pause_btn.clicked.connect(self.toggle_pause)
        layout.addWidget(self.pause_btn)

        layout.addWidget(QLabel(I18n.tr("group_label")))
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