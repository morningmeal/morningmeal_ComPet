from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QMouseEvent
from core.config_manager import config_mgr
from core.snap_manager import SnapManager
from core.i18n import I18n
from ui.mini_setting_dialog import MiniSettingDialog
from ui.components import format_time

class TimerWidget(QWidget):
    def __init__(self, timer_data, get_all_widgets_callback, open_main_settings_callback):
        super().__init__()
        self.timer_data = timer_data
        self.get_all_widgets_callback = get_all_widgets_callback
        self.open_main_settings_callback = open_main_settings_callback
        self.drag_position = QPoint()

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        # 크기를 약간 키워 여유롭고 뚜렷한 영역 확보
        self.setFixedSize(160, 62)

        self.init_ui()
        self.apply_theme()
        self.move(int(self.timer_data.get("x", 100)), int(self.timer_data.get("y", 100)))

    def init_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self.container = QWidget()
        self.container.setObjectName("timerCard")

        # 내부 요소들을 정가운데에 수직/수평 정렬
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 상단 작업 이름 (가운데 정렬)
        self.label_name = QLabel(self.timer_data.get("name", I18n.tr("default_timer_name")))
        self.label_name.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 중앙 타이머 숫자 (크기 확대 & 가운데 정렬)
        self.label_time = QLabel(format_time(self.timer_data.get("elapsed_seconds", 0)))
        self.label_time.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.label_name)
        layout.addWidget(self.label_time)
        outer.addWidget(self.container)

    def apply_theme(self):
        is_dark = config_mgr.config.get("settings", {}).get("dark_mode", False)
        if is_dark:
            self.container.setStyleSheet("""
                QWidget#timerCard {
                    background-color: rgba(24, 24, 27, 0.94);
                    border: 1px solid rgba(63, 63, 70, 0.95);
                    border-radius: 10px;
                }
            """)
            self.label_name.setStyleSheet("color: #A1A1AA; font-size: 11px; font-weight: 600; letter-spacing: 0.5px;")
            self.label_time.setStyleSheet("color: #FAFAFA; font-size: 20px; font-weight: bold; font-family: monospace; letter-spacing: 1px;")
        else:
            self.container.setStyleSheet("""
                QWidget#timerCard {
                    background-color: rgba(255, 255, 255, 0.96);
                    border: 1px solid rgba(209, 213, 219, 0.95);
                    border-radius: 10px;
                }
            """)
            self.label_name.setStyleSheet("color: #4B5563; font-size: 11px; font-weight: 600; letter-spacing: 0.5px;")
            self.label_time.setStyleSheet("color: #111827; font-size: 20px; font-weight: bold; font-family: monospace; letter-spacing: 1px;")

    def update_time(self, seconds):
        self.timer_data["elapsed_seconds"] = seconds
        self.label_time.setText(format_time(seconds))
        self.label_time.repaint()

    def update_metadata(self):
        self.label_name.setText(self.timer_data.get("name", I18n.tr("default_timer_name")))
        self.label_time.setText(format_time(self.timer_data.get("elapsed_seconds", 0)))

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        elif event.button() == Qt.MouseButton.RightButton:
            dialog = MiniSettingDialog(self.timer_data, self.open_main_settings_callback, self)
            dialog.move(event.globalPosition().toPoint())
            dialog.exec()
            self.update_metadata()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton:
            raw_pos = event.globalPosition().toPoint() - self.drag_position
            all_widgets = self.get_all_widgets_callback()
            snapped_pos = SnapManager.calculate_snap(self, all_widgets, raw_pos)
            self.move(snapped_pos)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.timer_data["x"] = self.x()
        self.timer_data["y"] = self.y()
        config_mgr.save_config()
        event.accept()