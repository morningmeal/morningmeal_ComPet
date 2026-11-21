# ui/timer_widget.py
import sys
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication
from PyQt6.QtCore import Qt, QPoint, QRectF, pyqtSignal
from PyQt6.QtGui import QMouseEvent, QPainter, QColor
from core.config_manager import config_mgr
from core.snap_manager import SnapManager
from core.i18n import I18n
from core.activity_engine import activity_engine
from ui.components import format_time, StyledMenu, ConfirmDialog


class TimerWidget(QWidget):
    SHADOW_MARGIN = 8
    moved = pyqtSignal(str, int, int)
    settings_requested = pyqtSignal()

    def __init__(
        self,
        timer_data,
        get_all_timers_callback,
        get_bound_pet_callback,
        open_main_settings_callback,
        remove_callback=None,
        quit_callback=None,
    ):
        super().__init__()
        self.timer_data = timer_data
        self.get_all_timers_callback = get_all_timers_callback
        self.get_bound_pet_callback = get_bound_pet_callback
        self.open_main_settings_callback = open_main_settings_callback
        self.remove_callback = remove_callback
        self.quit_callback = quit_callback
        self.drag_position = QPoint()
        self._applied_flags = None

        self.setFixedWidth(140 + self.SHADOW_MARGIN * 2)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        if sys.platform == 'darwin':
            self.setAttribute(Qt.WidgetAttribute.WA_MacAlwaysShowToolWindow, True)

        self.update_window_flags()
        self.init_ui()
        self.move(int(self.timer_data.get("x", 200)), int(self.timer_data.get("y", 300)))
        I18n.language_changed.connect(self.retranslate_ui)

    def update_window_flags(self):
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        if config_mgr.config.get("settings", {}).get("tray_mode", False):
            if sys.platform == 'win32':
                flags |= Qt.WindowType.Tool
            else:
                flags |= Qt.WindowType.NoDropShadowWindowHint

        if self._applied_flags != flags:
            was_visible = self.isVisible()
            self._applied_flags = flags
            self.setWindowFlags(flags)
            if was_visible:
                self.show()

    def init_ui(self):
        m = self.SHADOW_MARGIN
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14 + m, 10 + m, 14 + m, 10 + m)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.label_name = QLabel(self.timer_data.get("name", I18n.tr("default_timer_name")))
        self.label_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_name.setStyleSheet("background: transparent; font-size: 11px; font-weight: 600; color: #6B7280;")

        self.label_time = QLabel(format_time(self.timer_data.get("elapsed_seconds", 0)))
        self.label_time.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_time.setStyleSheet("background: transparent; font-size: 16px; font-weight: bold; font-family: monospace;")

        layout.addWidget(self.label_name)
        layout.addWidget(self.label_time)
        self.apply_theme()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)

        is_dark = config_mgr.config.get("settings", {}).get("dark_mode", False)
        m = self.SHADOW_MARGIN
        card_rect = QRectF(m, m, self.width() - m * 2, self.height() - m * 2)

        # 옅은 다중 레이어 드롭 섀도우 (아래쪽으로 살짝 치우친 자연스러운 그림자)
        for i in range(m, 0, -1):
            alpha = int((1.0 - (i / (m + 1))) ** 2 * (26 if is_dark else 16))
            painter.setBrush(QColor(0, 0, 0, alpha))
            shadow_rect = card_rect.adjusted(-i * 0.6, -i * 0.4 + 1.5, i * 0.6, i * 0.8 + 1.5)
            painter.drawRoundedRect(shadow_rect, 6 + i * 0.4, 6 + i * 0.4)

        # 본체 카드
        bg_color = QColor(24, 24, 27, 248) if is_dark else QColor(255, 255, 255, 248)
        painter.setBrush(bg_color)
        painter.drawRoundedRect(card_rect, 6, 6)

    def apply_theme(self):
        is_dark = config_mgr.config.get("settings", {}).get("dark_mode", False)
        is_paused = self.timer_data.get("paused", False)
        name_color = "#A1A1AA" if is_dark else "#6B7280"
        time_color = "#71717A" if is_paused else ("#FFFFFF" if is_dark else "#000000")

        self.label_name.setStyleSheet(f"background: transparent; font-size: 11px; font-weight: 600; color: {name_color};")
        self.label_time.setStyleSheet(f"background: transparent; font-size: 16px; font-weight: bold; font-family: monospace; color: {time_color};")
        self.update()

    def update_time(self, seconds):
        self.timer_data["elapsed_seconds"] = seconds
        self.label_time.setText(format_time(seconds))

    def update_metadata(self):
        self.label_name.setText(self.timer_data.get("name", I18n.tr("default_timer_name")))
        self.label_time.setText(format_time(self.timer_data.get("elapsed_seconds", 0)))
        self.apply_theme()

    def retranslate_ui(self):
        if not self.timer_data.get("name"):
            self.label_name.setText(I18n.tr("default_timer_name"))

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        elif event.button() == Qt.MouseButton.RightButton:
            self.show_context_menu(event.globalPosition().toPoint())
            event.accept()

    def show_context_menu(self, global_pos):
        menu = StyledMenu(self)

        is_paused = self.timer_data.get("paused", False)
        pause_act = menu.addAction(I18n.tr("resume") if is_paused else I18n.tr("pause"))
        pause_act.triggered.connect(self.toggle_pause)

        reset_act = menu.addAction(I18n.tr("reset"))
        reset_act.triggered.connect(self.reset_time)

        delete_act = menu.addAction(I18n.tr("delete"))
        delete_act.triggered.connect(self.delete_timer)

        menu.addSeparator()

        group_title = I18n.tr("group_label").rstrip(":").strip()
        group_menu = menu.addStyledMenu(group_title)
        groups = list(config_mgr.config.get("groups", {}).keys())
        cur_group = self.timer_data.get("group", "")

        if groups:
            for g_name in groups:
                act = group_menu.addAction(g_name)
                act.setCheckable(True)
                if g_name == cur_group:
                    act.setChecked(True)
                act.triggered.connect(lambda checked, name=g_name: self.change_group(name))
        else:
            empty_act = group_menu.addAction(I18n.tr("no_group_available"))
            empty_act.setEnabled(False)

        menu.addSeparator()

        settings_act = menu.addAction(I18n.tr("open_settings"))
        settings_act.triggered.connect(self.open_main_settings)

        menu.addSeparator()

        exit_act = menu.addAction(I18n.tr("tray_exit"))
        exit_act.triggered.connect(self.quit_program)

        menu.exec(global_pos)

    def toggle_pause(self):
        self.timer_data["paused"] = not self.timer_data.get("paused", False)
        config_mgr.save_config()
        self.update_metadata()

    def reset_time(self):
        dlg = ConfirmDialog(
            I18n.tr("reset_confirm_title"),
            I18n.tr("reset_confirm_msg"),
            is_danger=False,
            parent=None,
        )
        if dlg.exec() == ConfirmDialog.DialogCode.Accepted:
            t_id = self.timer_data.get("id")
            self.timer_data["elapsed_seconds"] = 0
            config_mgr.save_config()
            self.update_metadata()
            activity_engine.tick.emit({t_id: 0})

    def delete_timer(self):
        timer_name = self.timer_data.get("name", I18n.tr("default_timer_name"))
        dlg = ConfirmDialog(
            I18n.tr("del_timer_title"),
            I18n.tr("del_timer_msg").format(name=timer_name),
            is_danger=True,
            parent=None,
        )
        if dlg.exec() == ConfirmDialog.DialogCode.Accepted:
            if self.remove_callback:
                self.remove_callback(self.timer_data.get("id"))

    def change_group(self, group_name: str):
        self.timer_data["group"] = group_name
        config_mgr.save_config()
        self.update_metadata()

    def open_main_settings(self):
        if self.open_main_settings_callback:
            self.open_main_settings_callback()

    def quit_program(self):
        if self.quit_callback:
            self.quit_callback()
        else:
            QApplication.quit()

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