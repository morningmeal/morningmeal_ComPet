# ui/timer_widget.py
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QPoint, pyqtSignal
from PyQt6.QtGui import QMouseEvent, QPainter, QColor, QPen
from core.config_manager import config_mgr
from core.snap_manager import SnapManager
from core.i18n import I18n
from ui.mini_dialogs import TimerMiniDialog
from ui.components import format_time

class TimerWidget(QWidget):
    moved = pyqtSignal(str, int, int)  # (timer_id, x, y)
    settings_requested = pyqtSignal()

    def __init__(self, timer_data, get_all_timers_callback, get_bound_pet_callback, open_main_settings_callback):
        super().__init__()
        self.timer_data = timer_data
        self.get_all_timers_callback = get_all_timers_callback
        self.get_bound_pet_callback = get_bound_pet_callback
        self.open_main_settings_callback = open_main_settings_callback
        self.drag_position = QPoint()

        # 가로 폭 140px 고정
        self.setFixedWidth(140)

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.update_window_flags()

        self.init_ui()
        self.move(int(self.timer_data.get("x", 200)), int(self.timer_data.get("y", 300)))
        I18n.language_changed.connect(self.retranslate_ui)

    def update_window_flags(self):
        """플로팅 타이머 위젯의 창 속성 설정"""
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        if config_mgr.config.get("settings", {}).get("tray_mode", False):
            flags |= Qt.WindowType.Tool
        self.setWindowFlags(flags)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 1. 타이머 이름 라벨 (짙은 회색 고정)
        self.label_name = QLabel(self.timer_data.get("name", I18n.tr("default_timer_name")))
        self.label_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_name.setStyleSheet("background: transparent; font-size: 11px; font-weight: 600; color: #4B5563;")

        # 2. 시간 라벨
        self.label_time = QLabel(format_time(self.timer_data.get("elapsed_seconds", 0)))
        self.label_time.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_time.setStyleSheet("background: transparent; font-size: 16px; font-weight: bold; font-family: monospace;")

        layout.addWidget(self.label_name)
        layout.addWidget(self.label_time)

        self.apply_theme()

    def paintEvent(self, event):
        """네이티브 렌더링으로 딜레이 없이 카드 배경 드로잉"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        is_dark = config_mgr.config.get("settings", {}).get("dark_mode", False)

        if is_dark:
            bg_color = QColor(24, 24, 27, 240)
            border_color = QColor(63, 63, 70, 255)
        else:
            bg_color = QColor(255, 255, 255, 245)
            border_color = QColor(209, 213, 219, 255)

        painter.setBrush(bg_color)
        painter.setPen(QPen(border_color, 1))
        painter.drawRoundedRect(1, 1, self.width() - 2, self.height() - 2, 8, 8)

    def apply_theme(self):
        """테마 전환 시 시간 텍스트 색상 및 배경만 0ms로 즉각 갱신 (이름은 짙은 회색 유지)"""
        is_dark = config_mgr.config.get("settings", {}).get("dark_mode", False)
        
        # 다크 모드에서는 가독성을 고려한 다크 차콜/미디엄 그레이, 라이트 모드에서는 짙은 그레이
        name_color = "#9CA3AF" if is_dark else "#4B5563"
        time_color = "#FFFFFF" if is_dark else "#000000"

        self.label_name.setStyleSheet(f"background: transparent; font-size: 11px; font-weight: 600; color: {name_color};")
        self.label_time.setStyleSheet(f"background: transparent; font-size: 16px; font-weight: bold; font-family: monospace; color: {time_color};")
        self.update()

    def update_time(self, seconds):
        self.timer_data["elapsed_seconds"] = seconds
        self.label_time.setText(format_time(seconds))

    def update_metadata(self):
        self.label_name.setText(self.timer_data.get("name", I18n.tr("default_timer_name")))
        self.apply_theme()

    def retranslate_ui(self):
        if not self.timer_data.get("name"):
            self.label_name.setText(I18n.tr("default_timer_name"))

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        elif event.button() == Qt.MouseButton.RightButton:
            dialog = TimerMiniDialog(self.timer_data, self.open_main_settings_callback, self)
            dialog.move(event.globalPosition().toPoint())
            dialog.exec()
            self.update_metadata()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton:
            raw_pos = event.globalPosition().toPoint() - self.drag_position
            all_timers = self.get_all_timers_callback()
            snapped_pos = SnapManager.calculate_snap(self, all_timers, raw_pos)
            self.move(snapped_pos)

            bound_pet = self.get_bound_pet_callback(self.timer_data.get("id"))
            if bound_pet:
                bound_pet.snap_to_timer(self)

            self.moved.emit(self.timer_data.get("id"), snapped_pos.x(), snapped_pos.y())
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.timer_data["x"] = self.x()
        self.timer_data["y"] = self.y()
        config_mgr.save_config()

        bound_pet = self.get_bound_pet_callback(self.timer_data.get("id"))
        if bound_pet:
            bound_pet.save_position()
        event.accept()